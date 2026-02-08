"""Runtime primitives: lifecycle, health and error contracts."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from orchid_commons.runtime.errors import (
    InvalidResourceNameError,
    MissingDependencyError,
    MissingRequiredResourceError,
    OrchidCommonsError,
    ResourceNotFoundError,
    ShutdownError,
)
from orchid_commons.runtime.health import (
    HealthCheck,
    HealthReport,
    HealthStatus,
    HealthSummary,
    Resource,
    aggregate_health_checks,
)

if TYPE_CHECKING:
    from orchid_commons.runtime.manager import (
        ResourceFactory,
        ResourceManager,
        bootstrap_resources,
        register_factory,
    )

__all__ = [
    "HealthCheck",
    "HealthReport",
    "HealthStatus",
    "HealthSummary",
    "InvalidResourceNameError",
    "MissingDependencyError",
    "MissingRequiredResourceError",
    "OrchidCommonsError",
    "Resource",
    "ResourceFactory",
    "ResourceManager",
    "ResourceNotFoundError",
    "ShutdownError",
    "aggregate_health_checks",
    "bootstrap_resources",
    "register_factory",
]


def __getattr__(name: str) -> Any:
    if name in {"ResourceFactory", "ResourceManager", "bootstrap_resources", "register_factory"}:
        from orchid_commons.runtime.manager import (
            ResourceFactory,
            ResourceManager,
            bootstrap_resources,
            register_factory,
        )

        exported: dict[str, Any] = {
            "ResourceFactory": ResourceFactory,
            "ResourceManager": ResourceManager,
            "bootstrap_resources": bootstrap_resources,
            "register_factory": register_factory,
        }
        return exported[name]

    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
