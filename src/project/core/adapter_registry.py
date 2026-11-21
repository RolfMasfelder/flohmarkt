"""Adapter-Registry: dynamisches Laden von Plattform-Adaptern via ``adapter_slug``."""

from importlib import import_module
from typing import Callable, Protocol


class BaseAdapter(Protocol):
    """Zentrales Adapter-Interface (Kernentscheidung der Architektur).

    Die Domäne kennt nur dieses Interface. Adapter implementieren:

    - ``create(item, media)`` → externe ID
    - ``update(item, media)``
    - ``delete(ext_id)``
    - ``sync_status(ext_id)`` → Status-Info

    ``media``: Liste absoluter Pfade (Bytes/Datei), die hochgeladen werden.
    """

    def create(self, **kwargs) -> str:
        ...

    def update(self, **kwargs) -> None:
        ...

    def delete(self, ext_id: str) -> None:
        ...

    def sync_status(self, ext_id: str) -> dict:
        ...


# Registry-Singleton (pro-Process; Stateless, Adapter selbst konfigurierbar)
_registry: dict[str, Callable[[], BaseAdapter]] = {}


def register(slug: str, factory: Callable[[], BaseAdapter]) -> None:
    _registry[slug] = factory


def get(slug: str) -> BaseAdapter:
    try:
        factory = _registry[slug]
    except KeyError as exc:
        raise LookupError(f"Kein Adapter für Slug {slug!r}. Registriert: {sorted(_registry)}") from exc
    return factory()


def slugs() -> list[str]:
    return sorted(_registry)
