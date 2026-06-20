from django.contrib import admin

from .models import Order, OrderItem


class OrderItemInline(admin.TabularInline[OrderItem, Order]):
    model = OrderItem
    extra = 1


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin[Order]):
    list_display = ("id", "created_at", "recommended_box", "fit_found")
    list_filter = ("fit_found",)
    inlines = [OrderItemInline]
    readonly_fields = ("created_at",)
