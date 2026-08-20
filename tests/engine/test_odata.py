"""Connector tests against a stubbed transport. No network is touched (NFR-11.1 to NFR-11.3)."""
import json
from datetime import date

import pytest

from bwace.engine import odata
from bwace.engine.loader import DATA_DIR, DATASET_FILES
from bwace.engine.odata import (
    BasicAuth,
    HttpResponse,
    MappingError,
    OdataSettings,
    RetryPolicy,
    Status,
    TransportFailure,
)

NO_SLEEP = RetryPolicy(attempts=3, backoff_seconds=0.0, sleep=lambda _s: None)
ONE_SHOT = RetryPolicy(attempts=1, backoff_seconds=0.0, sleep=lambda _s: None)

ENV = {
    "BWACE_ODATA_BASE_URL": "https://sapgw.example.test:44300",
    "BWACE_ODATA_USER": "bwace_reader",
    "BWACE_ODATA_PASSWORD": "s3cr3t-value",
}


def settings(**overrides) -> OdataSettings:
    env = {**ENV, **overrides}
    return OdataSettings.from_env(env)


class StubTransport:
    """Scripted responses keyed by substring of the requested URL."""

    def __init__(self, script):
        self.script = script
        self.calls: list[str] = []

    def get(self, url, headers):
        self.calls.append(url)
        for fragment, outcome in self.script:
            if fragment in url:
                if isinstance(outcome, list):
                    result = outcome.pop(0) if len(outcome) > 1 else outcome[0]
                else:
                    result = outcome
                if isinstance(result, BaseException):
                    raise result
                if isinstance(result, int):
                    return HttpResponse(status_code=result, body=b"", url=url)
                if isinstance(result, bytes):
                    return HttpResponse(status_code=200, body=result, url=url)
                return HttpResponse(status_code=200, body=json.dumps(result).encode(), url=url)
        raise AssertionError(f"No stub matched {url}")


def v2(records, next_url=None):
    payload = {"d": {"results": records}}
    if next_url:
        payload["d"]["__next"] = next_url
    return payload


# ---- Settings and URL construction ----------------------------------------


def test_settings_from_env_reports_presence_not_values():
    s = settings()
    assert s.user_set and s.password_set
    assert "s3cr3t-value" not in repr(s)
    assert s.host == "sapgw.example.test:44300"


def test_settings_missing_configuration_lists_gaps():
    s = OdataSettings.from_env({})
    assert s.is_configured is False
    assert s.missing_configuration() == (
        "BWACE_ODATA_BASE_URL", "BWACE_ODATA_USER", "BWACE_ODATA_PASSWORD",
    )


def test_collection_and_metadata_urls_use_defaults():
    s = settings()
    assert s.collection_url("object_inventory") == (
        "https://sapgw.example.test:44300/sap/opu/odata/sap/RSOD_CATALOG_SRV/ObjectCatalog"
    )
    assert s.metadata_url("object_inventory").endswith("RSOD_CATALOG_SRV/$metadata")


def test_service_path_override_is_honoured():
    s = settings(BWACE_ODATA_SERVICE_INVENTORY="ZCUSTOM_SRV/Objects")
    assert s.collection_url("object_inventory").endswith("ZCUSTOM_SRV/Objects")


def test_criticality_is_not_a_live_dataset():
    assert "criticality" not in odata.ODATA_LIVE_DATASETS
    assert len(odata.ODATA_LIVE_DATASETS) == 5


# ---- Secret handling (NFR-9.2, NFR-9.3) ----------------------------------


def test_basic_auth_repr_masks_credentials():
    auth = BasicAuth(user="bwace_reader", password="s3cr3t-value")
    assert "s3cr3t-value" not in repr(auth)
    assert "bwace_reader" not in repr(auth)
    assert auth.headers()["Authorization"].startswith("Basic ")


def test_scrub_removes_url_userinfo_and_secrets():
    text = "Failed on https://user:p4ss@host/path with password p4ss"
    cleaned = odata.scrub(text, ("p4ss",))
    assert "p4ss" not in cleaned
    assert "user:" not in cleaned


