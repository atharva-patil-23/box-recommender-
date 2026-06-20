"""Thin HTTP layer: validate input, delegate to the service, shape the response."""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from orders.serializers import OrderCreateSerializer
from orders.services import OrderLine, create_order_with_recommendation
from selection.types import BoxEvaluation


def _percentage(ratio: Decimal) -> float:
    """A utilisation ratio (0..1) as a percentage rounded to one decimal place."""
    return float((ratio * 100).quantize(Decimal("0.1")))


def _box_payload(evaluation: BoxEvaluation) -> dict[str, Any]:
    box = evaluation.box
    return {
        "id": box.id,
        "name": box.name,
        "cost": str(box.cost),
        "utilisation": {
            "volume_pct": _percentage(evaluation.volume_utilisation),
            "weight_pct": _percentage(evaluation.weight_utilisation),
        },
    }


class OrderRecommendationView(APIView):
    """POST an order's items, get back the recommended shipping box."""

    def post(self, request: Request) -> Response:
        serializer = OrderCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        lines = [
            OrderLine(product=item["product"], quantity=item["quantity"])
            for item in serializer.validated_data["items"]
        ]
        order, recommendation = create_order_with_recommendation(lines)

        recommended = recommendation.recommended
        body: dict[str, Any] = {
            "order_id": order.pk,
            "fit_found": recommendation.fit_found,
            "reason": recommendation.reason or None,
            "recommended_box": _box_payload(recommended) if recommended else None,
            "alternatives": [
                _box_payload(evaluation) for evaluation in recommendation.alternatives
            ],
        }
        return Response(body, status=status.HTTP_201_CREATED)
