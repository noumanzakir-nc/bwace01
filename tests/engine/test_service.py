from bwace.engine.config import DEFAULT_SCORING, DEFAULT_WAVES
from bwace.engine.loader import load_bundled
from bwace.engine.models import Scenario, ScoringConfig
from bwace.engine.service import apply_config, assess, compare, compute_base, kpis


def _landscape():
    return load_bundled().landscape


def test_compute_base_is_dataset_only_and_cacheable():
    landscape = _landscape()
    base_a = compute_base(landscape)
    base_b = compute_base(landscape)
    assert base_a.reference_date == base_b.reference_date
    assert base_a.axis_scores.keys() == base_b.axis_scores.keys()


def test_apply_config_reflects_live_threshold():
    landscape = _landscape()
    base = compute_base(landscape)
    result_default = apply_config(base, landscape, DEFAULT_SCORING, DEFAULT_WAVES)
    result_lower_effort = apply_config(base, landscape, ScoringConfig(effort_threshold=66), DEFAULT_WAVES)
    default_categories = {a.object_id: a.classification.category for a in result_default.assessments}
    lower_categories = {a.object_id: a.classification.category for a in result_lower_effort.assessments}
    assert default_categories["FI100GC"] != lower_categories["FI100GC"]


def test_assess_matches_manual_compute_base_apply_config():
    landscape = _landscape()
    base = compute_base(landscape)
    manual = apply_config(base, landscape, DEFAULT_SCORING, DEFAULT_WAVES)
    convenience = assess(landscape, DEFAULT_SCORING, DEFAULT_WAVES)
    assert manual.distribution == convenience.distribution


def test_compare_shares_one_base_and_diffs_correctly():
    landscape = _landscape()
    left = Scenario(name="Default", scoring_config=DEFAULT_SCORING, wave_config=DEFAULT_WAVES)
    right = Scenario(name="LowerEffort", scoring_config=ScoringConfig(effort_threshold=66), wave_config=DEFAULT_WAVES)
    diff = compare(landscape, left, right)
    changed_ids = {c.object_id for c in diff.changed}
    assert "FI100GC" in changed_ids


def test_kpis_matches_reference():
    landscape = _landscape()
    result = assess(landscape, DEFAULT_SCORING, DEFAULT_WAVES)
    kpi = kpis(result.assessments, landscape)
    assert kpi.total_objects == 22
    assert kpi.total_storage_gb == 604
    assert round(kpi.decommission_pct, 1) == 18.2
    assert kpi.reclaimable_storage_gb == 21
