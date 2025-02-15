from django.urls import path
from .views import (
    ProductCreateAPIView,
    ProductDetailAPIView,
    ProductListAPIView, 
    CartAPIView, 
    OrderAPIView, 
    PaymentAPIView,
    VerifyPaymentAPIView, 
    ListTransactionsAPIView, 
    TransactionTotalAPIView, 
    RefundAPIView
)

urlpatterns = [
    path('products/', ProductListAPIView.as_view(), name='product-list-create'),
    path('products/create/', ProductCreateAPIView.as_view(), name='product-create'),
    path('products/<int:pk>/', ProductDetailAPIView.as_view(), name='product-detail'),
    path('cart/', CartAPIView.as_view(), name='cart-detail-create'),
    path('orders/', OrderAPIView.as_view(), name='order-list-create'),
    path('payments/', PaymentAPIView.as_view(), name='payment-initiate'),
    path('payments/verify/<str:reference>/', VerifyPaymentAPIView.as_view(), name='payment-verify'),
    path('transactions/', ListTransactionsAPIView.as_view(), name='transaction-list'),
    path('transactions/total/', TransactionTotalAPIView.as_view(), name='transaction-total'),
    path('refunds/', RefundAPIView.as_view(), name='refund-request'),
]
