from decimal import Decimal

import pytest

from inventory.models import Box, Product
from orders.models import Order, OrderItem


@pytest.mark.django_db
def test_order_and_item_str() -> None:
    product = Product.objects.create(
        name="Mug",
        length_cm=Decimal("10"),
        width_cm=Decimal("8"),
        height_cm=Decimal("12"),
        weight_g=Decimal("350"),
    )
    box = Box.objects.create(
        name="Medium",
        inner_length_cm=Decimal("30"),
        inner_width_cm=Decimal("20"),
        inner_height_cm=Decimal("15"),
        max_weight_g=Decimal("5000"),
        cost=Decimal("2.50"),
    )
    order = Order.objects.create(recommended_box=box, fit_found=True)
    item = OrderItem.objects.create(order=order, product=product, quantity=3)

    assert str(order) == f"Order #{order.pk}"
    assert str(item) == "3 x Mug"
    assert list(order.items.all()) == [item]
