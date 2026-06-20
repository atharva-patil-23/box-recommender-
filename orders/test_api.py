"""Integration tests for the order recommendation endpoint and service."""

from decimal import Decimal

import pytest
from rest_framework import status
from rest_framework.test import APIClient

from inventory.models import Box, Product
from orders.models import Order

URL = "/api/orders/"


@pytest.fixture
def client() -> APIClient:
    return APIClient()


@pytest.fixture
def product() -> Product:
    return Product.objects.create(
        name="Mug",
        length_cm=Decimal("10"),
        width_cm=Decimal("8"),
        height_cm=Decimal("12"),
        weight_g=Decimal("350"),
    )


@pytest.fixture
def boxes() -> list[Box]:
    return [
        Box.objects.create(
            name="Small",
            inner_length_cm=Decimal("12"),
            inner_width_cm=Decimal("10"),
            inner_height_cm=Decimal("14"),
            max_weight_g=Decimal("2000"),
            cost=Decimal("1.00"),
        ),
        Box.objects.create(
            name="Large",
            inner_length_cm=Decimal("40"),
            inner_width_cm=Decimal("40"),
            inner_height_cm=Decimal("40"),
            max_weight_g=Decimal("20000"),
            cost=Decimal("5.00"),
        ),
    ]


@pytest.mark.django_db
def test_recommends_cheapest_fitting_box_and_persists_order(
    client: APIClient, product: Product, boxes: list[Box]
) -> None:
    payload = {"items": [{"product_id": product.pk, "quantity": 1}]}
    response = client.post(URL, payload, format="json")

    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["fit_found"] is True
    assert data["recommended_box"]["name"] == "Small"
    assert data["recommended_box"]["cost"] == "1.00"
    assert data["reason"] is None
    # Utilisation metrics: 960 cm3 / 1680 cm3 volume, 350 g / 2000 g weight.
    assert data["recommended_box"]["utilisation"] == {"volume_pct": 57.1, "weight_pct": 17.5}
    # The bigger box is a ranked alternative.
    assert [alt["name"] for alt in data["alternatives"]] == ["Large"]

    order = Order.objects.get(pk=data["order_id"])
    assert order.fit_found is True
    assert order.recommended_box is not None
    assert order.recommended_box.name == "Small"
    assert order.items.count() == 1


@pytest.mark.django_db
def test_returns_no_fit_when_order_too_large(client: APIClient, boxes: list[Box]) -> None:
    giant = Product.objects.create(
        name="Wardrobe",
        length_cm=Decimal("200"),
        width_cm=Decimal("60"),
        height_cm=Decimal("60"),
        weight_g=Decimal("50000"),
    )
    payload = {"items": [{"product_id": giant.pk, "quantity": 1}]}
    response = client.post(URL, payload, format="json")

    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["fit_found"] is False
    assert data["recommended_box"] is None
    assert "No available box" in data["reason"]

    order = Order.objects.get(pk=data["order_id"])
    assert order.fit_found is False
    assert order.recommended_box is None


@pytest.mark.django_db
def test_rejects_empty_items(client: APIClient) -> None:
    response = client.post(URL, {"items": []}, format="json")
    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
def test_rejects_unknown_product(client: APIClient) -> None:
    response = client.post(URL, {"items": [{"product_id": 9999, "quantity": 1}]}, format="json")
    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
def test_rejects_zero_quantity(client: APIClient, product: Product) -> None:
    payload = {"items": [{"product_id": product.pk, "quantity": 0}]}
    response = client.post(URL, payload, format="json")
    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
def test_rejects_quantity_above_max(client: APIClient, product: Product) -> None:
    payload = {"items": [{"product_id": product.pk, "quantity": 10_001}]}
    response = client.post(URL, payload, format="json")
    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
def test_rejects_duplicate_products(client: APIClient, product: Product) -> None:
    payload = {
        "items": [
            {"product_id": product.pk, "quantity": 1},
            {"product_id": product.pk, "quantity": 2},
        ]
    }
    response = client.post(URL, payload, format="json")
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "Duplicate products" in str(response.json())
