import json
from pathlib import Path
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO

from transporte.core import (Capture, Fault, Prepared, Repair, Session, extract,
                            fingerprint, parse_locator, render_init, validate)
from transporte.__main__ import main

PROMPT = 'ROL=CONSTRUCTOR\r\nC:/Franco/ñ\n"comillas" \\ $() `literal` 🛶\n\nfin\n'


def envelope(actor="AUDITOR", turn=1, instance="current"):
    return dict(protocol="metodo-ai-hop/v1", work_id="prueba", turn_id=turn, actor=actor,
                repository="usuario/audit" if actor == "AUDITOR" else "usuario/work",
                commit="a" * 40, next_actor="CONSTRUCTOR" if actor == "AUDITOR" else "AUDITOR",
                next_instance=instance, next_prompt=PROMPT, human_need=None, unit=None, final=False)


def wrap(obj):
    return "```json\n" + json.dumps(obj, ensure_ascii=False) + "\n```"


def check(obj):
    return validate(obj, work_id="prueba", source_actor="AUDITOR", source_repo="usuario/audit", last_turn=0)


class FakeAdapter:
    def __init__(self):
        self.sent = []
        self.inserts = []
        self.bad_prepares = 0
        self.anomalies = 0
        self.receipts = ["DELIVERED"]
        self.readback_value = "same"
        self.current = True
        self.serial = 0
        self.fresh_override = None
        self.recapture = None
        self.repairs = []
        self.repair_calls = 0

    def is_current(self, role, handle):
        return self.current

    def open_fresh(self, role):
        self.serial += 1
        return self.fresh_override or f"{role}-{self.serial}"

    def capture(self, handle, response_id):
        return self.recapture

    def prepare(self, handle, text):
        self.inserts.append((handle, text))
        self.prepared = text
        if self.bad_prepares:
            self.bad_prepares -= 1
            self.prepared += "CORRUPTO"
        anomaly = self.anomalies > 0
        self.anomalies = max(0, self.anomalies - 1)
        return Prepared(self.prepared, anomaly)

    def readback(self, handle):
        return self.prepared if self.readback_value == "same" else self.readback_value

    def send(self, handle):
        result = self.receipts.pop(0) if len(self.receipts) > 1 else self.receipts[0]
        if isinstance(result, Exception):
            raise result
        self.sent.append((handle, self.prepared, result))
        return result

    def repair(self, handle, response_id, request):
        self.repair_calls += 1
        return self.repairs.pop(0) if self.repairs else None


def session():
    return Session("prueba", {"AUDITOR": "usuario/audit", "CONSTRUCTOR": "usuario/work"},
                   handles={"AUDITOR": "a0", "CONSTRUCTOR": "c0"})


