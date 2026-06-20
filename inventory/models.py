from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models

# Lengths in cm, weight in grams, cost in money — all positive, two decimal places.
_POSITIVE = [MinValueValidator(Decimal("0.01"))]


class Product(models.Model):
    """A sellable item with physical dimensions (cm) and weight (grams)."""

    name = models.CharField(max_length=200, unique=True)
    length_cm = models.DecimalField(max_digits=8, decimal_places=2, validators=_POSITIVE)
    width_cm = models.DecimalField(max_digits=8, decimal_places=2, validators=_POSITIVE)
    height_cm = models.DecimalField(max_digits=8, decimal_places=2, validators=_POSITIVE)
    weight_g = models.DecimalField(max_digits=10, decimal_places=2, validators=_POSITIVE)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name

    @property
    def volume_cm3(self) -> Decimal:
        return self.length_cm * self.width_cm * self.height_cm


class Box(models.Model):
    """A shipping box with internal dimensions (cm), weight capacity (g) and cost."""

    name = models.CharField(max_length=200, unique=True)
    inner_length_cm = models.DecimalField(max_digits=8, decimal_places=2, validators=_POSITIVE)
    inner_width_cm = models.DecimalField(max_digits=8, decimal_places=2, validators=_POSITIVE)
    inner_height_cm = models.DecimalField(max_digits=8, decimal_places=2, validators=_POSITIVE)
    max_weight_g = models.DecimalField(max_digits=10, decimal_places=2, validators=_POSITIVE)
    cost = models.DecimalField(
        max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal("0.00"))]
    )

    class Meta:
        ordering = ["cost", "name"]
        verbose_name_plural = "boxes"

    def __str__(self) -> str:
        return f"{self.name} (${self.cost})"

    @property
    def inner_volume_cm3(self) -> Decimal:
        return self.inner_length_cm * self.inner_width_cm * self.inner_height_cm
