"""Live SAP OData ingress. See requirements §10 — FR-13, FR-14, NFR-9 to NFR-11."""
from __future__ import annotations

import base64
import json
import os
import re
import time
from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from enum import Enum
from typing import Any, Callable, Mapping, Protocol, Sequence

from bwace.engine.config import (
    ODATA_DEFAULT_MAX_RECORDS,
    ODATA_DEFAULT_SERVICE_PATHS,
    ODATA_DEFAULT_SERVICE_ROOT,
    ODATA_DEFAULT_TIMEOUT_SECONDS,
    ODATA_ENV_VARS,
    ODATA_LIVE_DATASETS,
    ODATA_RETRY_ATTEMPTS,
    ODATA_RETRY_BACKOFF_SECONDS,
    ODATA_SERVICE_ENV_VARS,
)
from bwace.engine.loader import LoadOutcome, load_with_live


class Status(Enum):
    OK = "OK"
    UNAUTHORISED = "UNAUTHORISED"
    NOT_FOUND = "NOT_FOUND"
    SERVER_ERROR = "SERVER_ERROR"
    TIMEOUT = "TIMEOUT"
    TLS_ERROR = "TLS_ERROR"
    TRANSPORT_ERROR = "TRANSPORT_ERROR"
    MALFORMED = "MALFORMED"
    NOT_CONFIGURED = "NOT_CONFIGURED"


RETRYABLE = frozenset({Status.TIMEOUT, Status.SERVER_ERROR, Status.TRANSPORT_ERROR})

_SECRET_PLACEHOLDER = "***"
_USERINFO = re.compile(r"//[^/@\s]*@")


# ---- Settings ----------------------------------------------------


@dataclass(frozen=True)
class OdataSettings:
    """Resolved connection configuration. Deliberately holds no credentials (NFR-9.2)."""

    base_url: str = ""
    service_root: str = ODATA_DEFAULT_SERVICE_ROOT
    service_paths: Mapping[str, str] = field(default_factory=lambda: dict(ODATA_DEFAULT_SERVICE_PATHS))
    timeout_seconds: float = ODATA_DEFAULT_TIMEOUT_SECONDS
    max_records: int = ODATA_DEFAULT_MAX_RECORDS
    ca_bundle: str | None = None
    user_set: bool = False
    password_set: bool = False

    @classmethod
    def from_env(cls, env: Mapping[str, str] | None = None) -> "OdataSettings":
        env = os.environ if env is None else env
        paths = {
            dataset: env.get(var, ODATA_DEFAULT_SERVICE_PATHS[dataset]).strip("/")
            for dataset, var in ODATA_SERVICE_ENV_VARS.items()
        }
        return cls(
            base_url=env.get(ODATA_ENV_VARS["base_url"], "").rstrip("/"),
            service_root=env.get(ODATA_ENV_VARS["service_root"], ODATA_DEFAULT_SERVICE_ROOT).strip("/"),
            service_paths=paths,
            timeout_seconds=_float_or(env.get(ODATA_ENV_VARS["timeout"]), ODATA_DEFAULT_TIMEOUT_SECONDS),
            max_records=_int_or(env.get(ODATA_ENV_VARS["max_records"]), ODATA_DEFAULT_MAX_RECORDS),
            ca_bundle=env.get(ODATA_ENV_VARS["ca_bundle"]) or None,
            user_set=bool(env.get(ODATA_ENV_VARS["user"])),
            password_set=bool(env.get(ODATA_ENV_VARS["password"])),
        )

    @property
    def is_configured(self) -> bool:
        return bool(self.base_url) and self.user_set and self.password_set

    @property
    def host(self) -> str:
        stripped = _USERINFO.sub("//", self.base_url)
        return stripped.split("//", 1)[-1].split("/", 1)[0] or stripped

    def collection_url(self, dataset: str) -> str:
        return f"{self.base_url}/{self.service_root}/{self.service_paths[dataset]}"

    def metadata_url(self, dataset: str) -> str:
        service = self.service_paths[dataset].rsplit("/", 1)[0]
        return f"{self.base_url}/{self.service_root}/{service}/$metadata"

    def missing_configuration(self) -> tuple[str, ...]:
        missing = []
        if not self.base_url:
            missing.append(ODATA_ENV_VARS["base_url"])
        if not self.user_set:
            missing.append(ODATA_ENV_VARS["user"])
        if not self.password_set:
            missing.append(ODATA_ENV_VARS["password"])
        return tuple(missing)


