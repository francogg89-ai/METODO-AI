import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from transporte.core import Session, Capture
from transporte.local import Tape, Uncertain, LocalAdapter, save, read, snapshot, restore, transact

class LocalTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.config = {'claude': {'executable': '/native/claude.exe', 'cwd': str(self.root), 'tools': ['Read', 'Edit', 'Bash'], 'permission_mode': 'default'}}

    def test_tape_completed_send_never_replays(self):
        path = self.root/'tape.json'; calls=[]
        Tape(path).call('send',['h'], lambda: calls.append(1) or 'DELIVERED', True)
        result=Tape(path).call('send',['h'], lambda: calls.append(2), True)
        self.assertEqual(result,'DELIVERED'); self.assertEqual(calls,[1])

    def test_interrupted_send_is_not_retried(self):
        path=self.root/'tape.json'
        def die(): raise KeyboardInterrupt()
        with self.assertRaises(KeyboardInterrupt): Tape(path).call('send',['h'],die,True)
        with self.assertRaises(Uncertain): Tape(path).call('send',['h'],lambda:self.fail('resent'),True)

    def test_changed_replay_rejected(self):
        path=self.root/'tape.json'; Tape(path).call('prepare',['original'],lambda:1)
        with self.assertRaises(Uncertain): Tape(path).call('prepare',['altered'],lambda:2)

    def test_roundtrip_entire_session(self):
        s=Session('test',{'AUDITOR':'o/a','CONSTRUCTOR':'o/c'},handles={'AUDITOR':'a'},last_turn=2)
        s.known['AUDITOR'].add('retired'); s.stop_requested=True
        s.original=Capture('á\n\\','r',False); s.mode='paused'; s.pending={'text':'x'}
        self.assertEqual(snapshot(restore(snapshot(s))),snapshot(s))

    def test_claude_fresh_and_current_flags(self):
        a=LocalAdapter(self.root,self.config)
        fresh=a.claude_argv({'session_id':'s','started':False})
        current=a.claude_argv({'session_id':'s','started':True})
        self.assertIn('--session-id',fresh); self.assertNotIn('--resume',fresh)
        self.assertIn('--resume',current); self.assertNotIn('--continue',current)
        self.assertNotIn('--session-id',current)

    def test_exact_utf8_written(self):
        a=LocalAdapter(self.root,self.config); h=a.open_fresh('CONSTRUCTOR')
        text='á\nWindows C:\\algo\n"fin"\n'
        a.prepare(h,text)
        self.assertEqual(Path(a.instances[h]['prepared']).read_bytes(),text.encode())
        self.assertEqual(a.readback(h),text)

    def test_wrong_claude_session_is_unknown(self):
        a=LocalAdapter(self.root,self.config); h=a.open_fresh('CONSTRUCTOR'); a.prepare(h,'x')
        class Process:
            pid=100; returncode=0
            def __init__(self,*args,**kw):
                self.stdout=kw['stdout']
            def communicate(self,data):
                self.stdout.write(json.dumps({'session_id':'wrong','result':'ok','uuid':'r','is_error':False}).encode())
        with patch('transporte.local.subprocess.Popen',Process):
            self.assertEqual(a.send(h),'UNKNOWN')

    def test_current_lost_never_creates_fresh(self):
        a=LocalAdapter(self.root,self.config)
        self.assertFalse(a.is_current('CONSTRUCTOR','missing'))
        self.assertEqual(a.instances,{})

    def test_snapshot_terminal_accept_without_send(self):
        s=Session('test',{'AUDITOR':'o/a','CONSTRUCTOR':'o/c'},handles={'AUDITOR':'a'},last_turn=2)
        a=LocalAdapter(self.root,self.config)
        obj=dict(protocol='metodo-ai-hop/v1',work_id='test',turn_id=3,actor='AUDITOR',repository='o/a',commit='a'*40,next_actor=None,next_instance=None,next_prompt=None,human_need=None,unit=None,final=True)
        cap=Capture('```json\n'+json.dumps(obj)+'\n```','id')
        with patch.object(LocalAdapter,'is_current',return_value=True),patch.object(LocalAdapter,'send',side_effect=AssertionError('send')):
            result=transact(self.root,self.config,s,'accept',{'text':cap.text,'response_id':'id','complete':True})
        self.assertEqual(result[1]['status'],'final');self.assertEqual(read(self.root/'state.json')['last_turn'],3)

if __name__=='__main__':unittest.main()
