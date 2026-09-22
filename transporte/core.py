"""Deterministic validation and delivery; no model, network or Git calls."""
from __future__ import annotations

from dataclasses import dataclass, field
from hashlib import sha256
import json
import re
from typing import Protocol

PROTOCOL = "metodo-ai-hop/v1"
ROLES = {"AUDITOR", "CONSTRUCTOR"}
FIELDS = {"protocol", "work_id", "turn_id", "actor", "repository", "commit",
          "next_actor", "next_instance", "next_prompt", "human_need", "unit", "final"}
SHA = re.compile(r"[0-9a-fA-F]{40}\Z")
REPO = re.compile(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+\Z")
ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]*\Z")
FENCE = re.compile(r"\s*```json\r?\n(?P<body>.*?)\r?\n```\s*\Z", re.DOTALL)


class Fault(ValueError):
    def __init__(self, code: str, detail: str):
        super().__init__(detail)
        self.code = code


def require(ok: bool, code: str, detail: str) -> None:
    if not ok:
        raise Fault(code, detail)


def nonempty(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def matches(pattern: re.Pattern, value: object) -> bool:
    return isinstance(value, str) and pattern.fullmatch(value) is not None


def safe_path(value: object) -> bool:
    return (nonempty(value) and not str(value).startswith("/")
            and "\\" not in value and ":" not in value
            and all(p not in {"", ".", ".."} for p in value.split("/"))
            and not any(ord(c) < 32 for c in value))


def fingerprint(text: str) -> dict:
    try:
        data = text.encode("utf-8", errors="strict")
    except (UnicodeError, AttributeError) as exc:
        raise Fault("UTF8", "Texto no representable como UTF-8 estricto") from exc
    return {"utf8_bytes": len(data), "sha256": sha256(data).hexdigest()}


def identical(a: str, b: str) -> bool:
    return fingerprint(a) == fingerprint(b) and a == b


def _pairs(items):
    result = {}
    for key, value in items:
        require(key not in result, "DUPLICATE_KEY", f"Clave duplicada: {key}")
        result[key] = value
    return result


def _nonfinite(value):
    raise Fault("JSON", f"Número JSON no admitido: {value}")


def strict_json(text: str):
    try:
        result = json.loads(text, object_pairs_hook=_pairs, parse_constant=_nonfinite)
        # Escaped unpaired surrogates are accepted by json.loads but not by UTF-8.
        fingerprint(json.dumps(result, ensure_ascii=False))
        return result
    except (json.JSONDecodeError, RecursionError, OverflowError) as exc:
        raise Fault("JSON", "JSON inválido") from exc


def extract(raw: str) -> dict:
    fingerprint(raw)
    match = FENCE.fullmatch(raw)
    require(match is not None, "RESPONSE_FORM", "Se exige exclusivamente un bloque json")
    obj = strict_json(match.group("body"))
    require(type(obj) is dict, "OBJECT", "El sobre debe ser un objeto")
    return obj


def validate(obj: dict, *, work_id: str, source_actor: str,
             source_repo: str, last_turn: int) -> dict:
    require(type(obj) is dict and set(obj) == FIELDS, "FIELDS", "Campos ausentes o adicionales")
    require(obj["protocol"] == PROTOCOL, "PROTOCOL", "Protocolo distinto")
    require(matches(ID, obj["work_id"]) and obj["work_id"] == work_id,
            "WORK_ID", "Trabajo distinto o inválido")
    require(type(last_turn) is int and last_turn >= 0, "STATE", "Último turno inválido")
    require(type(obj["turn_id"]) is int and obj["turn_id"] == last_turn + 1,
            "TURN", "El turno no es el sucesor exacto")
    require(isinstance(obj["actor"], str) and obj["actor"] in ROLES
            and obj["actor"] == source_actor, "ACTOR", "Rol no coincide con origen")
    require(matches(REPO, obj["repository"]) and obj["repository"] == source_repo,
            "REPOSITORY", "Repositorio no coincide con origen")
    require(matches(SHA, obj["commit"]), "COMMIT", "Commit debe ser SHA de 40 caracteres")
    require(type(obj["final"]) is bool, "FINAL", "final debe ser booleano")
    require(obj["unit"] is None or nonempty(obj["unit"]), "UNIT", "unit inválido")
    need = obj["human_need"]
    if need is not None:
        keys = {"id", "type", "request", "checkpoint", "guide_prompt", "expected_evidence", "resume_actor"}
        require(type(need) is dict and set(need) == keys, "HUMAN_NEED", "Campos de necesidad inválidos")
        require(nonempty(need["id"]) and isinstance(need["type"], str)
                and need["type"] in {"material", "no_material"}
                and nonempty(need["request"])
                and need["request"].startswith("NECESIDAD DEL HUMANO")
                and need["resume_actor"] == "AUDITOR", "HUMAN_NEED", "Necesidad inválida")
        evidence = need["expected_evidence"]
        require(type(evidence) is list and bool(evidence) and all(nonempty(x) for x in evidence),
                "HUMAN_NEED", "Evidencia esperada inválida")
        if need["type"] == "material":
            point = need["checkpoint"]
            require(type(point) is dict and set(point) == {"repository", "commit", "path"},
                    "CHECKPOINT", "Checkpoint incompleto")
            require(matches(REPO, point["repository"]) and matches(SHA, point["commit"])
                    and safe_path(point["path"]) and nonempty(need["guide_prompt"]),
                    "CHECKPOINT", "Checkpoint inválido")
        else:
            require(need["checkpoint"] is None and need["guide_prompt"] is None,
                    "CHECKPOINT", "Necesidad no material no lleva checkpoint")
    if need is not None or obj["final"]:
        require(not (need is not None and obj["final"]), "COMBINATION", "Necesidad y cierre simultáneos")
        require(all(obj[x] is None for x in ("next_actor", "next_instance", "next_prompt")),
                "COMBINATION", "Una detención no lleva destino")
        require(obj["unit"] is None, "COMBINATION", "Una detención no declara transición")
    else:
        require(isinstance(obj["next_actor"], str) and obj["next_actor"] in ROLES
                and isinstance(obj["next_instance"], str) and obj["next_instance"] in {"fresh", "current"}
                and nonempty(obj["next_prompt"]), "DESTINATION", "Destino incompleto")
        require(obj["next_actor"] != source_actor, "DESTINATION", "No hay pase ordinario a sí mismo")
        fingerprint(obj["next_prompt"])
    if source_actor == "CONSTRUCTOR":
        require(need is None and obj["unit"] is None and obj["final"] is False,
                "AUTHORITY", "Constructor no emite necesidad, transición ni cierre")
    return obj


@dataclass(frozen=True)
class Capture:
    text: str
    response_id: str
    complete: bool = True


@dataclass(frozen=True)
class Prepared:
    text: str
    anomaly: bool = False


@dataclass(frozen=True)
class Repair:
    capture: Capture
    material_unchanged: bool


class Adapter(Protocol):
    def capture(self, handle: str, response_id: str) -> Capture: ...
    def open_fresh(self, role: str) -> str: ...
    def is_current(self, role: str, handle: str) -> bool: ...
    def prepare(self, handle: str, text: str) -> Prepared: ...
    def readback(self, handle: str) -> str | None: ...
    def send(self, handle: str) -> str: ...
    def repair(self, handle: str, response_id: str, request: str) -> Repair | None: ...


@dataclass
class Session:
    work_id: str
    repositories: dict[str, str]
    handles: dict[str, str] = field(default_factory=dict)
    last_turn: int = 0
    max_retries: int = 2
    expected_actor: str = "AUDITOR"
    mode: str = "running"
    stop_requested: bool = False
    pending: dict | None = None
    original: Capture | None = None
    captures: list = field(default_factory=list)
    known: dict = field(default_factory=lambda: {r: set() for r in ROLES})
    prepared: str | None = None
    attempts: dict = field(default_factory=dict)
    delivery: str = "NOT_SENT"
    report: dict | None = None
    readback_available: bool | None = None
    source_actor: str | None = None

    def __post_init__(self):
        require(matches(ID, self.work_id), "CONFIG", "work_id inválido")
        require(set(self.repositories) == ROLES and all(matches(REPO, x) for x in self.repositories.values()),
                "CONFIG", "Repositorios de ambos roles requeridos")
        require(len(set(self.repositories.values())) == 2, "CONFIG", "Work y audit deben estar separados")
        require(type(self.max_retries) is int and 0 <= self.max_retries <= 2,
                "CONFIG", "Como máximo dos reintentos")
        require(type(self.last_turn) is int and self.last_turn >= 0, "CONFIG", "Turno inválido")
        require(set(self.handles) <= ROLES and all(nonempty(v) for v in self.handles.values()),
                "CONFIG", "Handles inválidos")
        for role, handle in self.handles.items():
            self.known[role].add(handle)

    def _halt(self, error: Exception) -> dict:
        self.mode = "failed"
        self.report = {
            "status": "failed", "code": getattr(error, "code", "ADAPTER_ERROR"),
            "detail": str(error), "work_id": self.work_id, "actor": self.source_actor,
            "expected_actor": self.expected_actor,
            "handle": self.handles.get(self.source_actor), "last_turn": self.last_turn,
            "expected_turn": self.last_turn + 1, "attempts": dict(self.attempts),
            "delivery": self.delivery, "readback_available": self.readback_available,
            "original_response": self.original.text if self.original else None,
            "capture_complete": self.original.complete if self.original else False,
            "captures": list(self.captures), "prepared_text": self.prepared,
        }
        return self.report

    def _deliver(self, adapter: Adapter, role: str, instance: str, text: str) -> None:
        fingerprint(text)
        handle = self.handles.get(role)
        if instance == "fresh":
            handle = adapter.open_fresh(role)
            require(nonempty(handle) and handle not in self.known[role], "FRESH", "Instancia no demostrablemente nueva")
            self.known[role].add(handle)
        else:
            require(handle is not None and adapter.is_current(role, handle), "CURRENT_LOST", "Instancia current perdida")
        self.delivery = "NOT_SENT"
        for attempt in range(self.max_retries + 1):
            self.attempts["prepare_send"] = attempt + 1
            value = adapter.prepare(handle, text)
            self.prepared = value.text
            readback = adapter.readback(handle)
            self.readback_available = readback is not None
            good = not value.anomaly and identical(text, value.text)
            if readback is not None:
                good = good and identical(text, readback)
                self.prepared = readback
            if not good:
                if attempt < self.max_retries:
                    continue
                raise Fault("INTEGRITY", "Preparación alterada; no se envió")
            # After this boundary every exception is ambiguous; no replay.
            self.delivery = "UNKNOWN"
            result = adapter.send(handle)
            require(result in {"DELIVERED", "NOT_SENT", "UNKNOWN"}, "RECEIPT", "Recibo inválido")
            self.delivery = result
            if result == "DELIVERED":
                self.handles[role] = handle
                return
            if result == "UNKNOWN":
                raise Fault("DELIVERY_UNKNOWN", "No se puede determinar si comenzó la ejecución")
        raise Fault("NOT_SENT", "Se agotaron los intentos sin entrega")

    def start(self, adapter: Adapter, locator: str) -> dict:
        require(self.last_turn == 0 and not self.handles and self.mode == "running", "STATE", "Arranque ya efectuado")
        try:
            canonical, fields = parse_locator(locator)
            require(fields["WORK_ID"] == self.work_id, "WORK_ID", "Locator de otro trabajo")
            self._deliver(adapter, "AUDITOR", "fresh", canonical)
            return {"status": "started", "last_turn": 0}
        except Exception as exc:
            return self._halt(exc)

    def request_stop(self, save: bool = False) -> dict:
        self.stop_requested = True
        return {"status": "stop_requested", "save_supported": False,
                "detail": "Guardado para tres agentes nuevos no implementado" if save else "Pausa solicitada"}

    def accept(self, adapter: Adapter, capture: Capture, *, source_actor: str) -> dict:
        require(self.mode == "running", "STATE", "Sesión no está esperando una respuesta ordinaria")
        self.original = capture
        self.source_actor = source_actor
        self.captures = []
        self.attempts = {}
        self.prepared = None
        self.delivery = "NOT_SENT"
        self.readback_available = None
        try:
            require(source_actor == self.expected_actor, "ACTOR", "Origen inesperado")
            handle = self.handles.get(source_actor)
            require(handle is not None and adapter.is_current(source_actor, handle), "CURRENT_LOST", "Origen current perdido")
            current = capture
            for attempt in range(self.max_retries + 1):
                self.attempts["capture"] = attempt + 1
                self.captures.append({"text": current.text, "response_id": current.response_id, "complete": current.complete})
                require(nonempty(current.response_id) and current.response_id == capture.response_id,
                        "CAPTURE_ID", "Recaptura de otra respuesta")
                if current.complete:
                    break
                if attempt < self.max_retries:
                    current = adapter.capture(handle, capture.response_id)
            require(current.complete, "CAPTURE_INCOMPLETE", "Captura incompleta tras los intentos")
            try:
                obj = extract(current.text)
            except Fault as exc:
                # Only an unambiguous, already parseable JSON object may have its wrapper repaired.
                # Broken JSON, duplicate keys or several candidates cannot be safely inferred.
                require(exc.code == "RESPONSE_FORM", exc.code, str(exc))
                base = strict_json(current.text.strip())
                validate(base, work_id=self.work_id, source_actor=source_actor,
                         source_repo=self.repositories[source_actor], last_turn=self.last_turn)
                obj = None
                for attempt in range(self.max_retries):
                    self.attempts["repair"] = attempt + 1
                    repaired = adapter.repair(handle, capture.response_id,
                        "REEMITIR_SALIDA: corregir sólo el bloque json; mismos valores, turno y resultado; sin trabajo ni commits.")
                    require(repaired is not None, "REPAIR_UNAVAILABLE", "No existe canal de reparación restringida")
                    self.captures.append({"text": repaired.capture.text, "response_id": repaired.capture.response_id,
                                          "complete": repaired.capture.complete})
                    require(repaired.material_unchanged, "REPAIR_MATERIAL", "No se acreditó ausencia de trabajo nuevo")
                    if not repaired.capture.complete:
                        continue
                    try:
                        candidate = extract(repaired.capture.text)
                        # Compare serialized structures, avoiding Python bool == int equivalence.
                        require(json.dumps(base, sort_keys=True) == json.dumps(candidate, sort_keys=True),
                                "REPAIR_CHANGED", "La reemisión alteró valores del sobre")
                        obj = candidate
                        break
                    except Fault as repair_error:
                        if repair_error.code in {"REPAIR_CHANGED", "UTF8"}:
                            raise
                require(obj is not None, "REPAIR_EXHAUSTED", "Reemisión no produjo la forma requerida")
            obj = validate(obj, work_id=self.work_id, source_actor=source_actor,
                           source_repo=self.repositories[source_actor], last_turn=self.last_turn)
            self.pending = obj
            if obj["human_need"] is not None or obj["final"]:
                self.last_turn = obj["turn_id"]
                self.mode = "human_need" if obj["human_need"] else "final"
                return {"status": self.mode, "human_need": obj["human_need"], "last_turn": self.last_turn}
            if self.stop_requested and source_actor == "CONSTRUCTOR":
                self.mode = "paused"
                return {"status": "paused", "last_turn": self.last_turn}
            return self._route(adapter)
        except Exception as exc:
            return self._halt(exc)

    def _route(self, adapter: Adapter, directive: str | None = None) -> dict:
        obj = self.pending
        text = obj["next_prompt"]
        if directive is not None:
            require(obj["next_actor"] == "AUDITOR" and obj["next_instance"] == "current",
                    "DIRECTIVE_DESTINATION", "Directiva requiere auditor competente current")
            # JSON string values preserve boundaries even if literals contain delimiter-like text.
            text = json.dumps({"ACTOR_PROMPT_LITERAL": text, "HUMAN_DIRECTIVE_LITERAL": directive}, ensure_ascii=False)
        self._deliver(adapter, obj["next_actor"], obj["next_instance"], text)
        self.last_turn = obj["turn_id"]
        self.expected_actor = obj["next_actor"]
        self.pending = None
        self.mode = "running"
        return {"status": "delivered", "last_turn": self.last_turn, "unit": obj["unit"],
                "readback_available": self.readback_available}

    def continue_(self, adapter: Adapter, directive: str | None = None) -> dict:
        require(self.mode == "paused", "STATE", "No existe pausa ordinaria")
        try:
            self.stop_requested = False
            return self._route(adapter, directive)
        except Exception as exc:
            return self._halt(exc)

    def resolve_human(self, adapter: Adapter, resolution: str) -> dict:
        require(self.mode == "human_need", "STATE", "No existe necesidad humana detenida")
        try:
            require(nonempty(resolution), "RESOLUTION", "Resolución vacía")
            text = json.dumps({"RESUME_CONTEXT": {"INCOMING_TURN_ID": self.pending["turn_id"]},
                               "HUMAN_RESOLUTION_LITERAL": resolution}, ensure_ascii=False)
            self.attempts = {}
            self._deliver(adapter, "AUDITOR", "current", text)
            self.expected_actor = "AUDITOR"
            self.mode = "running"
            self.pending = None
            return {"status": "resumed", "last_turn": self.last_turn}
        except Exception as exc:
            return self._halt(exc)


LOCATOR_KEYS = ["WORK_ID", "CARRIL", "CONSTITUTION_REPO", "CONSTITUTION_PATH", "CONSTITUTION_SHA"]


def parse_locator(text: str) -> tuple[str, dict]:
    if text.startswith("\ufeff"):
        text = text[1:]
    text = text.strip(" \t\r\n")
    require(text.isascii() and "\n" not in text and "\r" not in text, "LOCATOR", "Locator debe ser una línea ASCII")
    parts = text.split("|")
    require(len(parts) == 6 and parts[0] == "METODO_AI_INIT_V1", "LOCATOR", "Forma de locator inválida")
    fields = {}
    for expected, part in zip(LOCATOR_KEYS, parts[1:]):
        key, sep, value = part.partition("=")
        require(sep == "=" and key == expected, "LOCATOR", "Orden/campos inválidos")
        fields[key] = value
    require(matches(ID, fields["WORK_ID"]) and matches(ID, fields["CARRIL"])
            and matches(REPO, fields["CONSTITUTION_REPO"])
            and safe_path(fields["CONSTITUTION_PATH"]) and matches(SHA, fields["CONSTITUTION_SHA"]),
            "LOCATOR", "Coordenadas inválidas")
    return text, fields


def render_init(config: dict) -> str:
    keys = {"work_id", "carril", "method_repo", "method_sha", "constitution_repo", "constitution_path",
            "constitution_sha", "auditor_runtime", "constructor_runtime", "constructor_local_path"}
    require(type(config) is dict and set(config) == keys and all(nonempty(v) for v in config.values()),
            "CONFIG", "Configuración de arranque incompleta")
    require(matches(REPO, config["method_repo"]) and matches(SHA, config["method_sha"]), "CONFIG", "Método inválido")
    require(all("\n" not in v and "\r" not in v for v in config.values()), "CONFIG", "Campo multilínea")
    locator = "METODO_AI_INIT_V1|" + "|".join(f"{key}={config[key.lower()]}" for key in LOCATOR_KEYS)
    parse_locator(locator)
    return ("ARRANQUE DEL ORQUESTADOR — METODO-AI\n\n"
            f"METHOD_REPO={config['method_repo']}\nMETHOD_SHA={config['method_sha']}\n"
            f"AUDITOR_RUNTIME={config['auditor_runtime']}\nCONSTRUCTOR_RUNTIME={config['constructor_runtime']}\n"
            f"CONSTRUCTOR_LOCAL_PATH={config['constructor_local_path']}\n\n"
            "Leé transporte/ORQUESTADOR.md y transporte/ADAPTADORES.md en METHOD_SHA.\n"
            "Usá el núcleo de código de ese commit. No regeneres next_prompt.\n"
            "Abrí auditor realmente nuevo; entregale exclusivamente el locator final.\n"
            "No crees BOOTSTRAP ni escribas work/audit. Esperá su respuesta completa.\n"
            "Validá actor=AUDITOR y turn_id=1; seguí las reglas de transporte y recuperación.\n"
            "Ante falla final mostrá el reporte y la respuesta original completa.\n"
            "El guardado para tres agentes nuevos no está habilitado en esta entrega.\n\n"
            f"ENTREGAR SÓLO ESTA LÍNEA:\n{locator}\n")