def test_failure_detail_never_contains_the_password():
    transport = StubTransport([("", TransportFailure(
        Status.TRANSPORT_ERROR, "Request failed for user bwace_reader with s3cr3t-value"))])
    outcome = odata.fetch_landscape(
        settings(), transport, retry=ONE_SHOT, secrets=("s3cr3t-value", "bwace_reader"),
    )
    assert not outcome.ok
    assert all("s3cr3t-value" not in e.detail for e in outcome.endpoints)


def test_ca_bundle_is_the_only_tls_lever():
    transport = odata.HttpxTransport(auth=BasicAuth("u", "p"), ca_bundle=None)
    assert transport._verify is True
    with_bundle = odata.HttpxTransport(auth=BasicAuth("u", "p"), ca_bundle="/etc/ssl/corp.pem")
    assert with_bundle._verify == "/etc/ssl/corp.pem"


# ---- Paging, caps and retries (FR-14.4, FR-14.5, FR-14.10) ---------------


def test_single_page_collection():
    transport = StubTransport([("Objects", v2([{"ObjectId": "A"}, {"ObjectId": "B"}]))])
    result = odata.fetch_collection(transport, "https://h/Objects", retry=ONE_SHOT)
    assert len(result.records) == 2
    assert result.pages == 1
    assert result.truncated is False


def test_paged_collection_follows_next_link():
    page_two = "https://h/Objects?$skiptoken=2"
    transport = StubTransport([
        ("$skiptoken=2", v2([{"ObjectId": "C"}])),
        ("Objects", v2([{"ObjectId": "A"}, {"ObjectId": "B"}], next_url=page_two)),
    ])
    result = odata.fetch_collection(transport, "https://h/Objects", retry=ONE_SHOT)
    assert [r["ObjectId"] for r in result.records] == ["A", "B", "C"]
    assert result.pages == 2


def test_record_cap_truncates_and_flags():
    transport = StubTransport([("Objects", v2([{"ObjectId": str(i)} for i in range(10)]))])
    result = odata.fetch_collection(transport, "https://h/Objects", max_records=4, retry=ONE_SHOT)
    assert len(result.records) == 4
    assert result.truncated is True


def test_unauthorised_is_not_retried():
    transport = StubTransport([("Objects", 401)])
    with pytest.raises(TransportFailure) as exc:
        odata.fetch_collection(transport, "https://h/Objects", retry=NO_SLEEP)
    assert exc.value.status is Status.UNAUTHORISED
    assert len(transport.calls) == 1


def test_not_found_is_not_retried():
    transport = StubTransport([("Objects", 404)])
    with pytest.raises(TransportFailure) as exc:
        odata.fetch_collection(transport, "https://h/Objects", retry=NO_SLEEP)
    assert exc.value.status is Status.NOT_FOUND
    assert len(transport.calls) == 1


def test_server_error_then_success_is_retried():
    transport = StubTransport([("Objects", [500, v2([{"ObjectId": "A"}])])])
    result = odata.fetch_collection(transport, "https://h/Objects", retry=NO_SLEEP)
    assert len(result.records) == 1
    assert len(transport.calls) == 2


def test_timeout_exhausts_attempts_then_fails():
    transport = StubTransport([("Objects", TransportFailure(Status.TIMEOUT, "Request timed out"))])
    with pytest.raises(TransportFailure) as exc:
        odata.fetch_collection(transport, "https://h/Objects", retry=NO_SLEEP)
    assert exc.value.status is Status.TIMEOUT
    assert len(transport.calls) == 3


def test_malformed_body_is_reported_as_malformed():
    transport = StubTransport([("Objects", b"<html>not json</html>")])
    with pytest.raises(TransportFailure) as exc:
        odata.fetch_collection(transport, "https://h/Objects", retry=ONE_SHOT)
    assert exc.value.status is Status.MALFORMED


def test_payload_without_a_collection_is_malformed():
    transport = StubTransport([("Objects", {"d": {"unexpected": 1}})])
    with pytest.raises(TransportFailure) as exc:
        odata.fetch_collection(transport, "https://h/Objects", retry=ONE_SHOT)
    assert exc.value.status is Status.MALFORMED


def test_v4_style_payload_is_also_accepted():
    page = odata.parse_page(json.dumps({"value": [{"ObjectId": "A"}]}).encode())
    assert len(page.records) == 1
    assert page.next_url is None


# ---- Mapping (FR-14.3) ----------------------------------------------------


