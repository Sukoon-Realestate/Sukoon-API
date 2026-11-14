"""Domain command receipt; HTTP adapters choose rendering independently."""

from dataclasses import dataclass


@dataclass(frozen=True)
class MoneyResult:
    data: object
    status: int = 200


__all__ = ["MoneyResult"]
