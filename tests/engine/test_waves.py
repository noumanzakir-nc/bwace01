from bwace.engine.config import DEFAULT_SCORING
from bwace.engine.dependencies import build_graph
from bwace.engine.loader import load_bundled
from bwace.engine.service import compute_base, apply_config
from bwace.engine.models import WaveConfig


def _result(wave_count: int = 5):
    landscape = load_bundled().landscape
    base = compute_base(landscape)
    return apply_config(base, landscape, DEFAULT_SCORING, WaveConfig(wave_count=wave_count)), landscape


def test_wave_object_counts_at_default_five_waves():
    result, _ = _result(5)
    counts = [len(w.object_ids) for w in result.wave_plan.waves]
    assert counts == [5, 4, 5, 3, 5]
    assert sum(counts) == 22


def test_wave_compression_at_three_waves():
    result, _ = _result(3)
    counts = [len(w.object_ids) for w in result.wave_plan.waves]
    assert len(counts) == 3
    assert sum(counts) == 22


def test_wave_count_seven_leaves_last_two_empty():
    result, _ = _result(7)
    counts = [len(w.object_ids) for w in result.wave_plan.waves]
    assert len(counts) == 7
    assert counts[5] == 0
    assert counts[6] == 0
    assert sum(counts) == 22


def test_exactly_one_violation_lc_to_tm():
    result, _ = _result(5)
    assert len(result.wave_plan.violations) == 1
    v = result.wave_plan.violations[0]
    assert v.dependent_area == "Logistics Costing"
    assert v.depends_on_area == "Transport Management"


def test_risk_bands_match_reference():
    result, _ = _result(5)
    bands = [w.risk.band.value for w in result.wave_plan.waves]
    assert bands == ["MEDIUM", "HIGH", "MEDIUM", "MEDIUM", "LOW"]
    assert round(result.wave_plan.waves[1].risk.score, 1) == 77.9
