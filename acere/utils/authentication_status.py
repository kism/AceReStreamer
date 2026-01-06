"""Model for toggling authentication."""

from acere.utils.logger import get_logger

logger = get_logger(__name__)


class AuthenticationStatus:
    """Simple object to toggle authentication."""

    _enabled: bool = True

    def __bool__(self) -> bool:
        """Check if authentication is enabled."""
        return self._enabled

    def set_enabled(self, *, enabled: bool) -> None:
        """Set the status of authentication."""
        if not enabled:
            logger.warning("Authentication disabled")
            # use somethign like: flask_principal.Permission.can = lambda self: True
            raise NotImplementedError

        self._enabled = enabled
