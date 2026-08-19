from datetime import date

from bwace.engine.classification import classify, classify_by_score, is_active, is_dormant
from bwace.engine.config import DEFAULT_SCORING
from bwace.engine.models import AxisScore, Category, Determinant, ScoringConfig, UsageRecord


def _axis(total: float) -> AxisScore:
    return AxisScore(axis="test", total=total, dimensions=())


def test_classify_by_score_quadrants():
    cfg = DEFAULT_SCORING
    assert classify_by_score(_axis(20), _axis(80), cfg) is Category.DECOMMISSION
    assert classify_by_score(_axis(50), _axis(50), cfg) is Category.REPLICATE_AS_IS
    assert classify_by_score(_axis(50), _axis(80), cfg) is Category.REBUILD_AS_DATA_PRODUCT


def test_guard_predicates_mutually_exclusive():
    cfg = DEFAULT_SCORING
    reference = date(2026, 8, 14)
    usage = UsageRecord(object_id="X", last_run_date=date(2025, 8, 1), monthly_executions=2,
                         distinct_users=1, business_owner="Owner")
    dormant = is_dormant(usage, reference, cfg)
    active = is_active(usage, reference, cfg)
    assert not (dormant and active)


def test_scoring_config_rejects_invalid_guard_ordering():
    import pytest
    with pytest.raises(ValueError):
        ScoringConfig(activity_days=200, dormancy_days=100)


def test_dormancy_ceiling_overrides_score():
    cfg = DEFAULT_SCORING
    reference = date(2026, 8, 14)
    usage = UsageRecord(object_id="IN200", last_run_date=date(2025, 8, 4), monthly_executions=2,
                         distinct_users=1, business_owner="Owner")
    value = _axis(35.9)
    effort = _axis(25.7)
    result = classify(value, effort, usage, reference, cfg)
    assert result.category is Category.DECOMMISSION
    assert result.determinant is Determinant.DORMANCY_CEILING
    assert result.is_dormant is True


def test_activity_floor_protects_object():
    cfg = DEFAULT_SCORING
    reference = date(2026, 8, 14)
    usage = UsageRecord(object_id="IM100", last_run_date=date(2026, 8, 7), monthly_executions=40,
                         distinct_users=10, business_owner="Owner")
    value = _axis(31.8)
    effort = _axis(31.0)
    result = classify(value, effort, usage, reference, cfg)
    assert result.category is Category.REPLICATE_AS_IS
    assert result.determinant is Determinant.ACTIVITY_FLOOR
    assert result.is_active is True


def test_dormant_without_override_keeps_score_determinant():
    """TR200: dormant is true but the pure-score category is already Decommission."""
    cfg = DEFAULT_SCORING
    reference = date(2026, 8, 14)
    usage = UsageRecord(object_id="TR200", last_run_date=date(2025, 9, 22), monthly_executions=3,
                         distinct_users=2, business_owner="Owner")
    value = _axis(18.8)
    effort = _axis(16.3)
    result = classify(value, effort, usage, reference, cfg)
    assert result.category is Category.DECOMMISSION
    assert result.determinant is Determinant.SCORE
    assert result.is_dormant is True
