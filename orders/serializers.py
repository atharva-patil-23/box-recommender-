"""Request/response serializers for the order recommendation endpoint."""

from __future__ import annotations

from typing import Any

from rest_framework import serializers

from inventory.models import Product

# Guards against absurd inputs that would balloon the volume/weight arithmetic.
MAX_QUANTITY = 10_000


class OrderItemInputSerializer(serializers.Serializer[Any]):
    product_id = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.all(), source="product"
    )
    quantity = serializers.IntegerField(min_value=1, max_value=MAX_QUANTITY)


class OrderCreateSerializer(serializers.Serializer[Any]):
    items = OrderItemInputSerializer(many=True, allow_empty=False)

    def validate_items(self, value: list[dict[str, Any]]) -> list[dict[str, Any]]:
        product_ids = [item["product"].pk for item in value]
        if len(product_ids) != len(set(product_ids)):
            raise serializers.ValidationError(
                "Duplicate products in order; combine each into one line with a higher quantity."
            )
        return value
