"""Unit tests for the framework-free selection core. No Django, no database."""

from decimal import Decimal

import pytest

from selection.engine import (
    dimensions_fit,
    item_fits_box,
    order_fits_box,
    recommend_box,
)
from selection.types import BoxSpec, Dimensions, Item


def dims(length: str, width: str, height: str) -> Dimensions:
    return Dimensions(Decimal(length), Decimal(width), Decimal(height))


def item(length: str, width: str, height: str, weight: str, quantity: int = 1) -> Item:
    return Item(dimensions=dims(length, width, height), weight_g=Decimal(weight), quantity=quantity)


def box(
    name: str,
    length: str,
    width: str,
    height: str,
    max_weight: str,
    cost: str,
    box_id: int = 1,
) -> BoxSpec:
    return BoxSpec(
        id=box_id,
        name=name,
        dimensions=dims(length, width, height),
        max_weight_g=Decimal(max_weight),
        cost=Decimal(cost),
    )


# --- low-level geometry ------------------------------------------------------


def test_dimensions_fit_exact() -> None:
    assert dimensions_fit([Decimal("5"), Decimal("5"), Decimal("5")], [Decimal("5")] * 3)


def test_dimensions_fit_rejects_when_one_side_too_big() -> None:
    assert not dimensions_fit([Decimal("5"), Decimal("5"), Decimal("11")], [Decimal("10")] * 3)


def test_item_fits_box_allows_rotation() -> None:
    # A long thin item (30x5x5) does not fit 10x10x10 axis-aligned, but the box
    # 40x10x10 holds it once rotated — sorted-side comparison captures that.
    long_item = item("30", "5", "5", "100")
    assert item_fits_box(long_item, box("B", "10", "10", "40", "1000", "1.00"))
    assert not item_fits_box(long_item, box("B", "10", "10", "10", "1000", "1.00"))


# --- order-level fit ---------------------------------------------------------


def test_order_fits_box_happy_path() -> None:
    items = [item("10", "10", "10", "500", quantity=2)]
    assert order_fits_box(items, box("M", "30", "20", "15", "5000", "2.50"))


def test_order_rejected_when_total_volume_exceeds_box() -> None:
    # 5 units * 1000 cm3 = 5000 cm3 > box internal volume 8*8*8 = 512 cm3.
    items = [item("10", "10", "10", "10", quantity=5)]
    assert not order_fits_box(items, box("S", "8", "8", "8", "100000", "1.00"))


def test_order_rejected_when_total_weight_exceeds_capacity() -> None:
    # Fits by dimension and volume, but 3 * 2000 g = 6000 g > 5000 g capacity.
    items = [item("5", "5", "5", "2000", quantity=3)]
    assert not order_fits_box(items, box("M", "100", "100", "100", "5000", "2.50"))


def test_order_rejected_when_single_item_too_large_by_dimension() -> None:
    # Volume and weight are fine, but the item's longest side exceeds every box side.
    items = [item("50", "1", "1", "10")]
    assert not order_fits_box(items, box("Flat", "40", "40", "2", "1000", "1.00"))


# --- recommendation selection ------------------------------------------------


def test_recommend_picks_cheapest_fitting_box() -> None:
    items = [item("10", "10", "10", "500")]
    boxes = [
        box("Large", "50", "50", "50", "10000", "5.00", box_id=1),
        box("Medium", "30", "30", "30", "10000", "2.50", box_id=2),
        box("Small", "12", "12", "12", "10000", "1.00", box_id=3),
    ]
    result = recommend_box(items, boxes)
    assert result.fit_found
    assert result.recommended is not None
    assert result.recommended.box.id == 3
    assert result.recommended.box.name == "Small"
    # The other fitting boxes come back as ranked alternatives (cheapest-first).
    assert [evaluation.box.name for evaluation in result.alternatives] == ["Medium", "Large"]


def test_recommend_tie_breaks_cheapest_by_smallest_volume() -> None:
    items = [item("5", "5", "5", "100")]
    # Two boxes share the lowest cost; the smaller-volume one should win.
    boxes = [
        box("CheapBig", "40", "40", "40", "10000", "1.50", box_id=1),
        box("CheapSmall", "10", "10", "10", "10000", "1.50", box_id=2),
    ]
    result = recommend_box(items, boxes)
    assert result.recommended is not None
    assert result.recommended.box.name == "CheapSmall"


def test_recommend_tie_breaks_by_name_when_cost_and_volume_equal() -> None:
    items = [item("5", "5", "5", "100")]
    boxes = [
        box("Bravo", "10", "10", "10", "10000", "1.50", box_id=1),
        box("Alpha", "10", "10", "10", "10000", "1.50", box_id=2),
    ]
    result = recommend_box(items, boxes)
    assert result.recommended is not None
    assert result.recommended.box.name == "Alpha"


def test_recommendation_reports_utilisation() -> None:
    # Order volume 1000 cm3, weight 500 g against a 2000 cm3 / 1000 g box.
    items = [item("10", "10", "10", "500")]
    boxes = [box("Snug", "10", "10", "20", "1000", "1.00")]
    result = recommend_box(items, boxes)
    assert result.recommended is not None
    assert result.recommended.volume_utilisation == Decimal("1000") / Decimal("2000")
    assert result.recommended.weight_utilisation == Decimal("500") / Decimal("1000")


def test_recommend_returns_no_fit_when_nothing_holds_the_order() -> None:
    items = [item("100", "100", "100", "50000")]
    boxes = [box("Small", "10", "10", "10", "1000", "1.00")]
    result = recommend_box(items, boxes)
    assert not result.fit_found
    assert result.recommended is None
    assert result.alternatives == ()
    assert "No available box" in result.reason


def test_recommend_no_fit_when_box_list_is_empty() -> None:
    result = recommend_box([item("1", "1", "1", "1")], [])
    assert not result.fit_found


def test_recommend_raises_on_empty_order() -> None:
    with pytest.raises(ValueError, match="no items"):
        recommend_box([], [box("Any", "10", "10", "10", "1000", "1.00")])


def test_recommend_considers_multiple_items_together() -> None:
    items = [
        item("10", "10", "10", "500"),
        item("8", "8", "8", "300", quantity=2),
    ]
    boxes = [
        box("TooSmall", "10", "10", "10", "10000", "1.00", box_id=1),
        box("FitsAll", "30", "30", "30", "10000", "3.00", box_id=2),
    ]
    result = recommend_box(items, boxes)
    assert result.recommended is not None
    assert result.recommended.box.name == "FitsAll"
