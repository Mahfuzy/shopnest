from django.urls import path
from .views import (
    ProductAPIView, CartAPIView, OrderAPIView, PaymentAPIView, VerifyPaymentAPIView, RefundAPIView
)

urlpatterns = [
    path('products/', ProductAPIView.as_view(), name='product-list-create'),
    path('cart/', CartAPIView.as_view(), name='cart-detail'),
    path('orders/', OrderAPIView.as_view(), name='order-list-create'),
    path('payments/', PaymentAPIView.as_view(), name='payment-create'),
    path('payments/verify/<str:reference>/', VerifyPaymentAPIView.as_view(), name='payment-verify'),
    path('refunds/', RefundAPIView.as_view(), name='refund-create'),
]
