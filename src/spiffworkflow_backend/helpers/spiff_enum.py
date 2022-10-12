"""Spiff_enum."""
import enum


class SpiffEnum(enum.Enum):
    """SpiffEnum."""

    @classmethod
    def list(cls) -> list[str]:
        """List."""
        return [el.value for el in cls]
