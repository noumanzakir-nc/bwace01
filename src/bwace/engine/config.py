"""Static defaults: weights, bands, thresholds, palette, guard parameters. See business-rules.md."""
from __future__ import annotations

from datetime import date
from typing import NamedTuple

from bwace.engine.models import ScoringConfig, WaveConfig


class Band(NamedTuple):
    upper: float  # inclusive upper bound; last band's upper is math.inf
    score: float


VALUE_WEIGHTS: dict[str, float] = {
    "usage_frequency": 29.41,
    "distinct_users": 17.65,
    "criticality": 23.53,
    "outgoing_dependencies": 17.65,
    "incoming_dependencies": 11.76,
}

EFFORT_WEIGHTS: dict[str, float] = {
    "technical_complexity": 66.67,
    "data_volume": 33.33,
}

COMPLEXITY_SUBWEIGHTS: dict[str, float] = {
    "hana_cv_count": 0.40,
    "transformation_count": 0.30,
    "interface_count": 0.20,
    "custom_logic_present": 0.10,
}

VOLUME_SUBWEIGHTS: dict[str, float] = {
    "record_count": 0.40,
    "storage_gb": 0.40,
    "load_frequency": 0.20,
}

INF = float("inf")

BANDS: dict[str, tuple[Band, ...]] = {
    "usage_frequency": (
        Band(5, 0), Band(25, 20), Band(75, 40), Band(150, 60), Band(300, 80), Band(INF, 100),
    ),
    "distinct_users": (
        Band(2, 0), Band(10, 20), Band(20, 40), Band(40, 60), Band(70, 80), Band(INF, 100),
    ),
    "outgoing_dependencies": (
        Band(0, 0), Band(1, 20), Band(2, 40), Band(3, 60), Band(4, 80), Band(INF, 100),
    ),
    "incoming_dependencies": (
        Band(0, 0), Band(1, 25), Band(2, 50), Band(4, 75), Band(INF, 100),
    ),
    "hana_cv_count": (
        Band(0, 0), Band(5, 20), Band(10, 40), Band(15, 60), Band(20, 80), Band(INF, 100),
    ),
    "transformation_count": (
        Band(0, 0), Band(3, 20), Band(6, 40), Band(9, 60), Band(12, 80), Band(INF, 100),
    ),
    "interface_count": (
        Band(0, 0), Band(2, 20), Band(4, 40), Band(6, 60), Band(8, 80), Band(INF, 100),
    ),
    "record_count": (
        Band(499_999, 0), Band(1_000_000, 20), Band(3_000_000, 40),
        Band(8_000_000, 60), Band(15_000_000, 80), Band(INF, 100),
    ),
    "storage_gb": (
        Band(4, 0), Band(10, 20), Band(25, 40), Band(50, 60), Band(80, 80), Band(INF, 100),
    ),
}

LOAD_FREQUENCY_SCORES: dict[str, float] = {
    "Monthly": 0,
    "Weekly": 25,
    "Daily": 75,
    "Hourly": 100,
}


class RecencyTier(NamedTuple):
    upper_days: float  # inclusive upper bound; last tier's upper is math.inf
    factor: float


RECENCY_TIERS: tuple[RecencyTier, ...] = (
    RecencyTier(90, 1.00),
    RecencyTier(180, 0.75),
    RecencyTier(365, 0.50),
    RecencyTier(INF, 0.25),
)

DEFAULT_SCORING = ScoringConfig()
DEFAULT_WAVES = WaveConfig()


class RiskBandBoundary(NamedTuple):
    upper: float  # inclusive upper bound
    band: str


RISK_BANDS: tuple[RiskBandBoundary, ...] = (
    RiskBandBoundary(39, "LOW"),
    RiskBandBoundary(69, "MEDIUM"),
    RiskBandBoundary(INF, "HIGH"),
)

RISK_WEIGHTS: dict[str, float] = {
    "complexity": 0.40,
    "dependency": 0.25,
    "downtime": 0.25,
    "dmk": 0.10,
}

CROSS_WAVE_DEPENDENCY_BANDS: tuple[Band, ...] = (
    Band(0, 0), Band(1, 25), Band(2, 50), Band(4, 75), Band(INF, 100),
)

DOWNTIME_BANDS: tuple[Band, ...] = (
    Band(4, 100), Band(8, 80), Band(12, 60), Band(24, 40), Band(48, 20), Band(INF, 0),
)

DMK_FREEZE_UNTIL = date(2028, 1, 1)

# Node types that are never schedulable / never violation endpoints (BR-8.4, BR-9.1b)
NON_SCHEDULABLE_NODE_TYPES = frozenset({"EXTERNAL", "CONSTRAINT", "SHARED_OBJECT", "SOURCE"})


# ---- Live SAP OData connectivity (requirements §10) ----------------------

# Service paths are placeholders, not SAP-delivered endpoints. See requirements
# §10.2 — no SAP-delivered service by these names could be found; they ship as
# defaults only so the configured endpoint list matches what was promised.
ODATA_DEFAULT_SERVICE_ROOT = "/sap/opu/odata/sap"

ODATA_DEFAULT_SERVICE_PATHS: dict[str, str] = {
    "object_inventory": "RSOD_CATALOG_SRV/ObjectCatalog",
    "complexity": "RSOD_ADSO_SRV/AdsoMetadata",
    "data_volume": "RSOD_ADSO_SRV/AdsoVolume",
    "dependencies": "RSPC_API_SRV/ProcessChains",
    "usage_logs": "RSOD_USAGE_SRV/Results",
}

# criticality is deliberately absent: business criticality, migration priority
# and downtime tolerance are business judgements, not BW metadata (FR-14.1).
ODATA_LIVE_DATASETS: tuple[str, ...] = (
    "object_inventory", "complexity", "data_volume", "dependencies", "usage_logs",
)

ODATA_DEFAULT_TIMEOUT_SECONDS = 30.0
ODATA_DEFAULT_MAX_RECORDS = 5_000
ODATA_RETRY_ATTEMPTS = 3
ODATA_RETRY_BACKOFF_SECONDS = 0.5

ODATA_ENV_VARS: dict[str, str] = {
    "base_url": "BWACE_ODATA_BASE_URL",
    "service_root": "BWACE_ODATA_SERVICE_ROOT",
    "user": "BWACE_ODATA_USER",
    "password": "BWACE_ODATA_PASSWORD",
    "ca_bundle": "BWACE_ODATA_CA_BUNDLE",
    "timeout": "BWACE_ODATA_TIMEOUT_SECONDS",
    "max_records": "BWACE_ODATA_MAX_RECORDS",
}

ODATA_SERVICE_ENV_VARS: dict[str, str] = {
    "object_inventory": "BWACE_ODATA_SERVICE_INVENTORY",
    "complexity": "BWACE_ODATA_SERVICE_COMPLEXITY",
    "data_volume": "BWACE_ODATA_SERVICE_VOLUME",
    "dependencies": "BWACE_ODATA_SERVICE_DEPENDENCIES",
    "usage_logs": "BWACE_ODATA_SERVICE_USAGE",
}