class ContractTests(unittest.TestCase):
    def test_unicode_and_line_endings_preserved(self):
        raw = wrap(envelope())
        self.assertEqual(check(extract(raw))["next_prompt"], PROMPT)
        self.assertEqual(fingerprint(PROMPT)["utf8_bytes"], len(PROMPT.encode()))

    def test_rejects_extra_prose_and_multiple_objects(self):
        for raw in ["hola\n" + wrap(envelope()), wrap(envelope()) + "\nfin",
                    wrap(envelope()) + "\n" + wrap(envelope()), json.dumps(envelope())]:
            with self.subTest(raw=raw[:20]), self.assertRaises(Fault):
                extract(raw)

    def test_duplicate_key_rejected(self):
        with self.assertRaises(Fault) as exc:
            extract('```json\n{"a":1,"a":2}\n```')
        self.assertEqual(exc.exception.code, "DUPLICATE_KEY")

    def test_schema_rejections(self):
        for key, value in [("turn_id", True), ("turn_id", 2), ("turn_id", 1.0),
                           ("work_id", "otro"), ("actor", "CONSTRUCTOR"), ("actor", []),
                           ("commit", "a" * 39), ("repository", "otro/audit"),
                           ("next_instance", []), ("next_prompt", ""), ("final", 0)]:
            obj = envelope(); obj[key] = value
            with self.subTest(key=key, value=value), self.assertRaises(Fault):
                check(obj)

    def test_missing_extra_keys(self):
        obj = envelope(); del obj["unit"]
        with self.assertRaises(Fault): check(obj)
        obj = envelope(); obj["other"] = 1
        with self.assertRaises(Fault): check(obj)

    def test_surrogate_and_nonfinite(self):
        for raw in ['```json\n{"x":"\\ud800"}\n```', '```json\n{"x":NaN}\n```']:
            with self.assertRaises(Fault): extract(raw)

    def test_constructor_cannot_close(self):
        obj = envelope("CONSTRUCTOR")
        obj.update(final=True, next_actor=None, next_instance=None, next_prompt=None)
        with self.assertRaises(Fault):
            validate(obj, work_id="prueba", source_actor="CONSTRUCTOR", source_repo="usuario/work", last_turn=0)

    def test_human_need_material_requires_checkpoint(self):
        obj = human_need(); obj["human_need"]["type"] = "material"
        with self.assertRaises(Fault): check(obj)
        obj["human_need"].update(checkpoint=dict(repository="usuario/work", commit="b"*40, path="u/CHECKPOINT_HUMANO.md"), guide_prompt="Ayudar")
        self.assertEqual(check(obj), obj)
        obj["human_need"]["checkpoint"]["path"] = "../secreto"
        with self.assertRaises(Fault): check(obj)

    def test_terminal_shapes(self):
        obj = envelope(); obj.update(final=True, next_actor=None, next_instance=None, next_prompt=None)
        self.assertEqual(check(obj), obj)
        obj = human_need(); obj["final"] = True
        with self.assertRaises(Fault): check(obj)


def human_need():
    obj = envelope()
    obj.update(next_actor=None, next_instance=None, next_prompt=None,
               human_need=dict(id="H1", type="no_material", request="NECESIDAD DEL HUMANO: elegir",
                               checkpoint=None, guide_prompt=None, expected_evidence=["decisión"], resume_actor="AUDITOR"))
    return obj


