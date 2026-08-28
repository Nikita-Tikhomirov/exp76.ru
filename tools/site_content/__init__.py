"""Validated content evidence used by the service-hub release."""

from importlib import import_module
from typing import Any

__all__ = [
    "CaseEvidence",
    "ImageAudit",
    "PageAudit",
    "build_case_catalog",
    "validate_case_reference",
]


def __getattr__(name: str) -> Any:
    """Load case exports lazily so ``python -m tools.site_content.cases`` is clean."""
    if name not in __all__:
        raise AttributeError(name)
    return getattr(import_module(".cases", __name__), name)