def load_env_file(path: str = ".env", env: dict[str, str] | None = None) -> tuple[str, ...]:
    """NFR-9.1. Minimal KEY=VALUE reader; existing environment always wins. No new dependency."""
    target = os.environ if env is None else env
    try:
        with open(path, "r", encoding="utf-8") as handle:
            lines = handle.readlines()
    except OSError:
        return ()
    loaded: list[str] = []
    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, _, value = stripped.partition("=")
        key, value = key.strip(), value.strip().strip("'\"")
        if key and key not in target:
            target[key] = value
            loaded.append(key)
    return tuple(loaded)


def _float_or(raw: str | None, fallback: float) -> float:
    try:
        return float(raw) if raw else fallback
    except ValueError:
        return fallback


def _int_or(raw: str | None, fallback: int) -> int:
    try:
        return int(raw) if raw else fallback
    except ValueError:
        return fallback


# ---- Transport ----------------------------------------------------


@dataclass(frozen=True)
class HttpResponse:
    status_code: int
    body: bytes
    url: str


class TransportFailure(Exception):
    def __init__(self, status: Status, detail: str) -> None:
        super().__init__(detail)
        self.status = status
        self.detail = detail


class Transport(Protocol):
    def get(self, url: str, headers: Mapping[str, str]) -> HttpResponse: ...


class AuthStrategy(Protocol):
    def headers(self) -> dict[str, str]: ...


@dataclass(frozen=True)
class BasicAuth:
    """FR-13.7. OAuth arrives as a second AuthStrategy, not as a change to the fetch layer."""

    user: str
    password: str

    def headers(self) -> dict[str, str]:
        token = base64.b64encode(f"{self.user}:{self.password}".encode("utf-8")).decode("ascii")
        return {"Authorization": f"Basic {token}"}

    def __repr__(self) -> str:  # NFR-9.3 - must not leak through a traceback or a log line
        return f"BasicAuth(user={_SECRET_PLACEHOLDER!r}, password={_SECRET_PLACEHOLDER!r})"


def basic_auth_from_env(env: Mapping[str, str] | None = None) -> BasicAuth | None:
    env = os.environ if env is None else env
    user = env.get(ODATA_ENV_VARS["user"])
    password = env.get(ODATA_ENV_VARS["password"])
    if not user or not password:
        return None
    return BasicAuth(user=user, password=password)


def secret_values(env: Mapping[str, str] | None = None) -> tuple[str, ...]:
    env = os.environ if env is None else env
    return tuple(v for v in (env.get(ODATA_ENV_VARS["password"]), env.get(ODATA_ENV_VARS["user"])) if v)


def scrub(text: str, secrets: Sequence[str] = ()) -> str:
    """NFR-9.3. Strip URL userinfo and any known secret value from anything user-visible."""
    cleaned = _USERINFO.sub(f"//{_SECRET_PLACEHOLDER}@", text)
    for secret in secrets:
        if secret:
            cleaned = cleaned.replace(secret, _SECRET_PLACEHOLDER)
    return cleaned