class DeliveryTests(unittest.TestCase):
    def run_one(self, s, a, obj=None):
        return s.accept(a, Capture(wrap(obj or envelope()), "r1"), source_actor="AUDITOR")

    def test_direct_transfer_preserves_value(self):
        s = session(); a = FakeAdapter()
        result = self.run_one(s, a)
        self.assertEqual(result["status"], "delivered")
        self.assertEqual(a.sent[0][1].encode(), PROMPT.encode())
        self.assertEqual(s.last_turn, 1)

    def test_retry_before_send(self):
        s = session(); a = FakeAdapter(); a.bad_prepares = 2
        result = self.run_one(s, a)
        self.assertEqual(result["status"], "delivered")
        self.assertEqual(len(a.inserts), 3); self.assertEqual(len(a.sent), 1)

    def test_exhaustion_does_not_advance(self):
        s = session(); a = FakeAdapter(); a.bad_prepares = 3
        result = self.run_one(s, a)
        self.assertEqual(result["code"], "INTEGRITY")
        self.assertEqual(s.last_turn, 0); self.assertEqual(a.sent, [])
        self.assertEqual(result["original_response"], wrap(envelope()))
        self.assertEqual(result["attempts"]["prepare_send"], 3)

    def test_readback_mismatch_blocks_send(self):
        s = session(); a = FakeAdapter(); a.readback_value = "distinto"
        self.assertEqual(self.run_one(s, a)["code"], "INTEGRITY")
        self.assertEqual(a.sent, [])

    def test_anomaly_blocks_send_without_readback(self):
        s = session(); a = FakeAdapter(); a.readback_value = None; a.anomalies = 3
        self.assertEqual(self.run_one(s, a)["code"], "INTEGRITY")
        self.assertEqual(a.sent, [])

    def test_no_readback_is_explicit_limit(self):
        s = session(); a = FakeAdapter(); a.readback_value = None
        result = self.run_one(s, a)
        self.assertFalse(result["readback_available"])
        self.assertEqual(result["status"], "delivered")

    def test_unknown_never_replayed(self):
        s = session(); a = FakeAdapter(); a.receipts = ["UNKNOWN", "DELIVERED"]
        result = self.run_one(s, a)
        self.assertEqual(result["delivery"], "UNKNOWN")
        self.assertEqual(len(a.sent), 1); self.assertEqual(s.last_turn, 0)
        with self.assertRaises(Fault): self.run_one(s, a)

    def test_exception_after_send_never_replayed(self):
        s = session(); a = FakeAdapter(); a.receipts = [OSError("interrumpido")]
        result = self.run_one(s, a)
        self.assertEqual(result["delivery"], "UNKNOWN")
        self.assertEqual(len(a.inserts), 1); self.assertEqual(s.last_turn, 0)

    def test_not_sent_retry_and_exhaustion(self):
        s = session(); a = FakeAdapter(); a.receipts = ["NOT_SENT", "DELIVERED"]
        self.assertEqual(self.run_one(s, a)["status"], "delivered")
        self.assertEqual(len(a.sent), 2)
        s = session(); a = FakeAdapter(); a.receipts = ["NOT_SENT"]
        self.assertEqual(self.run_one(s, a)["code"], "NOT_SENT")
        self.assertEqual(s.last_turn, 0); self.assertEqual(len(a.sent), 3)

    def test_fresh_promoted_only_on_delivery(self):
        s = session(); a = FakeAdapter(); a.receipts = ["UNKNOWN"]
        self.run_one(s, a, envelope(instance="fresh"))
        self.assertEqual(s.handles["CONSTRUCTOR"], "c0")
        s = session(); a = FakeAdapter()
        self.run_one(s, a, envelope(instance="fresh"))
        self.assertNotEqual(s.handles["CONSTRUCTOR"], "c0")
        self.assertIn("c0", s.known["CONSTRUCTOR"])

    def test_reused_fresh_rejected(self):
        s = session(); a = FakeAdapter(); a.fresh_override = "c0"
        self.assertEqual(self.run_one(s, a, envelope(instance="fresh"))["code"], "FRESH")
        self.assertEqual(a.sent, [])

    def test_current_loss_no_fresh(self):
        s = session(); a = FakeAdapter(); a.current = False
        self.assertEqual(self.run_one(s, a)["code"], "CURRENT_LOST")
        self.assertEqual(a.serial, 0)

    def test_complete_recapture_same_response(self):
        s = session(); a = FakeAdapter(); a.recapture = Capture(wrap(envelope()), "r1")
        result = s.accept(a, Capture("parcial", "r1", False), source_actor="AUDITOR")
        self.assertEqual(result["status"], "delivered")
        self.assertEqual(len(s.captures), 2)

    def test_recapture_other_response_rejected(self):
        s = session(); a = FakeAdapter(); a.recapture = Capture(wrap(envelope()), "r2")
        result = s.accept(a, Capture("parcial", "r1", False), source_actor="AUDITOR")
        self.assertEqual(result["code"], "CAPTURE_ID"); self.assertEqual(a.sent, [])

    def test_incomplete_capture_report(self):
        s = session(); a = FakeAdapter(); a.recapture = Capture("parcial", "r1", False)
        result = s.accept(a, a.recapture, source_actor="AUDITOR")
        self.assertEqual(result["code"], "CAPTURE_INCOMPLETE")
        self.assertFalse(result["capture_complete"])
        self.assertEqual(result["original_response"], "parcial")

    def test_format_reissue_no_turn_consumed(self):
        s = session(); a = FakeAdapter(); a.repairs = [Repair(Capture(wrap(envelope()), "repair1"), True)]
        raw = json.dumps(envelope())
        result = s.accept(a, Capture(raw, "r1"), source_actor="AUDITOR")
        self.assertEqual(result["status"], "delivered"); self.assertEqual(s.last_turn, 1)
        self.assertEqual(s.original.text, raw); self.assertEqual(a.repair_calls, 1)

    def test_reissue_cannot_change_payload(self):
        s = session(); a = FakeAdapter(); changed = envelope(); changed["next_prompt"] += "CAMBIO"
        a.repairs = [Repair(Capture(wrap(changed), "repair1"), True)]
        result = s.accept(a, Capture(json.dumps(envelope()), "r1"), source_actor="AUDITOR")
        self.assertEqual(result["code"], "REPAIR_CHANGED"); self.assertEqual(a.sent, [])

    def test_no_repair_without_material_guarantee(self):
        s = session(); a = FakeAdapter(); a.repairs = [Repair(Capture(wrap(envelope()), "repair1"), False)]
        result = s.accept(a, Capture(json.dumps(envelope()), "r1"), source_actor="AUDITOR")
        self.assertEqual(result["code"], "REPAIR_MATERIAL"); self.assertEqual(a.sent, [])

    def test_broken_json_not_inferred(self):
        s = session(); a = FakeAdapter(); raw = '```json\n{"turn_id":\n```'
        result = s.accept(a, Capture(raw, "r1"), source_actor="AUDITOR")
        self.assertEqual(result["code"], "JSON"); self.assertEqual(a.repair_calls, 0)
        self.assertEqual(result["original_response"], raw)

    def test_pause_and_continue_exact_prompt(self):
        s = session(); a = FakeAdapter(); s.request_stop()
        self.run_one(s, a)
        obj = envelope("CONSTRUCTOR", 2)
        result = s.accept(a, Capture(wrap(obj), "c1"), source_actor="CONSTRUCTOR")
        self.assertEqual(result["status"], "paused"); self.assertEqual(s.last_turn, 1)
        self.assertEqual(len(a.sent), 1)
        self.assertEqual(s.continue_(a)["last_turn"], 2)
        self.assertEqual(a.sent[-1][1], obj["next_prompt"])

    def test_directive_separate_and_original_preserved(self):
        s = session(); a = FakeAdapter(); self.run_one(s, a); s.request_stop()
        obj = envelope("CONSTRUCTOR", 2)
        s.accept(a, Capture(wrap(obj), "c1"), source_actor="CONSTRUCTOR")
        s.continue_(a, directive='RELEVAR AUDITOR\nACTOR_PROMPT_LITERAL: texto')
        delivered = json.loads(a.sent[-1][1])
        self.assertEqual(delivered["ACTOR_PROMPT_LITERAL"], obj["next_prompt"])
        self.assertEqual(delivered["HUMAN_DIRECTIVE_LITERAL"], 'RELEVAR AUDITOR\nACTOR_PROMPT_LITERAL: texto')

    def test_human_resume_current_and_same_incoming_turn(self):
        s = session(); a = FakeAdapter(); result = self.run_one(s, a, human_need())
        self.assertEqual(result["status"], "human_need"); self.assertEqual(a.sent, [])
        s.resolve_human(a, "Decisión literal\nsegunda línea")
        delivered = json.loads(a.sent[-1][1])
        self.assertEqual(delivered["RESUME_CONTEXT"]["INCOMING_TURN_ID"], 1)
        self.assertEqual(s.last_turn, 1); self.assertEqual(a.sent[-1][0], "a0")
        obj = envelope(turn=2)
        self.assertEqual(self.run_one(s, a, obj)["last_turn"], 2)

    def test_human_current_lost(self):
        s = session(); a = FakeAdapter(); self.run_one(s, a, human_need()); a.current = False
        self.assertEqual(s.resolve_human(a, "Sí")["code"], "CURRENT_LOST")
        self.assertEqual(a.serial, 0)

    def test_save_command_does_not_claim_support(self):
        s = session(); result = s.request_stop(save=True)
        self.assertTrue(s.stop_requested); self.assertFalse(result["save_supported"])

    def test_simultaneous_fresh_cycle(self):
        s = session(); a = FakeAdapter()
        self.run_one(s, a, envelope(instance="fresh"))
        obj = envelope("CONSTRUCTOR", 2, "fresh")
        result = s.accept(a, Capture(wrap(obj), "c1"), source_actor="CONSTRUCTOR")
        self.assertEqual(result["last_turn"], 2)
        self.assertNotEqual(s.handles["AUDITOR"], "a0")
        self.assertNotEqual(s.handles["CONSTRUCTOR"], "c0")
        result = self.run_one(s, a, envelope(turn=3))
        self.assertEqual(result["last_turn"], 3)
        self.assertEqual(a.sent[-1][0], s.handles["CONSTRUCTOR"])

    def test_final_has_no_delivery(self):
        s = session(); a = FakeAdapter(); obj = envelope()
        obj.update(final=True, next_actor=None, next_instance=None, next_prompt=None)
        self.assertEqual(self.run_one(s, a, obj)["status"], "final")
        self.assertEqual(s.last_turn, 1); self.assertEqual(a.sent, [])

    def test_wrong_origin_report_preserves_actual_role(self):
        s = session(); a = FakeAdapter()
        raw = wrap(envelope("CONSTRUCTOR"))
        result = s.accept(a, Capture(raw, "c1"), source_actor="CONSTRUCTOR")
        self.assertEqual(result["code"], "ACTOR")
        self.assertEqual(result["actor"], "CONSTRUCTOR")
        self.assertEqual(result["expected_actor"], "AUDITOR")
        self.assertEqual(result["original_response"], raw)

    def test_retries_cannot_exceed_two(self):
        with self.assertRaises(Fault):
            Session("p", {"AUDITOR": "u/a", "CONSTRUCTOR": "u/w"}, max_retries=3)


