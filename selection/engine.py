"""The box-selection algorithm — pure functions, no side effects, no Django.

An order *fits* a box when ALL of the following hold:

1. Every item fits the box by dimensions, comparing sorted sides so 90 degree axis
   rotation is allowed (a 30x5x5 item fits a 10x10x40 box).
2. The total volume of the order does not exceed the box's internal volume.
3. The total weight of the order does not exceed the box's weight capacity.

Among the fitting boxes the cheapest wins; ties are broken by smallest internal
volume, then by name for determinism. If nothing fits, an explained no-fit
``Recommendation`` is returned.

Known, intentional limitation: checks 1-3 are conservative approximations. Each
item is tested against the box independently; we do not verify that all items can
be physically arranged inside the box at once (true 3D bin packing is out of
scope). This can occasionally report a fit that a real packer would reject.
"""

from __future__ import annotations

from decimal import Decimal

from .types import BoxEvaluation, BoxSpec, Item, Recommendation

_NO_FIT_REASON = (
    "No available box can hold this order within its dimension, volume and weight limits."
)


def dimensions_fit(item_sides: list[Decimal], box_sides: list[Decimal]) -> bool:
    """True if a cuboid fits inside another when both are freely rotatable."""
    return all(
        item_side <= box_side for item_side, box_side in zip(item_sides, box_sides, strict=True)
    )


def item_fits_box(item: Item, box: BoxSpec) -> bool:
    """True if a single unit of ``item`` fits the box by dimensions alone."""
    return dimensions_fit(item.dimensions.sorted_sides(), box.dimensions.sorted_sides())


def order_fits_box(items: list[Item], box: BoxSpec) -> bool:
    """True if every item fits and the order is within the box's volume and weight."""
    total_weight = sum((item.total_weight_g for item in items), Decimal("0"))
    if total_weight > box.max_weight_g:
        return False

    total_volume = sum((item.total_volume_cm3 for item in items), Decimal("0"))
    if total_volume > box.inner_volume_cm3:
        return False

    return all(item_fits_box(item, box) for item in items)


def _evaluate(items: list[Item], box: BoxSpec) -> BoxEvaluation:
    """Capacity utilisation of ``box`` for the order (ratios in [0, 1] when it fits)."""
    total_volume = sum((item.total_volume_cm3 for item in items), Decimal("0"))
    total_weight = sum((item.total_weight_g for item in items), Decimal("0"))
    return BoxEvaluation(
        box=box,
        volume_utilisation=total_volume / box.inner_volume_cm3,
        weight_utilisation=total_weight / box.max_weight_g,
    )


def recommend_box(items: list[Item], boxes: list[BoxSpec]) -> Recommendation:
    """Recommend the cheapest box that fits the order, with ranked alternatives.

    The cheapest fitting box wins; ties break by smallest internal volume, then
    name. Remaining fitting boxes are returned as ``alternatives`` in the same
    order. If nothing fits, an explained no-fit ``Recommendation`` is returned.
    """
    if not items:
        raise ValueError("Cannot recommend a box for an order with no items.")

    fitting = [box for box in boxes if order_fits_box(items, box)]
    if not fitting:
        return Recommendation(
            fit_found=False, recommended=None, alternatives=(), reason=_NO_FIT_REASON
        )

    ranked = sorted(fitting, key=lambda box: (box.cost, box.inner_volume_cm3, box.name))
    evaluations = [_evaluate(items, box) for box in ranked]
    return Recommendation(
        fit_found=True,
        recommended=evaluations[0],
        alternatives=tuple(evaluations[1:]),
        reason="",
    )