class HttpxTransport:
    """Real transport. httpx is imported lazily so demo mode never needs it (NFR-10.2)."""

    def __init__(
        self,
        auth: AuthStrategy,
        timeout_seconds: float = ODATA_DEFAULT_TIMEOUT_SECONDS,
        ca_bundle: str | None = None,
        secrets: Sequence[str] = (),
    ) -> None:
        self._auth = auth
        self._timeout = timeout_seconds
        self._verify: Any = ca_bundle if ca_bundle else True  # NFR-9.4 - never False
        self._secrets = tuple(secrets)

    def get(self, url: str, headers: Mapping[str, str]) -> HttpResponse:
        try:
            import httpx
        except ImportError as exc:
            raise TransportFailure(
                Status.TRANSPORT_ERROR,
                "The httpx package is not installed, so live OData mode is unavailable.",
            ) from exc

        merged = {**self._auth.headers(), **headers}
        try:
            with httpx.Client(timeout=self._timeout, verify=self._verify, follow_redirects=True) as client:
                response = client.get(url, headers=merged)
        except httpx.TimeoutException as exc:
            raise TransportFailure(Status.TIMEOUT, self._detail("Request timed out", exc)) from exc
        except httpx.ConnectError as exc:
            detail = self._detail("Could not connect", exc)
            status = Status.TLS_ERROR if _looks_like_tls(str(exc)) else Status.TRANSPORT_ERROR
            raise TransportFailure(status, detail) from exc
        except httpx.HTTPError as exc:
            raise TransportFailure(Status.TRANSPORT_ERROR, self._detail("Request failed", exc)) from exc
        return HttpResponse(status_code=response.status_code, body=response.content, url=url)

    def _detail(self, prefix: str, exc: Exception) -> str:
        return scrub(f"{prefix}: {type(exc).__name__}: {exc}", self._secrets)


def _looks_like_tls(message: str) -> bool:
    lowered = message.lower()
    return "certificate" in lowered or "ssl" in lowered or "tls" in lowered


@dataclass(frozen=True)
class RetryPolicy:
    attempts: int = ODATA_RETRY_ATTEMPTS
    backoff_seconds: float = ODATA_RETRY_BACKOFF_SECONDS
    sleep: Callable[[float], None] = time.sleep


JSON_HEADERS = {"Accept": "application/json"}
METADATA_HEADERS = {"Accept": "application/xml"}


def _status_for(code: int) -> Status:
    if code in (401, 403):
        return Status.UNAUTHORISED
    if code == 404:
        return Status.NOT_FOUND
    if code >= 500:
        return Status.SERVER_ERROR
    if code >= 400:
        return Status.TRANSPORT_ERROR
    return Status.OK


def request(
    transport: Transport,
    url: str,
    headers: Mapping[str, str],
    retry: RetryPolicy | None = None,
) -> HttpResponse:
    """FR-14.10. Retries transient failures only; auth and not-found are terminal."""
    retry = retry or RetryPolicy()
    last: TransportFailure | None = None
    for attempt in range(max(1, retry.attempts)):
        try:
            response = transport.get(url, headers)
        except TransportFailure as failure:
            last = failure
            if failure.status not in RETRYABLE:
                raise
        else:
            status = _status_for(response.status_code)
            if status is Status.OK:
                return response
            last = TransportFailure(status, f"HTTP {response.status_code} from {scrub(url)}")
            if status not in RETRYABLE:
                raise last
        if attempt < retry.attempts - 1:
            retry.sleep(retry.backoff_seconds * (2 ** attempt))
    raise last if last is not None else TransportFailure(Status.TRANSPORT_ERROR, "No attempt was made.")


# ---- Collection retrieval ----------------------------------------------------


@dataclass(frozen=True)
class CollectionPage:
    records: list[dict]
    next_url: str | None