def test_map_records_renames_and_coerces():
    rows = odata.map_records("complexity", [{
        "ObjectId": "FI100", "HanaCvCount": "3", "TransformationCount": 4,
        "CustomLogicPresent": "X", "InterfaceCount": "0",
    }])
    assert rows == [{
        "object_id": "FI100", "hana_cv_count": 3, "transformation_count": 4,
        "custom_logic_present": True, "interface_count": 0,
    }]


def test_map_records_accepts_native_field_names():
    rows = odata.map_records("data_volume", [{
        "object_id": "FI100", "record_count": 10, "storage_gb": 2, "load_frequency": "Daily",
    }])
    assert rows[0]["object_id"] == "FI100"


def test_sap_v2_date_format_is_normalised():
    rows = odata.map_records("usage_logs", [{
        "ObjectId": "FI100", "LastRunDate": "/Date(1755561600000)/",
        "MonthlyExecutions": 5, "DistinctUsers": 2, "BusinessOwner": "Owner",
    }])
    assert date.fromisoformat(rows[0]["last_run_date"]).year == 2025


def test_iso_date_with_time_is_truncated_to_the_day():
    rows = odata.map_records("usage_logs", [{
        "ObjectId": "X", "LastRunDate": "2026-08-07T10:15:00", "MonthlyExecutions": 1,
        "DistinctUsers": 1, "BusinessOwner": "O",
    }])
    assert rows[0]["last_run_date"] == "2026-08-07"


def test_non_numeric_value_raises_mapping_error():
    with pytest.raises(MappingError):
        odata.map_records("data_volume", [{"ObjectId": "X", "RecordCount": "many"}])


def test_dependency_rows_become_nodes_and_edges():
    payload = odata.build_dependency_payload([{
        "source": "FI", "source_label": "Finance", "source_node_type": "SOLUTION_AREA",
        "target": "DMK", "target_label": "Data Mesh", "target_node_type": "EXTERNAL",
        "edge_type": "LOGICAL", "description": "feeds",
    }])
    assert {n["node_id"] for n in payload["nodes"]} == {"FI", "DMK"}
    assert payload["edges"][0] == {
        "source": "FI", "target": "DMK", "edge_type": "LOGICAL", "description": "feeds",
    }


def test_unknown_node_type_falls_back_to_solution_area():
    payload = odata.build_dependency_payload([
        {"source": "FI", "target": "SD", "source_node_type": "MYSTERY", "edge_type": "LOGICAL"},
    ])
    types = {n["node_id"]: n["node_type"] for n in payload["nodes"]}
    assert types["FI"] == "SOLUTION_AREA"


# ---- Connection test (FR-13.5) ------------------------------------------


def test_connection_test_reports_per_endpoint():
    transport = StubTransport([
        ("RSOD_CATALOG_SRV", b"<edmx/>"),
        ("RSOD_ADSO_SRV", b"<edmx/>"),
        ("RSPC_API_SRV", 404),
        ("RSOD_USAGE_SRV", 401),
    ])
    results = odata.test_connection(settings(), transport, retry=ONE_SHOT)
    by_dataset = {r.dataset: r.status for r in results}
    assert by_dataset["object_inventory"] is Status.OK
    assert by_dataset["dependencies"] is Status.NOT_FOUND
    assert by_dataset["usage_logs"] is Status.UNAUTHORISED
    assert len(results) == 5


def test_tls_failure_names_the_ca_bundle_variable():
    transport = StubTransport([
        ("", TransportFailure(Status.TLS_ERROR, "Could not connect: certificate verify failed")),
    ])
    results = odata.test_connection(settings(), transport, retry=ONE_SHOT)
    assert all("BWACE_ODATA_CA_BUNDLE" in r.detail for r in results)


# ---- Full fetch (FR-14.1, FR-14.6) --------------------------------------


def _bundled(name: str):
    return json.loads((DATA_DIR / DATASET_FILES[name]).read_text(encoding="utf-8"))


