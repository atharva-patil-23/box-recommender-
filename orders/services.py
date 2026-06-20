"""Application service: the single place where the ORM meets the pure core.

It maps stored ``Product``/``Box`` rows into the framework-free dataclasses the
selection engine understands, runs the recommendation, and persists the result
onto the order. Views stay thin and the engine stays Django-free.
"""

from __future__ import annotations

from dataclasses import dataclass

from django.db import transaction

from inventory.models import Box, Product
from orders.models import Order, OrderItem
from selection.engine import recommend_box
from selection.types import BoxSpec, Dimensions, Item, Recommendation


@dataclass(frozen=True)
class OrderLine:
    """One validated line of an incoming order."""

    product: Product
    quantity: int


def _to_item(line: OrderLine) -> Item:
    product = line.product
    return Item(
        dimensions=Dimensions(product.length_cm, product.width_cm, product.height_cm),
        weight_g=product.weight_g,
        quantity=line.quantity,
    )


def _to_box_spec(box: Box) -> BoxSpec:
    return BoxSpec(
        id=box.pk,
        name=box.name,
        dimensions=Dimensions(box.inner_length_cm, box.inner_width_cm, box.inner_height_cm),
        max_weight_g=box.max_weight_g,
        cost=box.cost,
    )


@transaction.atomic
def create_order_with_recommendation(lines: list[OrderLine]) -> tuple[Order, Recommendation]:
    """Persist the order, compute the box recommendation, and store the outcome."""
    order = Order.objects.create()
    OrderItem.objects.bulk_create(
        [OrderItem(order=order, product=line.product, quantity=line.quantity) for line in lines]
    )

    items = [_to_item(line) for line in lines]
    boxes = [_to_box_spec(box) for box in Box.objects.all()]
    recommendation = recommend_box(items, boxes)

    order.fit_found = recommendation.fit_found
    order.recommended_box_id = (
        recommendation.recommended.box.id if recommendation.recommended else None
    )
    order.save(update_fields=["fit_found", "recommended_box"])

    return order, recommendation
