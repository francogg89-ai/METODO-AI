"""Local host: durable operation receipts, CUA mailbox and Claude stdin bytes."""
from __future__ import annotations
import argparse
from contextlib import contextmanager
from dataclasses import asdict
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import time
import uuid
from .core import Capture, Prepared, Session, parse_locator


def read(path):
    return json.loads(Path(path).read_bytes().decode('utf-8'))


def save(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    data = json.dumps(value, ensure_ascii=False, indent=2).encode('utf-8')
    tmp = path.with_name(path.name + '.tmp')
    with tmp.open('wb') as f:
        f.write(data); f.flush(); os.fsync(f.fileno())
    os.replace(tmp, path)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def snapshot(session):
    obj = asdict(session)
    obj['known'] = {r: sorted(v) for r, v in session.known.items()}
    return obj


def restore(obj):
    obj = dict(obj)
    obj['known'] = {r: set(v) for r, v in obj['known'].items()}
    if obj['original'] is not None:
        obj['original'] = Capture(**obj['original'])
    return Session(**obj)


@contextmanager
def lock(root):
    # Kernel lock is released on process death; never remove a live lock by age.
    f = (root / 'host.lock').open('a+b')
    f.seek(0); f.write(b'0'); f.flush(); f.seek(0)
    try:
        if os.name == 'nt':
            import msvcrt
            msvcrt.locking(f.fileno(), msvcrt.LK_NBLCK, 1)
        else:
            import fcntl
            fcntl.flock(f.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        yield
    finally:
        f.close()


class Uncertain(RuntimeError):
    pass


class Mailbox:
    def __init__(self, root, timeout=600):
        self.root, self.timeout = Path(root), timeout

    def call(self, op, **payload):
        key = uuid.uuid4().hex
        box = self.root / 'mailbox'
        request = {'id': key, 'op': op, **payload}
        save(box / 'requests' / (key + '.json'), request)
        # One outstanding operation per locked host. Service must persist its claim before effects.
        save(box / 'command.json', request)
        end = time.monotonic() + self.timeout
        reply = box / 'responses' / (key + '.json')
        while time.monotonic() < end:
            if reply.exists():
                obj = read(reply)
                if obj.get('id') != key:
                    raise RuntimeError('Mailbox identity mismatch')
                if obj.get('error'):
                    raise RuntimeError(obj['error'])
                return obj['result']
            time.sleep(.15)
        raise Uncertain('Mailbox timeout; operation remains recorded: ' + key)


class Tape:
    """Replay only saved results. An unfinished mutation is never invoked twice."""
    def __init__(self, path):
        self.path = path
        self.entries = read(path) if path.exists() else []
        self.index = 0

    def call(self, name, args, fn, mutating=False):
        index = self.index; self.index += 1
        signature = digest(json.dumps([name, args], sort_keys=True, ensure_ascii=False).encode())
        if index < len(self.entries):
            e = self.entries[index]
            if e['signature'] != signature:
                raise Uncertain('Operation replay diverged; refusing execution')
            if e['state'] == 'done':
                return e['result']
            if e['state'] == 'error':
                raise RuntimeError(e['error'])
            if mutating:
                raise Uncertain('Unfinished operation: ' + name + '; do not resend')
        else:
            self.entries.append({'signature': signature, 'operation': name, 'state': 'issued'})
            save(self.path, self.entries)
        try:
            value = fn()
        except Exception as exc:
            # Mutations stay uncertain after an exception, even if a host dies now.
            if not mutating:
                self.entries[index].update(state='error', error=str(exc))
                save(self.path, self.entries)
            raise
        self.entries[index].update(state='done', result=value)
        save(self.path, self.entries)
        return value


class LocalAdapter:
    def __init__(self, root, config, tape=None):
        self.root, self.config, self.tape = Path(root), config, tape
        self.mail = Mailbox(root, config.get('browser_timeout_seconds', 600))
        self.registry_path = self.root / 'instances.json'
        self.instances = read(self.registry_path) if self.registry_path.exists() else {}

    def persist(self):
        save(self.registry_path, self.instances)

    def op(self, name, args, fn, mutating=False):
        return self.tape.call(name, args, fn, mutating) if self.tape else fn()

    def open_fresh(self, role):
        def create():
            token = uuid.uuid4().hex
            handle = ('chatgpt:' if role == 'AUDITOR' else 'claude:') + token
            if role == 'AUDITOR':
                value = self.mail.call('fresh', token=token)
                if not value.get('fresh') or value.get('conversation_id') is not None:
                    raise RuntimeError('Fresh browser conversation not demonstrated')
                record = {'role': role, 'token': token, 'tab_id': value['tab_id'], 'conversation_id': None}
            else:
                record = {'role': role, 'session_id': str(uuid.uuid4()), 'started': False}
            self.instances[handle] = record
            self.persist()
            return handle
        return self.op('fresh', [role], create, True)

    def is_current(self, role, handle):
        def check():
            record = self.instances.get(handle)
            if not record or record['role'] != role:
                return False
            if role == 'AUDITOR':
                return self.mail.call('current', instance=record).get('matches') is True
            # CLI resume must also return exactly this ID. No --continue/latest fallback.
            return record.get('started') is True and bool(record.get('last_result'))
        return self.op('current', [role, handle], check)

    def prepare(self, handle, text):
        def write():
            data = text.encode('utf-8', 'strict')
            path = self.root / 'payloads' / (uuid.uuid4().hex + '.txt')
            path.parent.mkdir(exist_ok=True)
            path.write_bytes(data)
            r = self.instances[handle]
            r['prepared'] = str(path); r['prepared_hash'] = digest(data)
            self.persist()
            if r['role'] == 'AUDITOR':
                value = self.mail.call('prepare', instance=r, text=path.read_bytes().decode('utf-8'))
                return {'text': text, 'anomaly': value.get('anomaly', True)}
            return {'text': path.read_bytes().decode('utf-8'), 'anomaly': False}
        return Prepared(**self.op('prepare', [handle, text], write))

    def readback(self, handle):
        def get():
            r = self.instances[handle]
            if r['role'] == 'AUDITOR':
                return self.mail.call('readback', instance=r)['text']
            return Path(r['prepared']).read_bytes().decode('utf-8')
        return self.op('readback', [handle], get)

    def claude_argv(self, record):
        c = self.config['claude']
        executable = c.get('executable') or shutil.which('claude')
        if not executable or str(executable).lower().endswith(('.cmd', '.bat')):
            raise RuntimeError('Configure executable as native claude.exe, not a shell wrapper')
        command = [executable, '-p', '--output-format', 'json', '--permission-mode', c.get('permission_mode', 'default')]
        command += ['--resume' if record.get('started') else '--session-id', record['session_id']]
        if c.get('settings_file'):
            command += ['--settings', str(Path(c['settings_file']).resolve())]
        if c.get('model'):
            command += ['--model', c['model']]
        if 'tools' in c:
            command += ['--tools', ','.join(c['tools'])]
        if c.get('allowed_tools'):
            command += ['--allowedTools', ','.join(c['allowed_tools'])]
        return command

    def send(self, handle):
        def execute():
            r = self.instances[handle]
            data = Path(r['prepared']).read_bytes()
            if digest(data) != r['prepared_hash']:
                return 'NOT_SENT'
            if r['role'] == 'AUDITOR':
                value = self.mail.call('send', instance=r, expected_text=data.decode('utf-8'))
                r['receipt'] = value
                if value.get('receipt') == 'DELIVERED':
                    r['conversation_id'] = value['conversation_id']
                    r['response_id'] = value['assistant_message_id']
                self.persist()
                return value.get('receipt', 'UNKNOWN')
            # Resolve all local validation BEFORE creating the child process.
            command = self.claude_argv(r)
            directory = Path(self.config['claude']['cwd'])
            if not directory.is_dir():
                return 'NOT_SENT'
            call_id = uuid.uuid4().hex
            out = self.root / 'cli' / call_id
            out.mkdir(parents=True)
            save(out / 'invocation.json', {'argv': command, 'cwd': str(directory), 'stdin_bytes': len(data), 'stdin_sha256': digest(data)})
            try:
                with (out / 'stdout.json').open('wb') as stdout, (out / 'stderr.bin').open('wb') as stderr:
                    process = subprocess.Popen(command, cwd=directory, stdin=subprocess.PIPE, stdout=stdout, stderr=stderr)
                    save(out / 'process.json', {'pid': process.pid, 'session_id': r['session_id']})
                    process.communicate(data)
                    code = process.returncode
            except OSError:
                # No automatic replay even if an OS error happened after process creation.
                return 'UNKNOWN'
            raw = (out / 'stdout.json').read_bytes()
            r['last_result'] = str(out / 'stdout.json')
            try:
                obj = json.loads(raw.decode('utf-8'))
                valid = (code == 0 and obj.get('is_error') is False and
                         obj.get('session_id') == r['session_id'] and isinstance(obj.get('result'), str)
                         and isinstance(obj.get('uuid'), str))
                r['response_id'] = obj.get('uuid')
                r['started'] = bool(valid)
                # Denials remain visible in the CLI evidence; no silent permission escalation.
                r['permission_denials'] = obj.get('permission_denials', [])
            except Exception:
                valid = False
            r['receipt'] = {'receipt': 'DELIVERED' if valid else 'UNKNOWN', 'stdout': str(out / 'stdout.json')}
            self.persist()
            return r['receipt']['receipt']
        return self.op('send', [handle], execute, True)

    def capture(self, handle, response_id):
        r = self.instances[handle]
        key = uuid.uuid4().hex
        try:
            if r['role'] == 'AUDITOR':
                value = self.mail.call('capture', instance=r, response_id=response_id)
                if value.get('response_id') != response_id or value.get('conversation_id') != r['conversation_id']:
                    raise RuntimeError('Capture identity mismatch')
                text, complete = value['text'], value.get('complete') is True
            else:
                value = read(r['last_result'])
                text = value.get('result', '')
                complete = (value.get('uuid') == response_id and value.get('session_id') == r['session_id']
                            and value.get('is_error') is False and value.get('stop_reason') == 'end_turn')
            path = self.root / 'captures' / (key + '.txt')
            path.parent.mkdir(exist_ok=True)
            path.write_bytes(text.encode('utf-8'))
            save(path.with_suffix('.json'), {'handle': handle, 'response_id': response_id, 'complete': complete,
                                            'sha256': digest(path.read_bytes()), 'metadata': value})
            return Capture(text, response_id, complete)
        except Exception as exc:
            save(self.root / 'captures' / (key + '-error.json'), {'handle': handle, 'response_id': response_id, 'error': str(exc)})
            return Capture('', response_id, False)

    def repair(self, *args):
        return None


def transact(root, config, session, action, payload=None):
    active = root / 'active.json'
    if active.exists():
        tx = read(active)
        session = restore(tx['before'])
        action, payload = tx['action'], tx['payload']
    else:
        tx = {'id': uuid.uuid4().hex, 'action': action, 'payload': payload, 'before': snapshot(session)}
        save(active, tx)
    adapter = LocalAdapter(root, config, Tape(root / 'transactions' / (tx['id'] + '.json')))
    if action == 'start':
        result = session.start(adapter, payload)
    elif action == 'accept':
        result = session.accept(adapter, Capture(**payload), source_actor=session.expected_actor)
    elif action == 'continue':
        result = session.continue_(adapter, payload)
    elif action == 'resolve':
        result = session.resolve_human(adapter, payload)
    else:
        raise RuntimeError('Unknown transaction')
    save(root / 'state.json', snapshot(session))
    save(root / 'results' / (tx['id'] + '.json'), result)
    active.unlink()
    return session, result


def validate_config(config):
    parse_locator(config['locator'])
    if parse_locator(config['locator'])[1]['WORK_ID'] != config['work_id']:
        raise ValueError('Locator work differs')
    Session(config['work_id'], config['repositories'])
    if config['claude'].get('permission_mode', 'default') not in {'default', 'acceptEdits', 'dontAsk', 'plan'}:
        raise ValueError('Unsupported permission mode; no bypass')
    return config


def main():
    p = argparse.ArgumentParser(description='METODO-AI local transport; no automatic replay of uncertain sends')
    p.add_argument('command', choices=['init', 'check', 'step', 'recover', 'stop', 'continue', 'resolve', 'status'])
    p.add_argument('--run', required=True, type=Path)
    p.add_argument('--config', type=Path)
    p.add_argument('--text-file', type=Path)
    args = p.parse_args(); root = args.run.resolve()
    root.mkdir(parents=True, exist_ok=True)
    if args.command == 'stop':
        save(root / 'stop-request.json', {'requested': True})
        print('stop_requested; applied at the constructor-to-auditor boundary'); return
    with lock(root):
        if args.command == 'check':
            config = validate_config(read(args.config))
            a = LocalAdapter(root, config)
            cmd = a.claude_argv({'session_id': str(uuid.uuid4())})
            version = subprocess.run([cmd[0], '--version'], capture_output=True, check=True, timeout=20)
            cwd = Path(config['claude']['cwd'])
            if not cwd.is_dir(): raise RuntimeError('Constructor directory missing')
            remote = subprocess.run(['git', '-C', str(cwd), 'remote', 'get-url', 'origin'], capture_output=True, check=True, timeout=20).stdout.decode().strip()
            repo = config['repositories']['CONSTRUCTOR']
            if remote not in {'https://github.com/'+repo, 'https://github.com/'+repo+'.git', 'git@github.com:'+repo+'.git'}:
                raise RuntimeError('Constructor remote differs')
            print(json.dumps({'status':'local_paths_checked', 'claude_version':version.stdout.decode().strip(), 'browser_verified':False, 'permissions_verified':False})); return
        if args.command == 'init':
            if (root / 'config.json').exists():
                raise RuntimeError('Run already initialized; use step/recover')
            config = validate_config(read(args.config))
            if config.get('method_sha'):
                method = Path(__file__).resolve().parents[1]
                head = subprocess.run(['git', '-C', str(method), 'rev-parse', 'HEAD'], capture_output=True, check=True).stdout.decode().strip()
                dirty = subprocess.run(['git', '-C', str(method), 'status', '--porcelain'], capture_output=True, check=True).stdout
                if head != config['method_sha'] or dirty:
                    raise RuntimeError('Method checkout must be clean and pinned to configured method_sha')
            save(root / 'config.json', config)
            save(root / 'state.json', snapshot(Session(config['work_id'], config['repositories'])))
            print('initialized; no messages sent'); return
        config = validate_config(read(root / 'config.json'))
        session = restore(read(root / 'state.json'))
        if (root / 'stop-request.json').exists():
            session.request_stop()
            save(root / 'state.json', snapshot(session))
        result = {'status': session.mode, 'last_turn': session.last_turn}
        text = args.text_file.read_bytes().decode('utf-8') if args.text_file else None
        if args.command == 'status':
            print(json.dumps({'status':session.mode, 'last_turn':session.last_turn, 'expected_actor':session.expected_actor, 'handles':session.handles, 'stop_requested':session.stop_requested, 'unfinished_transaction':(root / 'active.json').exists(), 'failure':session.report}, ensure_ascii=False)); return
        if (root / 'active.json').exists():
            if args.command != 'recover':
                raise RuntimeError('Unfinished transaction; use recover, never init')
            session, result = transact(root, config, session, '')
        elif args.command == 'stop':
            result = session.request_stop(); save(root / 'state.json', snapshot(session))
        elif args.command in {'continue', 'resolve'}:
            if args.command == 'continue' and (root / 'stop-request.json').exists():
                (root / 'stop-request.json').unlink()
            session, result = transact(root, config, session, args.command, text)
        elif session.mode == 'running':
            if not session.handles:
                session, result = transact(root, config, session, 'start', config['locator'])
            else:
                adapter = LocalAdapter(root, config)
                handle = session.handles[session.expected_actor]
                record = adapter.instances[handle]
                response_id = record.get('response_id')
                if not response_id:
                    raise RuntimeError('No confirmed response ID; inspect receipts, do not resend')
                capture = Capture('', response_id, False)
                counter_path = root / 'capture-attempts.json'
                counters = read(counter_path) if counter_path.exists() else {}
                key = handle + '/' + response_id
                cached = root / 'ready-capture.json'
                if cached.exists() and read(cached).get('key') == key:
                    capture = Capture(**read(cached)['capture'])
                while not capture.complete and counters.get(key, 0) < session.max_retries + 1:
                    counters[key] = counters.get(key, 0) + 1
                    save(counter_path, counters)
                    capture = adapter.capture(handle, response_id)
                    if capture.complete:
                        save(cached, {'key': key, 'capture': asdict(capture)})
                if not capture.complete:
                    result = {'status': 'capture_blocked', 'response_id': response_id,
                              'detail': 'Three safe capture attempts exhausted; state unchanged; no new automatic retry budget on restart',
                              'original_response': capture.text, 'capture_complete': False}
                    save(root / 'capture-blocked.json', result)
                else:
                    if (root / 'stop-request.json').exists(): session.request_stop()
                    session, result = transact(root, config, session, 'accept', asdict(capture))
        print(json.dumps(result, ensure_ascii=False))


if __name__ == '__main__':
    main()