def _dependency_rows():
    doc = _bundled("dependencies")
    labels = {n["node_id"]: n for n in doc["nodes"]}
    rows = []
    for edge in doc["edges"]:
        if edge["source"] == "ALL":
            continue
        src, tgt = labels[edge["source"]], labels[edge["target"]]
        rows.append({
            "SourceNodeId": src["node_id"], "SourceLabel": src["label"],
            "SourceNodeType": src["node_type"], "TargetNodeId": tgt["node_id"],
            "TargetLabel": tgt["label"], "TargetNodeType": tgt["node_type"],
            "EdgeType": edge["edge_type"], "Description": edge.get("description", ""),
        })
    return rows


def _full_script():
    def to_sap(records, mapping):
        reverse = {m.target: m.source for m in mapping}
        return [{reverse[k]: v for k, v in r.items() if k in reverse} for r in records]

    return [
        ("ObjectCatalog", v2(to_sap(_bundled("object_inventory"), odata.OBJECT_INVENTORY_FIELDS))),
        ("AdsoMetadata", v2(to_sap(_bundled("complexity"), odata.COMPLEXITY_FIELDS))),
        ("AdsoVolume", v2(to_sap(_bundled("data_volume"), odata.VOLUME_FIELDS))),
        ("ProcessChains", v2(_dependency_rows())),
        ("Results", v2(to_sap(_bundled("usage_logs"), odata.USAGE_FIELDS))),
    ]


def test_full_fetch_assembles_a_valid_landscape():
    transport = StubTransport(_full_script())
    outcome = odata.fetch_landscape(settings(), transport, retry=ONE_SHOT)
    assert outcome.ok, [e.detail for e in outcome.failures]
    landscape = outcome.load.landscape
    assert len(landscape.objects) == 22
    assert outcome.fetched_at is not None


def test_live_provenance_is_recorded_and_criticality_stays_local():
    transport = StubTransport(_full_script())
    outcome = odata.fetch_landscape(settings(), transport, retry=ONE_SHOT)
    sources = outcome.load.landscape.sources
    assert sources["object_inventory"] == "live"
    assert sources["usage_logs"] == "live"
    assert sources["criticality"] == "bundled"


def test_live_fetch_reuses_the_existing_validators():
    script = _full_script()
    script[0] = ("ObjectCatalog", v2([{"ObjectId": "ONLY", "ObjectType": "Query"}]))
    outcome = odata.fetch_landscape(settings(), StubTransport(script), retry=ONE_SHOT)
    assert not outcome.ok
    assert outcome.load is not None and outcome.load.report.is_fatal


def test_one_failed_endpoint_yields_no_landscape_at_all():
    script = _full_script()
    script[3] = ("ProcessChains", 500)
    outcome = odata.fetch_landscape(settings(), StubTransport(script), retry=ONE_SHOT)
    assert outcome.load is None
    assert [f.dataset for f in outcome.failures] == ["dependencies"]


def test_unconfigured_fetch_is_reported_not_attempted():
    transport = StubTransport([])
    outcome = odata.fetch_landscape(OdataSettings.from_env({}), transport, retry=ONE_SHOT)
    assert outcome.load is None
    assert all(e.status is Status.NOT_CONFIGURED for e in outcome.endpoints)
    assert transport.calls == []


def test_truncation_surfaces_as_a_warning():
    transport = StubTransport(_full_script())
    outcome = odata.fetch_landscape(settings(BWACE_ODATA_MAX_RECORDS="3"), transport, retry=ONE_SHOT)
    assert outcome.load is None or outcome.warnings
    assert any("cap" in w for w in outcome.warnings)


def test_transport_from_env_returns_none_without_credentials():
    assert odata.transport_from_env(OdataSettings.from_env({}), {}) is None
    assert odata.transport_from_env(settings(), ENV) is not None


def test_env_file_does_not_override_existing_values(tmp_path):
    path = tmp_path / ".env"
    path.write_text("BWACE_ODATA_USER=from_file\nBWACE_ODATA_BASE_URL=https://from-file\n", encoding="utf-8")
    env = {"BWACE_ODATA_USER": "from_environment"}
    loaded = odata.load_env_file(str(path), env)
    assert env["BWACE_ODATA_USER"] == "from_environment"
    assert env["BWACE_ODATA_BASE_URL"] == "https://from-file"
    assert loaded == ("BWACE_ODATA_BASE_URL",)


def test_missing_env_file_is_not_an_error():
    assert odata.load_env_file("does-not-exist.env", {}) == ()
