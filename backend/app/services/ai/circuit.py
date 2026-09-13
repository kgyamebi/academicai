"""Per-provider circuit breaker for AI fallback. Not a product feature."""

from __future__ import annotations

import time
from dataclasses import dataclass
from threading import Lock

from app.config import get_settings

_lock = Lock()


@dataclass
class CircuitState:
    failures: int = 0
    opened_at: float | None = None
    state: str = "closed"


_circuits: dict[str, CircuitState] = {}


def reset_circuits() -> None:
    with _lock:
        _circuits.clear()


def allow(provider: str) -> bool:
    settings = get_settings()
    cooldown = settings.ai_circuit_cooldown_seconds
    with _lock:
        circuit = _circuits.setdefault(provider, CircuitState())
        if circuit.state != "open":
            return True
        if circuit.opened_at is None:
            circuit.state = "half_open"
            return True
        if time.monotonic() - circuit.opened_at >= cooldown:
            circuit.state = "half_open"
            return True
        return False


def record_success(provider: str) -> None:
    with _lock:
        _circuits[provider] = CircuitState()


def record_failure(provider: str) -> None:
    settings = get_settings()
    with _lock:
        circuit = _circuits.setdefault(provider, CircuitState())
        circuit.failures += 1
        if circuit.failures >= settings.ai_circuit_threshold:
            circuit.state = "open"
            circuit.opened_at = time.monotonic()


def snapshot() -> dict[str, str]:
    with _lock:
        return {name: circuit.state for name, circuit in _circuits.items()}
