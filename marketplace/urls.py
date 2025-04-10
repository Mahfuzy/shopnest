from django.urls import path
from marketplace.views import (
    CategoryListAPIView, ProductListAPIView, ProductCreateAPIView, ProductDetailAPIView,
    CartAPIView, OrderAPIView, PaymentAPIView, ReviewAPIView, VerifyPaymentAPIView,
    TransactionTotalAPIView, ListTransactionsAPIView, RefundAPIView, PaystackWebhookView
)

urlpatterns = [
    path("categories/", CategoryListAPIView.as_view(), name="category-list"),
    path("products/", ProductListAPIView.as_view(), name="product-list"),
    path("products/create/", ProductCreateAPIView.as_view(), name="product-create"),
    path("products/<int:product_id>/", ProductDetailAPIView.as_view(), name="product-detail"),
    path("cart/", CartAPIView.as_view(), name="cart"),
    path("orders/", OrderAPIView.as_view(), name="orders"),
    path("payments/", PaymentAPIView.as_view(), name="payment"),
    path("payments/verify/<str:reference>/", VerifyPaymentAPIView.as_view(), name="verify-payment"),
    path("payments/webhook/", PaystackWebhookView.as_view(), name="paystack-webhook"),
    path("reviews/", ReviewAPIView.as_view(), name="reviews"),
    path("transactions/total/", TransactionTotalAPIView.as_view(), name="transaction-total"),
    path("transactions/list/", ListTransactionsAPIView.as_view(), name="transaction-list"),
    path("refunds/", RefundAPIView.as_view(), name="refunds"),
]
