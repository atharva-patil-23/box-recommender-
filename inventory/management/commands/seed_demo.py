"""Seed a realistic catalogue of products and shipping boxes for demos/dev.

Idempotent: re-running updates the canonical rows rather than duplicating them.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from django.core.management.base import BaseCommand

from inventory.models import Box, Product

# name, length_cm, width_cm, height_cm, weight_g
PRODUCTS: list[tuple[str, str, str, str, str]] = [
    ("Phone", "16", "8", "1", "200"),
    ("Mug", "12", "9", "10", "400"),
    ("Book", "24", "17", "4", "800"),
    ("Shoes", "32", "20", "12", "1300"),
    ("Lamp", "45", "28", "28", "3000"),
    ("Monitor", "62", "42", "14", "6500"),
]

# name, inner_length_cm, inner_width_cm, inner_height_cm, max_weight_g, cost
BOXES: list[tuple[str, str, str, str, str, str]] = [
    ("Envelope", "25", "18", "3", "500", "0.50"),
    ("Small", "22", "16", "10", "2000", "1.20"),
    ("Medium", "35", "25", "18", "8000", "2.50"),
    ("Large", "50", "40", "30", "20000", "5.00"),
    ("XLarge", "70", "50", "45", "40000", "9.00"),
]


class Command(BaseCommand):
    help = "Seed the database with demo products and shipping boxes (idempotent)."

    def handle(self, *args: Any, **options: Any) -> None:
        for name, length, width, height, weight in PRODUCTS:
            Product.objects.update_or_create(
                name=name,
                defaults={
                    "length_cm": Decimal(length),
                    "width_cm": Decimal(width),
                    "height_cm": Decimal(height),
                    "weight_g": Decimal(weight),
                },
            )

        for name, length, width, height, max_weight, cost in BOXES:
            Box.objects.update_or_create(
                name=name,
                defaults={
                    "inner_length_cm": Decimal(length),
                    "inner_width_cm": Decimal(width),
                    "inner_height_cm": Decimal(height),
                    "max_weight_g": Decimal(max_weight),
                    "cost": Decimal(cost),
                },
            )

        self.stdout.write(
            self.style.SUCCESS(f"Seeded {len(PRODUCTS)} products and {len(BOXES)} boxes.")
        )
