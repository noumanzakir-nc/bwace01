from bwace.engine.config import DEFAULT_SCORING, DEFAULT_WAVES
from bwace.engine.export import classification_csv, config_summary, wave_recommendation_json
from bwace.engine.loader import load_bundled
from bwace.engine.service import assess


def _result():
    landscape = load_bundled().landscape
    return assess(landscape, DEFAULT_SCORING, DEFAULT_WAVES)


def test_classification_csv_has_22_data_rows():
    result = _result()
    csv_text = classification_csv(result)
    lines = [line for line in csv_text.splitlines() if line.strip()]
    data_lines = lines[1:23]  # header + 22 rows
    assert len(data_lines) == 22


def test_classification_csv_embeds_configuration():
    result = _result()
    csv_text = classification_csv(result)
    assert "value_threshold" in csv_text
    assert "33" in csv_text


def test_wave_recommendation_json_structure():
    result = _result()
    payload = wave_recommendation_json(result)
    assert len(payload["waves"]) == 5
    assert len(payload["violations"]) == 1
    assert payload["configuration"]["value_threshold"] == 33


def test_config_summary_fields():
    summary = config_summary(DEFAULT_SCORING, DEFAULT_WAVES)
    assert summary["wave_count"] == 5
    assert summary["value_threshold"] == 33
