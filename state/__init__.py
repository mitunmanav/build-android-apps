"""state/ — per-project state.json loader, validator, migrator, manager, router.

Public API:
    SCHEMA_VERSION, current_schema_version
    load, save, validate
    migrate
    StateManager, StateError
    topological_order, detect_cycle, route_full, route_after, explain
"""

from .state import (
    SCHEMA_VERSION,
    current_schema_version,
    load,
    save,
    validate,
)
from .migrate import migrate
from .manager import StateManager, StateError
from .router import (
    topological_order,
    detect_cycle,
    route_full,
    route_after,
    explain,
)

__all__ = [
    "SCHEMA_VERSION",
    "StateError",
    "StateManager",
    "current_schema_version",
    "detect_cycle",
    "explain",
    "load",
    "migrate",
    "route_after",
    "route_full",
    "save",
    "topological_order",
    "validate",
]
