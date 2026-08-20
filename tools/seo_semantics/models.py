"""Immutable records used by the semantic keyword pipeline."""

from dataclasses import dataclass, field


@dataclass(frozen=True)
class KeywordRecord:
    """One keyword observation from a single source methodology."""

    query_raw: str
    query_normalized: str
    source: str
    seed: str = ""
    region: str = ""
    device: str = "all"
    broad_frequency: int | None = None
    phrase_frequency: int | None = None
    exact_frequency: int | None = None
    impressions: int | None = None
    clicks: int | None = None
    ctr: float | None = None
    avg_position: float | None = None
    current_url: str = ""
    collected_at: str = ""
    sources: tuple[str, ...] = field(default_factory=tuple)