def parse_page(payload: bytes) -> CollectionPage:
    try:
        body = json.loads(payload.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise TransportFailure(Status.MALFORMED, f"Response body is not valid JSON: {exc}") from exc

    if isinstance(body, list):
        return CollectionPage(records=[r for r in body if isinstance(r, dict)], next_url=None)
    if not isinstance(body, dict):
        raise TransportFailure(Status.MALFORMED, "Response body is neither a JSON object nor an array.")

    envelope = body.get("d", body)
    if isinstance(envelope, dict):
        records = envelope.get("results", envelope.get("value"))
        next_url = envelope.get("__next") or body.get("@odata.nextLink")
    else:
        records, next_url = envelope, None

    if records is None:
        raise TransportFailure(
            Status.MALFORMED,
            "Response contains no record collection (expected 'd.results' or 'value').",
        )
    if not isinstance(records, list):
        raise TransportFailure(Status.MALFORMED, "Record collection is not a JSON array.")
    return CollectionPage(
        records=[r for r in records if isinstance(r, dict)],
        next_url=next_url if isinstance(next_url, str) else None,
    )


@dataclass(frozen=True)
class CollectionResult:
    records: list[dict]
    truncated: bool
    pages: int


def fetch_collection(
    transport: Transport,
    url: str,
    max_records: int = ODATA_DEFAULT_MAX_RECORDS,
    retry: RetryPolicy | None = None,
) -> CollectionResult:
    """FR-14.4 / FR-14.5. Paging is a correctness requirement: an unpaged GET truncates silently."""
    records: list[dict] = []
    pages = 0
    next_url: str | None = f"{url}?$format=json" if "?" not in url else url
    while next_url:
        response = request(transport, next_url, JSON_HEADERS, retry)
        page = parse_page(response.body)
        pages += 1
        records.extend(page.records)
        if len(records) >= max_records:
            return CollectionResult(records=records[:max_records], truncated=True, pages=pages)
        next_url = page.next_url
    return CollectionResult(records=records, truncated=False, pages=pages)


# ---- Mapping ----------------------------------------------------

_V2_DATE = re.compile(r"^/Date\((-?\d+)([+-]\d+)?\)/$")


class MappingError(Exception):
    pass


def _to_str(value: Any) -> str:
    return "" if value is None else str(value)


def _to_int(value: Any) -> int:
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, (int, float)):
        return int(value)
    text = _to_str(value).strip().replace(",", "")
    if not text:
        return 0
    try:
        return int(float(text))
    except ValueError as exc:
        raise MappingError(f"Expected a number, got {value!r}.") from exc


def _to_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    return _to_str(value).strip().lower() in {"true", "x", "yes", "y", "1"}


def _to_date_iso(value: Any) -> str:
    """SAP OData V2 emits /Date(ms)/; V4 and CDS emit ISO-8601. Both normalise to ISO."""
    if isinstance(value, date):
        return value.isoformat()
    text = _to_str(value).strip()
    match = _V2_DATE.match(text)
    if match:
        millis = int(match.group(1))
        return datetime.fromtimestamp(millis / 1000, tz=timezone.utc).date().isoformat()
    return text.split("T", 1)[0]


@dataclass(frozen=True)
class FieldMap:
    source: str
    target: str
    coerce: Callable[[Any], Any]


OBJECT_INVENTORY_FIELDS: tuple[FieldMap, ...] = (
    FieldMap("ObjectId", "object_id", _to_str),
    FieldMap("ObjectType", "object_type", _to_str),
    FieldMap("SolutionArea", "solution_area", _to_str),
    FieldMap("Description", "description", _to_str),
    FieldMap("DataVolumeLabel", "data_volume_label", _to_str),
    FieldMap("HanaCvCount", "hana_cv_count", _to_int),
    FieldMap("AdsoCount", "adso_count", _to_int),
    FieldMap("CustomTableCount", "custom_table_count", _to_int),
)

USAGE_FIELDS: tuple[FieldMap, ...] = (
    FieldMap("ObjectId", "object_id", _to_str),
    FieldMap("LastRunDate", "last_run_date", _to_date_iso),
    FieldMap("MonthlyExecutions", "monthly_executions", _to_int),
    FieldMap("DistinctUsers", "distinct_users", _to_int),
    FieldMap("BusinessOwner", "business_owner", _to_str),
)

VOLUME_FIELDS: tuple[FieldMap, ...] = (
    FieldMap("ObjectId", "object_id", _to_str),
    FieldMap("RecordCount", "record_count", _to_int),
    FieldMap("StorageGb", "storage_gb", _to_int),
    FieldMap("LoadFrequency", "load_frequency", _to_str),
)

COMPLEXITY_FIELDS: tuple[FieldMap, ...] = (
    FieldMap("ObjectId", "object_id", _to_str),
    FieldMap("HanaCvCount", "hana_cv_count", _to_int),
    FieldMap("TransformationCount", "transformation_count", _to_int),
    FieldMap("CustomLogicPresent", "custom_logic_present", _to_bool),
    FieldMap("InterfaceCount", "interface_count", _to_int),
)

