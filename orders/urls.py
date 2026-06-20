from django.urls import path

from orders.api import OrderRecommendationView

app_name = "orders"

urlpatterns = [
    path("orders/", OrderRecommendationView.as_view(), name="order-create"),
]
