from django.contrib import admin

from .models import Box, Product


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin[Product]):
    list_display = ("name", "length_cm", "width_cm", "height_cm", "weight_g")
    search_fields = ("name",)


@admin.register(Box)
class BoxAdmin(admin.ModelAdmin[Box]):
    list_display = (
        "name",
        "inner_length_cm",
        "inner_width_cm",
        "inner_height_cm",
        "max_weight_g",
        "cost",
    )
    search_fields = ("name",)
    ordering = ("cost",)