DEPENDENCY_FIELDS: tuple[FieldMap, ...] = (
    FieldMap("SourceNodeId", "source", _to_str),
    FieldMap("SourceLabel", "source_label", _to_str),
    FieldMap("SourceNodeType", "source_node_type", _to_str),
    FieldMap("TargetNodeId", "target", _to_str),
    FieldMap("TargetLabel", "target_label", _to_str),
    FieldMap("TargetNodeType", "target_node_type", _to_str),
    FieldMap("EdgeType", "edge_type", _to_str),
    FieldMap("Description", "description", _to_str),
)

FIELD_MAPS: dict[str, tuple[FieldMap, ...]] = {
    "object_inventory": OBJECT_INVENTORY_FIELDS,
    "usage_logs": USAGE_FIELDS,
    "data_volume": VOLUME_FIELDS,
    "complexity": COMPLEXITY_FIELDS,
    "dependencies": DEPENDENCY_FIELDS,
}


def _lookup(record: Mapping[str, Any], mapping: FieldMap) -> Any:
    # Accept the SAP property name or the BW-ACE field name, so a service that
    # already speaks our vocabulary needs no per-site remapping.
    for key in (mapping.source, mapping.target):
        if key in record:
            return record[key]
    return None


def map_records(dataset: str, records: Sequence[Mapping[str, Any]]) -> list[dict]:
    fields = FIELD_MAPS[dataset]
    mapped: list[dict] = []
    for record in records:
        row: dict[str, Any] = {}
        for mapping in fields:
            raw = _lookup(record, mapping)
            if raw is None:
                continue
            row[mapping.target] = mapping.coerce(raw)
        mapped.append(row)
    return mapped


_NODE_TYPES = frozenset({"SOLUTION_AREA", "EXTERNAL", "CONSTRAINT", "SHARED_OBJECT", "SOURCE"})


def build_dependency_payload(rows: Sequence[Mapping[str, Any]]) -> dict:
    """Flatten edge rows into the nodes/edges document the loader validates."""
    nodes: dict[str, dict] = {}
    edges: list[dict] = []
    for row in rows:
        for prefix in ("source", "target"):
            node_id = _to_str(row.get(prefix))
            if not node_id or node_id == "ALL":
                continue
            node_type = _to_str(row.get(f"{prefix}_node_type")).upper() or "SOLUTION_AREA"
            if node_type not in _NODE_TYPES:
                node_type = "SOLUTION_AREA"
            nodes.setdefault(node_id, {
                "node_id": node_id,
                "label": _to_str(row.get(f"{prefix}_label")) or node_id,
                "node_type": node_type,
            })
        source, target = _to_str(row.get("source")), _to_str(row.get("target"))
        if not source or not target:
            continue
        edge = {
            "source": source,
            "target": target,
            "edge_type": _to_str(row.get("edge_type")).upper() or "LOGICAL",
        }
        description = _to_str(row.get("description"))
        if description:
            edge["description"] = description
        edges.append(edge)
    return {"nodes": list(nodes.values()), "edges": edges}


def dataset_payload(dataset: str, records: Sequence[Mapping[str, Any]]) -> bytes:
    mapped = map_records(dataset, records)
    document: Any = build_dependency_payload(mapped) if dataset == "dependencies" else mapped
    return json.dumps(document).encode("utf-8")


# ---- Orchestration ----------------------------------------------------


@dataclass(frozen=True)
class EndpointResult:
    dataset: str
    url: str
    status: Status
    detail: str = ""
    record_count: int = 0
    truncated: bool = False

    @property
    def ok(self) -> bool:
        return self.status is Status.OK


@dataclass(frozen=True)
class LiveFetchOutcome:
    """FR-14.6. `load` is populated only when every live dataset arrived intact."""

    load: LoadOutcome | None
    endpoints: tuple[EndpointResult, ...]
    fetched_at: datetime | None = None
    payloads: Mapping[str, bytes] = field(default_factory=dict)

    @property
    def ok(self) -> bool:
        return self.load is not None and self.load.landscape is not None

    @property
    def failures(self) -> tuple[EndpointResult, ...]:
        return tuple(e for e in self.endpoints if not e.ok)

    @property
    def warnings(self) -> tuple[str, ...]:
        return tuple(
            f"{e.dataset}: retrieval stopped at the {e.record_count}-record cap; "
            "the landscape may be incomplete. Raise BWACE_ODATA_MAX_RECORDS."
            for e in self.endpoints if e.truncated
        )


