"""
Processing Version Specification.

Every observation and artifact produced by the Mandi Nyaay inspection engine
must embed the processing version to guarantee auditability, traceability, and
reproducibility across all pipeline executions.
"""

from typing import Final

PROCESSING_VERSION: Final[str] = "0.1.0-phase0.dev"


def get_processing_version() -> str:
    """Return the active code/pipeline processing version string."""
    return PROCESSING_VERSION
