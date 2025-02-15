from django.contrib import admin
from .models import Category, Product, Cart, Order, OrderItem, Payment, Refund, Review

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("id", "name")
    search_fields = ("name",)

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "seller", "price", "stock", "category", "created_at")
    list_filter = ("category", "seller")
    search_fields = ("title", "seller__username", "category__name")
    ordering = ("-created_at",)

@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "product", "quantity", "added_at")
    search_fields = ("user__username", "product__title")
    list_filter = ("added_at",)

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "total_price", "status", "created_at", "tracking_id")
    list_filter = ("status", "created_at")
    search_fields = ("user__username", "tracking_id")
    ordering = ("-created_at",)

@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ("id", "order", "product", "quantity")
    search_fields = ("order__id", "product__title")

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ("id", "order", "amount", "status", "transaction_id", "created_at")
    list_filter = ("status",)
    search_fields = ("order__id", "transaction_id", "reference")

@admin.register(Refund)
class RefundAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "order", "status", "created_at")
    list_filter = ("status",)
    search_fields = ("user__username", "order__id")

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "product", "rating", "created_at")
    list_filter = ("rating",)
    search_fields = ("user__username", "product__title")

