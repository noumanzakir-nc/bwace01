"""Typed domain objects for the assessment engine. No logic beyond trivial derived access."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from enum import Enum
from types import MappingProxyType
from typing import Mapping


class Category(Enum):
    DECOMMISSION = "DECOMMISSION"
    REPLICATE_AS_IS = "REPLICATE_AS_IS"
    REBUILD_AS_DATA_PRODUCT = "REBUILD_AS_DATA_PRODUCT"


class Determinant(Enum):
    SCORE = "SCORE"
    DORMANCY_CEILING = "DORMANCY_CEILING"
    ACTIVITY_FLOOR = "ACTIVITY_FLOOR"


class RiskBand(Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class Severity(Enum):
    ERROR = "ERROR"
    WARNING = "WARNING"


class EdgeType(Enum):
    LOGICAL = "LOGICAL"
    OPERATIONAL = "OPERATIONAL"
    CONSTRAINT = "CONSTRAINT"


class NodeType(Enum):
    SOLUTION_AREA = "SOLUTION_AREA"
    EXTERNAL = "EXTERNAL"
    CONSTRAINT = "CONSTRAINT"
    SHARED_OBJECT = "SHARED_OBJECT"
    SOURCE = "SOURCE"


# ---- Input records ----------------------------------------------------

@dataclass(frozen=True)
class BwObject:
    object_id: str
    object_type: str
    solution_area: str
    description: str
    data_volume_label: str
    hana_cv_count: int
    adso_count: int
    custom_table_count: int


@dataclass(frozen=True)
class UsageRecord:
    object_id: str
    last_run_date: date
    monthly_executions: int
    distinct_users: int
    business_owner: str


@dataclass(frozen=True)
class AreaCriticality:
    solution_area: str
    criticality: int
    migration_priority: int
    downtime_tolerance_hours: int


@dataclass(frozen=True)
class VolumeMetrics:
    object_id: str
    record_count: int
    storage_gb: int
    load_frequency: str


@dataclass(frozen=True)
class ComplexityMetrics:
    object_id: str
    hana_cv_count: int
    transformation_count: int
    custom_logic_present: bool
    interface_count: int


@dataclass(frozen=True)
class DependencyNode:
    node_id: str
    label: str
    node_type: NodeType


@dataclass(frozen=True)
class DependencyEdge:
    source: str
    target: str
    edge_type: EdgeType
    description: str | None = None


# ---- Aggregate input ----------------------------------------------------

@dataclass(frozen=True)
class Landscape:
    objects: tuple[BwObject, ...]
    usage: Mapping[str, UsageRecord]
    criticality: Mapping[str, AreaCriticality]
    volume: Mapping[str, VolumeMetrics]
    complexity: Mapping[str, ComplexityMetrics]
    nodes: tuple[DependencyNode, ...]
    edges: tuple[DependencyEdge, ...]
    fingerprint: str
    sources: Mapping[str, str]

    def __post_init__(self) -> None:
        object.__setattr__(self, "usage", MappingProxyType(dict(self.usage)))
        object.__setattr__(self, "criticality", MappingProxyType(dict(self.criticality)))
        object.__setattr__(self, "volume", MappingProxyType(dict(self.volume)))
        object.__setattr__(self, "complexity", MappingProxyType(dict(self.complexity)))
        object.__setattr__(self, "sources", MappingProxyType(dict(self.sources)))


# ---- Configuration ----------------------------------------------------

@dataclass(frozen=True)
class ScoringConfig:
    value_threshold: float = 33
    effort_threshold: float = 67
    dormancy_days: int = 180
    dormancy_executions: int = 5
    activity_days: int = 90
    activity_executions: int = 25

    def __post_init__(self) -> None:
        if not self.activity_days < self.dormancy_days:
            raise ValueError("activity_days must be less than dormancy_days")


@dataclass(frozen=True)
class WaveConfig:
    wave_count: int = 5
    wave_months: int = 3
    start_date: date = date(2027, 1, 1)


@dataclass(frozen=True)
class Scenario:
    name: str
    scoring_config: ScoringConfig
    wave_config: WaveConfig


# ---- Computed entities ----------------------------------------------------

@dataclass(frozen=True)
class DimensionScore:
    dimension: str
    raw_display: str
    normalised: float
    weight: float
    contribution: float
    inherited_from: str | None = None


@dataclass(frozen=True)
class AxisScore:
    axis: str
    total: float
    dimensions: tuple[DimensionScore, ...]


@dataclass(frozen=True)
class Classification:
    category: Category
    determinant: Determinant
    is_dormant: bool
    is_active: bool
    rationale: str


@dataclass(frozen=True)
class ObjectAssessment:
    object_id: str
    bw_object: BwObject
    usage: UsageRecord
    business_value: AxisScore
    technical_effort: AxisScore
    classification: Classification
    incoming: tuple[DependencyEdge, ...]
    outgoing: tuple[DependencyEdge, ...]


@dataclass(frozen=True)
class LandscapeKpis:
    total_objects: int
    total_storage_gb: int
    decommission_pct: float
    reclaimable_storage_gb: int


@dataclass(frozen=True)
class AssessmentResult:
    assessments: tuple[ObjectAssessment, ...]
    distribution: Mapping[Category, int]
    graph: "DependencyGraph"
    wave_plan: "WavePlan"
    kpis: LandscapeKpis
    scoring_config: ScoringConfig
    wave_config: WaveConfig
    fingerprint: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "distribution", MappingProxyType(dict(self.distribution)))


# ---- Graph ----------------------------------------------------

@dataclass(frozen=True)
class DependencyGraph:
    nodes: tuple[DependencyNode, ...]
    edges: tuple[DependencyEdge, ...]
    out_degree: Mapping[str, int]
    in_degree: Mapping[str, int]
    area_order: tuple[str, ...]
    area_matrix: tuple[tuple[int, ...], ...]
    layout: Mapping[str, tuple[float, float]]

    def __post_init__(self) -> None:
        object.__setattr__(self, "out_degree", MappingProxyType(dict(self.out_degree)))
        object.__setattr__(self, "in_degree", MappingProxyType(dict(self.in_degree)))
        object.__setattr__(self, "layout", MappingProxyType(dict(self.layout)))


# ---- Planning entities ----------------------------------------------------

@dataclass(frozen=True)
class WaveRisk:
    score: float
    band: RiskBand
    complexity_contribution: float
    dependency_contribution: float
    downtime_contribution: float
    dmk_contribution: float


@dataclass(frozen=True)
class Wave:
    number: int
    start_date: date
    end_date: date
    object_ids: tuple[str, ...]
    areas: tuple[str, ...]
    risk: WaveRisk


@dataclass(frozen=True)
class DependencyViolation:
    dependent_area: str
    depends_on_area: str
    dependent_wave: int
    depends_on_wave: int
    description: str


@dataclass(frozen=True)
class WavePlan:
    waves: tuple[Wave, ...]
    violations: tuple[DependencyViolation, ...]


# ---- Validation entities ----------------------------------------------------

@dataclass(frozen=True)
class ValidationIssue:
    dataset: str
    field: str | None
    record: str | None
    message: str
    severity: Severity


@dataclass(frozen=True)
class ValidationReport:
    issues: tuple[ValidationIssue, ...] = field(default_factory=tuple)

    @property
    def is_fatal(self) -> bool:
        return any(issue.severity is Severity.ERROR for issue in self.issues)


@dataclass(frozen=True)
class LoadOutcome:
    landscape: Landscape | None
    report: ValidationReport


# ---- Comparison entities ----------------------------------------------------

@dataclass(frozen=True)
class ClassificationChange:
    object_id: str
    left_category: Category
    right_category: Category


@dataclass(frozen=True)
class ScenarioDiff:
    left_name: str
    right_name: str
    changed: tuple[ClassificationChange, ...]
    left_distribution: Mapping[Category, int]
    right_distribution: Mapping[Category, int]

    def __post_init__(self) -> None:
        object.__setattr__(self, "left_distribution", MappingProxyType(dict(self.left_distribution)))
        object.__setattr__(self, "right_distribution", MappingProxyType(dict(self.right_distribution)))


# ---- Service intermediate type ----------------------------------------------------

@dataclass(frozen=True)
class BaseScores:
    graph: DependencyGraph
    axis_scores: Mapping[str, tuple[AxisScore, AxisScore]]
    reference_date: date

    def __post_init__(self) -> None:
        object.__setattr__(self, "axis_scores", MappingProxyType(dict(self.axis_scores)))
