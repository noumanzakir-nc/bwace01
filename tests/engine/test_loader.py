from bwace.engine.loader import load_bundled
from bwace.engine.models import Severity


def test_load_bundled_succeeds():
    outcome = load_bundled()
    assert outcome.report.is_fatal is False
    assert outcome.landscape is not None
    assert len(outcome.landscape.objects) == 22


def test_fingerprint_stable_across_loads():
    first = load_bundled()
    second = load_bundled()
    assert first.landscape.fingerprint == second.landscape.fingerprint


def test_fingerprint_changes_with_content():
    from bwace.engine.loader import fingerprint
    a = fingerprint({"x": b"hello"})
    b = fingerprint({"x": b"world"})
    assert a != b


def test_sources_all_bundled_by_default():
    outcome = load_bundled()
    assert all(v == "bundled" for v in outcome.landscape.sources.values())


def test_validate_objects_missing_field_is_error():
    from bwace.engine.loader import validate_objects
    records = [{"object_id": "X1", "object_type": "Query"}]  # missing required fields
    objects, report = validate_objects(records)
    assert len(objects) == 0
    assert report.is_fatal
    assert all(i.severity is Severity.ERROR for i in report.issues)


def test_validate_usage_bad_date_is_error():
    from bwace.engine.loader import validate_usage
    records = [{"object_id": "X1", "last_run_date": "not-a-date", "monthly_executions": 1,
                "distinct_users": 1, "business_owner": "Owner"}]
    usage, report = validate_usage(records)
    assert len(usage) == 0
    assert report.is_fatal


def test_validate_volume_negative_value_is_error():
    from bwace.engine.loader import validate_volume
    records = [{"object_id": "X1", "record_count": -5, "storage_gb": 1, "load_frequency": "Daily"}]
    _, report = validate_volume(records)
    assert report.is_fatal


def test_validate_volume_unknown_load_frequency_is_warning():
    from bwace.engine.loader import validate_volume
    records = [{"object_id": "X1", "record_count": 5, "storage_gb": 1, "load_frequency": "Fortnightly"}]
    volume, report = validate_volume(records)
    assert "X1" in volume
    assert not report.is_fatal
    assert any(i.severity is Severity.WARNING for i in report.issues)


def test_referential_integrity_missing_area_is_error():
    from bwace.engine.loader import check_referential_integrity
    from bwace.engine.models import BwObject

    obj = BwObject(object_id="X1", object_type="Query", solution_area="Nonexistent Area",
                    description="d", data_volume_label="Low", hana_cv_count=0,
                    adso_count=0, custom_table_count=0)
    report = check_referential_integrity((obj,), {}, {}, {}, {})
    assert report.is_fatal


def test_referential_integrity_missing_usage_is_warning():
    from bwace.engine.loader import check_referential_integrity
    from bwace.engine.models import AreaCriticality, BwObject

    obj = BwObject(object_id="X1", object_type="Query", solution_area="Area A",
                    description="d", data_volume_label="Low", hana_cv_count=0,
                    adso_count=0, custom_table_count=0)
    criticality = {"Area A": AreaCriticality(solution_area="Area A", criticality=50,
                                              migration_priority=1, downtime_tolerance_hours=24)}
    report = check_referential_integrity((obj,), {}, criticality, {}, {})
    assert not report.is_fatal
    assert any(i.severity is Severity.WARNING for i in report.issues)
