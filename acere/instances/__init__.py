"""Global singleton instances, one module per service."""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable


class GlobalInstance[T]:
    """Holder for a global service instance, optionally lazy-initialised via a factory."""

    def __init__(self, name: str, factory: Callable[[], T] | None = None) -> None:
        self._name = name
        self._factory = factory
        self._value: T | None = None

    def set(self, value: T) -> None:
        """Set the global instance."""
        self._value = value

    def get(self) -> T:
        """Get the global instance, creating it via the factory if one was provided."""
        if self._value is None:
            if self._factory is None:
                msg = f"{self._name} instance is not set."
                raise ValueError(msg)
            self._value = self._factory()
        return self._value
