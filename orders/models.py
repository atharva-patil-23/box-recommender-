from django.core.validators import MinValueValidator
from django.db import models

from inventory.models import Box, Product


class Order(models.Model):
    """A customer order: a set of line items plus the recommended shipping box.

    ``recommended_box`` and ``fit_found`` are populated by the recommendation
    service once the order is created.
    """

    created_at = models.DateTimeField(auto_now_add=True)
    recommended_box = models.ForeignKey(
        Box,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="orders",
    )
    fit_found = models.BooleanField(default=False)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"Order #{self.pk}"


class OrderItem(models.Model):
    """A quantity of a product within an order."""

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name="order_items")
    quantity = models.PositiveIntegerField(validators=[MinValueValidator(1)])

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["order", "product"], name="unique_product_per_order"),
        ]

    def __str__(self) -> str:
        return f"{self.quantity} x {self.product.name}"