class InitAndCliTests(unittest.TestCase):
    def config(self):
        return dict(work_id="prueba", carril="A", method_repo="francogg89-ai/METODO-AI", method_sha="a"*40,
                    constitution_repo="usuario/manifiestos", constitution_path="manifiestos/prueba/CONSTITUCION_INICIAL.md",
                    constitution_sha="b"*40, auditor_runtime="ChatGPT web", constructor_runtime="Claude Code local",
                    constructor_local_path="C:/Franco/work")

    def test_init_and_locator(self):
        text = render_init(self.config()); line = text.splitlines()[-1]
        canonical, fields = parse_locator("\ufeff" + line + " \n")
        self.assertEqual(canonical, line); self.assertEqual(fields["WORK_ID"], "prueba")
        s = Session("prueba", {"AUDITOR": "usuario/audit", "CONSTRUCTOR": "usuario/work"}); a = FakeAdapter()
        self.assertEqual(s.start(a, line)["status"], "started")
        self.assertEqual(a.sent[0][1], line); self.assertEqual(s.last_turn, 0)

    def test_init_placeholders_and_path_injection_rejected(self):
        for key, value in [("method_sha", "<sha>"), ("constitution_path", "../x"),
                           ("work_id", "p|CARRIL=X"), ("constructor_runtime", "x\notra")]:
            obj = self.config(); obj[key] = value
            with self.subTest(key=key), self.assertRaises(Fault): render_init(obj)

    def test_cli_preserves_original_and_prompt(self):
        with tempfile.TemporaryDirectory() as tmp, redirect_stdout(StringIO()):
            src = Path(tmp)/"source.txt"; out = Path(tmp)/"out"
            raw = wrap(envelope()).replace("\n", "\r\n").encode()
            src.write_bytes(raw)
            result = main(["validate", "--response", str(src), "--work-id", "prueba", "--actor", "AUDITOR",
                           "--repository", "usuario/audit", "--last-turn", "0", "--output-dir", str(out)])
            self.assertEqual(result, 0)
            self.assertEqual((out/"respuesta-original.txt").read_bytes(), raw)
            self.assertEqual((out/"next_prompt.txt").read_bytes(), PROMPT.encode())

    def test_cli_preserves_invalid_utf8(self):
        with tempfile.TemporaryDirectory() as tmp, redirect_stdout(StringIO()):
            src = Path(tmp)/"source.txt"; out = Path(tmp)/"out"; src.write_bytes(b"\xfforiginal")
            result = main(["validate", "--response", str(src), "--work-id", "prueba", "--actor", "AUDITOR",
                           "--repository", "usuario/audit", "--last-turn", "0", "--output-dir", str(out)])
            self.assertEqual(result, 2)
            self.assertEqual((out/"respuesta-original.txt").read_bytes(), b"\xfforiginal")


if __name__ == "__main__":
    unittest.main()
