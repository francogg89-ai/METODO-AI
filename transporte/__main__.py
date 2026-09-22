"""Offline CLI: validates captured files; never sends prompts."""
import argparse
import json
from pathlib import Path
import sys
from .core import Fault, extract, fingerprint, render_init, strict_json, validate


def read_exact(path):
    return Path(path).read_bytes().decode("utf-8", errors="strict")


def write_exact(path, text):
    # Exclusive creation avoids replacing a previous diagnostic or pending prompt.
    with Path(path).open("xb") as stream:
        stream.write(text.encode("utf-8"))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="action", required=True)
    check = sub.add_parser("validate", help="Validar captura completa sin enviarla")
    check.add_argument("--response", required=True)
    check.add_argument("--work-id", required=True)
    check.add_argument("--actor", choices=["AUDITOR", "CONSTRUCTOR"], required=True)
    check.add_argument("--repository", required=True)
    check.add_argument("--last-turn", type=int, required=True)
    check.add_argument("--output-dir", required=True, help="Directorio nuevo, fuera de Git")
    init = sub.add_parser("init", help="Materializar arranque desde coordenadas verificadas")
    init.add_argument("--config", required=True)
    init.add_argument("--output", required=True)
    args = parser.parse_args(argv)
    try:
        if args.action == "init":
            write_exact(args.output, render_init(strict_json(read_exact(args.config))))
            print(json.dumps({"status": "rendered", "path": str(Path(args.output).resolve()),
                              "git_and_authorization_verified": False}))
            return 0
        original_bytes = Path(args.response).read_bytes()
        directory = Path(args.output_dir)
        directory.mkdir(parents=True, exist_ok=False)
        # Preserve even malformed UTF-8 byte-for-byte before decoding or parsing.
        (directory / "respuesta-original.txt").write_bytes(original_bytes)
        try:
            raw = original_bytes.decode("utf-8", errors="strict")
            obj = validate(extract(raw), work_id=args.work_id, source_actor=args.actor,
                           source_repo=args.repository, last_turn=args.last_turn)
            report = {"status": "valid", "turn_id": obj["turn_id"], "sent": False,
                      "original_path": str((directory / "respuesta-original.txt").resolve())}
            write_exact(directory / "sobre.json", json.dumps(obj, ensure_ascii=False, indent=2))
            if obj["next_prompt"] is not None:
                write_exact(directory / "next_prompt.txt", obj["next_prompt"])
                report["prompt_fingerprint"] = fingerprint(obj["next_prompt"])
        except (Fault, UnicodeError) as exc:
            report = {"status": "failed", "code": getattr(exc, "code", "UTF8"), "detail": str(exc),
                      "actor": args.actor, "expected_turn": args.last_turn + 1,
                      "attempts": 1, "delivery": "NOT_SENT",
                      "original_path": str((directory / "respuesta-original.txt").resolve())}
        write_exact(directory / "reporte.json", json.dumps(report, ensure_ascii=False, indent=2))
        print(json.dumps(report, ensure_ascii=False))
        return 0 if report["status"] == "valid" else 2
    except (Fault, OSError, UnicodeError) as exc:
        print(json.dumps({"status": "failed", "code": getattr(exc, "code", "IO"), "detail": str(exc)}))
        return 2


if __name__ == "__main__":
    sys.exit(main())
