"""Framework-free value types for the box-selection core.

These are plain, immutable dataclasses built from ``Decimal``/``int`` only. They
carry no Django or ORM dependency, so the engine can be exercised in isolation.
All lengths are centimetres, weights are grams, cost is money.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True, slots=True)
class Dimensions:
    """A length, width and height in centimetres (order-independent for fit)."""

    length_cm: Decimal
    width_cm: Decimal
    height_cm: Decimal

    @property
    def volume_cm3(self) -> Decimal:
        return self.length_cm * self.width_cm * self.height_cm

    def sorted_sides(self) -> list[Decimal]:
        """Sides ascending, so two boxes can be compared regardless of orientation."""
        return sorted([self.length_cm, self.width_cm, self.height_cm])


@dataclass(frozen=True, slots=True)
class Item:
    """A quantity of one product: its unit dimensions and unit weight."""

    dimensions: Dimensions
    weight_g: Decimal
    quantity: int

    @property
    def total_weight_g(self) -> Decimal:
        return self.weight_g * self.quantity

    @property
    def total_volume_cm3(self) -> Decimal:
        return self.dimensions.volume_cm3 * self.quantity


@dataclass(frozen=True, slots=True)
class BoxSpec:
    """A candidate box. ``id`` lets the caller map the result back to storage."""

    id: int
    name: str
    dimensions: Dimensions
    max_weight_g: Decimal
    cost: Decimal

    @property
    def inner_volume_cm3(self) -> Decimal:
        return self.dimensions.volume_cm3


@dataclass(frozen=True, slots=True)
class BoxEvaluation:
    """A fitting box plus how fully the order would use its capacity.

    Utilisations are ratios in ``[0, 1]`` (order total / box capacity). Because
    only *fitting* boxes are evaluated, both are guaranteed not to exceed 1.
    """

    box: BoxSpec
    volume_utilisation: Decimal
    weight_utilisation: Decimal


@dataclass(frozen=True, slots=True)
class Recommendation:
    """The outcome of a recommendation.

    ``recommended`` is the cheapest fitting box (with utilisation); ``alternatives``
    are the remaining fitting boxes in the same ranked order. On a no-fit both are
    empty and ``reason`` explains why.
    """

    fit_found: bool
    recommended: BoxEvaluation | None
    alternatives: tuple[BoxEvaluation, ...]
    reason: str
