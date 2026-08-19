"""Serialise results for download. See FR-10.1 to FR-10.3."""
from __future__ import annotations

import csv
import io

from bwace.engine.models import AssessmentResult, ScoringConfig, WaveConfig


def config_summary(scoring: ScoringConfig, waves: WaveConfig) -> dict:
    return {
        "value_threshold": scoring.value_threshold,
        "effort_threshold": scoring.effort_threshold,
        "dormancy_days": scoring.dormancy_days,
        "dormancy_executions": scoring.dormancy_executions,
        "activity_days": scoring.activity_days,
        "activity_executions": scoring.activity_executions,
        "wave_count": waves.wave_count,
        "wave_months": waves.wave_months,
        "start_date": waves.start_date.isoformat(),
    }


def classification_csv(result: AssessmentResult) -> str:
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow([
        "object_id", "solution_area", "category", "determinant",
        "business_value", "technical_effort", "rationale",
    ])
    for assessment in result.assessments:
        writer.writerow([
            assessment.object_id,
            assessment.bw_object.solution_area,
            assessment.classification.category.value,
            assessment.classification.determinant.value,
            f"{assessment.business_value.total:.1f}",
            f"{assessment.technical_effort.total:.1f}",
            assessment.classification.rationale,
        ])
    config_block = config_summary(result.scoring_config, result.wave_config)
    writer.writerow([])
    writer.writerow(["configuration"])
    for key, value in config_block.items():
        writer.writerow([key, value])
    return buffer.getvalue()


def wave_recommendation_json(result: AssessmentResult) -> dict:
    return {
        "waves": [
            {
                "number": wave.number,
                "start_date": wave.start_date.isoformat(),
                "end_date": wave.end_date.isoformat(),
                "object_ids": list(wave.object_ids),
                "areas": list(wave.areas),
                "risk": {
                    "score": wave.risk.score,
                    "band": wave.risk.band.value,
                    "complexity_contribution": wave.risk.complexity_contribution,
                    "dependency_contribution": wave.risk.dependency_contribution,
                    "downtime_contribution": wave.risk.downtime_contribution,
                    "dmk_contribution": wave.risk.dmk_contribution,
                },
            }
            for wave in result.wave_plan.waves
        ],
        "violations": [
            {
                "dependent_area": v.dependent_area,
                "depends_on_area": v.depends_on_area,
                "dependent_wave": v.dependent_wave,
                "depends_on_wave": v.depends_on_wave,
                "description": v.description,
            }
            for v in result.wave_plan.violations
        ],
        "configuration": config_summary(result.scoring_config, result.wave_config),
    }