def _tls_hint(detail: str) -> str:
    return (
        f"{detail} Set {ODATA_ENV_VARS['ca_bundle']} to a CA bundle that trusts the SAP host. "
        "Certificate verification cannot be disabled (NFR-9.4)."
    )


def _failure_result(dataset: str, url: str, failure: TransportFailure, secrets: Sequence[str]) -> EndpointResult:
    detail = scrub(failure.detail, secrets)
    if failure.status is Status.TLS_ERROR:
        detail = _tls_hint(detail)
    return EndpointResult(dataset=dataset, url=scrub(url), status=failure.status, detail=detail)


def test_connection(
    settings: OdataSettings,
    transport: Transport,
    retry: RetryPolicy | None = None,
    secrets: Sequence[str] = (),
) -> tuple[EndpointResult, ...]:
    """FR-13.5. One $metadata probe per configured service."""
    results: list[EndpointResult] = []
    for dataset in ODATA_LIVE_DATASETS:
        url = settings.metadata_url(dataset)
        try:
            response = request(transport, url, METADATA_HEADERS, retry)
        except TransportFailure as failure:
            results.append(_failure_result(dataset, url, failure, secrets))
            continue
        results.append(EndpointResult(
            dataset=dataset, url=scrub(url), status=Status.OK,
            detail=f"Reachable and authenticated ({len(response.body)} bytes of metadata).",
        ))
    return tuple(results)


def fetch_landscape(
    settings: OdataSettings,
    transport: Transport,
    uploads: Mapping[str, bytes] | None = None,
    retry: RetryPolicy | None = None,
    secrets: Sequence[str] = (),
    now: Callable[[], datetime] | None = None,
) -> LiveFetchOutcome:
    """FR-14.1 to FR-14.6. All five live datasets, or nothing."""
    missing = settings.missing_configuration()
    if missing:
        detail = "Not configured. Missing: " + ", ".join(missing)
        return LiveFetchOutcome(
            load=None,
            endpoints=tuple(
                EndpointResult(dataset=d, url="", status=Status.NOT_CONFIGURED, detail=detail)
                for d in ODATA_LIVE_DATASETS
            ),
        )

    results: list[EndpointResult] = []
    payloads: dict[str, bytes] = {}
    for dataset in ODATA_LIVE_DATASETS:
        url = settings.collection_url(dataset)
        try:
            collection = fetch_collection(transport, url, settings.max_records, retry)
            payloads[dataset] = dataset_payload(dataset, collection.records)
        except TransportFailure as failure:
            results.append(_failure_result(dataset, url, failure, secrets))
            continue
        except MappingError as exc:
            results.append(EndpointResult(
                dataset=dataset, url=scrub(url), status=Status.MALFORMED,
                detail=scrub(f"Field mapping failed: {exc}", secrets),
            ))
            continue
        results.append(EndpointResult(
            dataset=dataset, url=scrub(url), status=Status.OK,
            detail=f"{len(collection.records)} records over {collection.pages} page(s).",
            record_count=len(collection.records) if not collection.truncated else settings.max_records,
            truncated=collection.truncated,
        ))

    endpoints = tuple(results)
    if any(not r.ok for r in endpoints):
        return LiveFetchOutcome(load=None, endpoints=endpoints)

    outcome = load_with_live(payloads, dict(uploads or {}))
    if outcome.landscape is None:
        return LiveFetchOutcome(load=outcome, endpoints=endpoints)

    clock = now or (lambda: datetime.now(tz=timezone.utc))
    return LiveFetchOutcome(load=outcome, endpoints=endpoints, fetched_at=clock(), payloads=payloads)


def transport_from_env(settings: OdataSettings, env: Mapping[str, str] | None = None) -> HttpxTransport | None:
    """Credentials are read here and held only for the life of the transport (NFR-9.1, NFR-9.2)."""
    auth = basic_auth_from_env(env)
    if auth is None:
        return None
    return HttpxTransport(
        auth=auth,
        timeout_seconds=settings.timeout_seconds,
        ca_bundle=settings.ca_bundle,
        secrets=secret_values(env),
    )
