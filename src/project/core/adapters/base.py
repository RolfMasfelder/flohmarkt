"""Base-Class für konkrete Plattform-Adapter.

Jeder Adapter ist eine Python-Class in ``src/project/core/adapters/<name>.py``
und implementiert die Methoden aus :mod:`project.core.adapter_registry`.
"""

import abc
from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class AdapterInterface(Protocol):
    def create(self, item, media) -> str: ...
    def update(self, item, media) -> None: ...
    def delete(self, ext_id: str) -> None: ...
    def sync_status(self, ext_id: str) -> dict[str, Any]: ...


class BaseAdapter(abc.ABC):
    """Mixin mit Shared-Logik (httpx-Client, Retry) für Adapter."""

    def __init__(self, config: dict[str, Any]):
        self.config = config
        self._closed = False

    # -- Lifecycle -------------------------------------------------------------
    def close(self) -> None:
        self._closed = True

    # -- Abstrakte API ---------------------------------------------------------
    @abc.abstractmethod
    def create(self, item, media) -> str: ...

    @abc.abstractmethod
    def update(self, item, media) -> None: ...

    @abc.abstractmethod
    def delete(self, ext_id: str) -> None: ...

    @abc.abstractmethod
    def sync_status(self, ext_id: str) -> dict[str, Any]: ...
