"""Binding assertions from unit-of-work.md Unit 1 Definition of Done. See business-rules.md #13."""
from bwace.engine.classification import classify_by_score
from bwace.engine.config import DEFAULT_SCORING, DEFAULT_WAVES
from bwace.engine.loader import load_bundled
from bwace.engine.models import Category, Determinant, ScoringConfig
from bwace.engine.service import assess


def _result():
    landscape = load_bundled().landscape
    return assess(landscape, DEFAULT_SCORING, DEFAULT_WAVES), landscape


def test_bundled_dataset_loads_22_objects_12_areas():
    _, landscape = _result()
    assert len(landscape.objects) == 22
    areas = {a for obj in landscape.objects for a in obj.solution_area.split("/")}
    assert len(areas) == 12
    zmd1 = next(o for o in landscape.objects if o.object_id == "ZMD1")
    assert "/" in zmd1.solution_area


def test_every_object_has_scores_and_classification():
    result, _ = _result()
    for a in result.assessments:
        assert a.business_value is not None
        assert a.technical_effort is not None
        assert a.classification is not None
        assert a.classification.category in Category


def test_reference_distribution_5_13_4():
    result, _ = _result()
    dist = result.distribution
    assert dist[Category.REBUILD_AS_DATA_PRODUCT] == 5
    assert dist[Category.REPLICATE_AS_IS] == 13
    assert dist[Category.DECOMMISSION] == 4


def test_exact_rebuild_set():
    result, _ = _result()
    rebuild = {a.object_id for a in result.assessments if a.classification.category is Category.REBUILD_AS_DATA_PRODUCT}
    assert rebuild == {"SC100", "SC200", "SA100", "PR100", "PR200"}


def test_exact_decommission_set():
    result, _ = _result()
    decommission = {a.object_id for a in result.assessments if a.classification.category is Category.DECOMMISSION}
    assert decommission == {"IN200", "TR100", "TR200", "TM100"}


def test_guard_overrides_exactly_two_objects():
    result, landscape = _result()
    ref = None
    from bwace.engine.scoring import reference_date
    ref = reference_date(landscape)

    differences = []
    for a in result.assessments:
        pure = classify_by_score(a.business_value, a.technical_effort, DEFAULT_SCORING)
        if pure != a.classification.category:
            differences.append(a.object_id)
    assert set(differences) == {"IN200", "IM100"}


def test_in200_dormancy_ceiling_im100_activity_floor():
    result, _ = _result()
    in200 = next(a for a in result.assessments if a.object_id == "IN200")
    im100 = next(a for a in result.assessments if a.object_id == "IM100")
    assert in200.classification.determinant is Determinant.DORMANCY_CEILING
    assert im100.classification.determinant is Determinant.ACTIVITY_FLOOR


def test_fi100gc_flips_at_effort_66():
    landscape = load_bundled().landscape
    result_default = assess(landscape, DEFAULT_SCORING, DEFAULT_WAVES)
    result_66 = assess(landscape, ScoringConfig(effort_threshold=66), DEFAULT_WAVES)
    fi_default = next(a for a in result_default.assessments if a.object_id == "FI100GC")
    fi_66 = next(a for a in result_66.assessments if a.object_id == "FI100GC")
    assert fi_default.classification.category is Category.REPLICATE_AS_IS
    assert fi_66.classification.category is Category.REBUILD_AS_DATA_PRODUCT


def test_dmk_expansion_12_edges():
    result, _ = _result()
    dmk_edges = [e for e in result.graph.edges if e.target == "DMK"]
    assert len(dmk_edges) == 12


def test_every_object_assigned_exactly_one_wave():
    result, _ = _result()
    assigned = [oid for w in result.wave_plan.waves for oid in w.object_ids]
    assert len(assigned) == 22
    assert len(set(assigned)) == 22


def test_exactly_one_violation():
    result, _ = _result()
    assert len(result.wave_plan.violations) == 1


def test_risk_bands_1_low_3_medium_1_high():
    result, _ = _result()
    bands = [w.risk.band.value for w in result.wave_plan.waves]
    assert bands.count("LOW") == 1
    assert bands.count("MEDIUM") == 3
    assert bands.count("HIGH") == 1


def test_malformed_input_returns_report_never_raises():
    from bwace.engine.loader import validate_objects
    objects, report = validate_objects([{"object_id": "BAD"}])
    assert objects == ()
    assert report.is_fatal


def test_exports_contain_22_rows_and_embed_config():
    from bwace.engine.export import classification_csv, wave_recommendation_json
    result, _ = _result()
    csv_text = classification_csv(result)
    data_rows = [line for line in csv_text.splitlines() if line.strip()][1:23]
    assert len(data_rows) == 22
    payload = wave_recommendation_json(result)
    assert payload["configuration"]["value_threshold"] == DEFAULT_SCORING.value_threshold
