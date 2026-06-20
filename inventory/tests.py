from decimal import Decimal

import pytest
from django.core.management import call_command

from inventory.models import Box, Product


@pytest.mark.django_db
def test_product_volume_and_str() -> None:
    product = Product.objects.create(
        name="Mug",
        length_cm=Decimal("10"),
        width_cm=Decimal("8"),
        height_cm=Decimal("12"),
        weight_g=Decimal("350"),
    )
    assert product.volume_cm3 == Decimal("960")
    assert str(product) == "Mug"


@pytest.mark.django_db
def test_box_volume_and_str() -> None:
    box = Box.objects.create(
        name="Medium",
        inner_length_cm=Decimal("30"),
        inner_width_cm=Decimal("20"),
        inner_height_cm=Decimal("15"),
        max_weight_g=Decimal("5000"),
        cost=Decimal("2.50"),
    )
    assert box.inner_volume_cm3 == Decimal("9000")
    assert str(box) == "Medium ($2.50)"


@pytest.mark.django_db
def test_seed_demo_is_idempotent() -> None:
    call_command("seed_demo")
    call_command("seed_demo")  # second run must not duplicate rows
    assert Product.objects.count() == 6
    assert Box.objects.count() == 5
