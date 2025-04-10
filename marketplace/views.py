from django.conf import settings
from django.db.models import Sum
from django.shortcuts import get_object_or_404
import requests
from rest_framework import views, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
import logging
from django.db import transaction
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
import hmac
import hashlib
import json
from django.utils import timezone

from marketplace.models import Category, Payment, Product, Review
from marketplace.serializers import (
    CategorySerializer, ProductSerializer, CartSerializer, OrderSerializer, PaymentSerializer, 
    RefundSerializer, Cart, Order, ReviewSerializer
)

logger = logging.getLogger(__name__)

class CategoryListAPIView(views.APIView):
    permission_classes = [AllowAny]
    """
    API endpoint for retrieving all categories.
    """
    @swagger_auto_schema(responses={200: CategorySerializer(many=True)})
    def get(self, request):
        """Retrieve all categories."""
        ...
        categories = Category.objects.all()
        serializer = CategorySerializer(categories, many=True)
        return Response(serializer.data)

class ProductListAPIView(views.APIView):
    """
    API endpoint to list products, optionally filtered by category and searchable by name.
    """
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        operation_description="Retrieve a list of products. Optionally filter by category and search by name.",
        manual_parameters=[
            openapi.Parameter(
                'category',
                openapi.IN_QUERY,
                description="Filter products by category ID",
                type=openapi.TYPE_INTEGER
            ),
            openapi.Parameter(
                'search',
                openapi.IN_QUERY,
                description="Search for products by name",
                type=openapi.TYPE_STRING
            )
        ],
        responses={200: ProductSerializer(many=True)}
    )
    def get(self, request):
        category_id = request.GET.get("category")
        search_query = request.GET.get("search")
        products = Product.objects.all()

        if category_id:
            products = products.filter(category_id=category_id)
        
        if search_query:
            products = products.filter(name__icontains=search_query)

        serializer = ProductSerializer(products, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
class ProductCreateAPIView(views.APIView):
    """
    API endpoint for creating a new product.
    """
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(request_body=ProductSerializer, responses={201: "Product created", 400: "Bad request"})
    def post(self, request):
        serializer = ProductSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(seller=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
class ProductDetailAPIView(views.APIView):
    """
    API endpoint for retrieving, updating, and deleting a product.
    """
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(responses={200: ProductSerializer()})
    def get(self, request, product_id):
        """Retrieve product details by ID."""
        product = get_object_or_404(Product, id=product_id)
        serializer = ProductSerializer(product)
        return Response(serializer.data)

    @swagger_auto_schema(request_body=ProductSerializer, responses={200: "Product updated", 400: "Bad request"})
    def put(self, request, product_id):
        """Update product details (only seller can update)."""
        product = get_object_or_404(Product, id=product_id, seller=request.user)
        serializer = ProductSerializer(product, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(responses={204: "Product deleted", 403: "Unauthorized"})
    def delete(self, request, product_id):
        """Delete a product (only seller can delete)."""
        product = get_object_or_404(Product, id=product_id, seller=request.user)
        product.delete()
        return Response({"detail": "Product deleted"}, status=status.HTTP_204_NO_CONTENT)
    

class CartAPIView(views.APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(responses={200: CartSerializer})
    def get(self, request):
        """Retrieve the current user's cart."""
        cart, created = Cart.objects.get_or_create(user=request.user)
        serializer = CartSerializer(cart)
        return Response(serializer.data)

    @swagger_auto_schema(request_body=CartSerializer, responses={201: CartSerializer})
    def post(self, request):
        """Add an item to the cart."""
        serializer = CartSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(request_body=CartSerializer, responses={200: CartSerializer})
    def put(self, request):
        """Update the quantity of a cart item."""
        cart = get_object_or_404(Cart, user=request.user)
        serializer = CartSerializer(cart, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter('product_id', openapi.IN_QUERY, type=openapi.TYPE_INTEGER, description="ID of the product to remove")
        ],
        responses={204: "Item removed", 400: "Bad request"}
    )
    def delete(self, request):
        """Remove an item from the cart."""
        product_id = request.GET.get("product_id")
        cart = get_object_or_404(Cart, user=request.user)
        cart.products.remove(product_id)
        cart.save()
        return Response({"detail": "Item removed"}, status=status.HTTP_204_NO_CONTENT)
    
class OrderAPIView(views.APIView):
    permission_classes = [IsAuthenticated]
    """
    API endpoint for retrieving and placing orders.
    """
    @swagger_auto_schema(responses={200: OrderSerializer(many=True)})
    def get(self, request):
        """Retrieve all orders of the current user."""
        orders = Order.objects.filter(user=request.user)
        serializer = OrderSerializer(orders, many=True)
        return Response(serializer.data)
    
    @swagger_auto_schema(request_body=OrderSerializer, responses={201: OrderSerializer})
    def post(self, request):
        """Place a new order."""
        serializer = OrderSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class PaymentAPIView(views.APIView):
    permission_classes = [IsAuthenticated]
    """
    API endpoint for initiating a payment.
    """
    @swagger_auto_schema(
        request_body=PaymentSerializer,
        responses={
            201: "Payment URL generated",
            400: "Invalid request",
            503: "Payment service unavailable"
        }
    )
    def post(self, request):
        """Initialize a new payment with Paystack."""
        try:
            serializer = PaymentSerializer(data=request.data)
            if serializer.is_valid():
                order = serializer.validated_data["order"]
                amount = serializer.validated_data["amount"]
                currency = serializer.validated_data.get("currency", "GHS")
                payment_method = serializer.validated_data.get("payment_method", "card")
                
                # Check if payment already exists for this order
                if Payment.objects.filter(order=order).exists():
                    return Response(
                        {"error": "Payment already exists for this order"},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                headers = {
                    "Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}",
                    "Content-Type": "application/json"
                }
                
                # Base payment data
                data = {
                    "email": request.user.email,
                    "amount": int(amount * 100),  # Convert to kobo/pesewas
                    "currency": currency,
                    "reference": f"{order.id}-{request.user.id}",
                    "metadata": {
                        "order_id": order.id,
                        "user_id": request.user.id,
                        "payment_method": payment_method
                    }
                }
                
                # Add payment method specific data
                if payment_method == "mobile_money":
                    data["channels"] = ["mobile_money"]
                elif payment_method == "bank_transfer":
                    data["channels"] = ["bank_transfer"]
                elif payment_method == "ussd":
                    data["channels"] = ["ussd"]
                elif payment_method == "qr":
                    data["channels"] = ["qr"]
                
                try:
                    response = requests.post(
                        "https://api.paystack.co/transaction/initialize",
                        json=data,
                        headers=headers,
                        timeout=30
                    )
                    
                    if response.status_code != 200:
                        logger.error(f"Paystack API returned error: {response.status_code} - {response.text}")
                        return Response(
                            {"error": "Payment service temporarily unavailable. Please try again later."},
                            status=status.HTTP_503_SERVICE_UNAVAILABLE
                        )
                        
                    res_data = response.json()
                    
                    with transaction.atomic():
                        payment = serializer.save(
                            reference=res_data['data']['reference'],
                            status='Pending',
                            currency=currency,
                            payment_method=payment_method,
                            metadata={
                                "payment_url": res_data['data']['authorization_url'],
                                "payment_method": payment_method,
                                "currency": currency
                            }
                        )
                        logger.info(
                            f"Payment initialized - Order: {order.id}, "
                            f"Amount: {amount} {currency}, "
                            f"Method: {payment_method}, "
                            f"Reference: {res_data['data']['reference']}"
                        )
                        return Response(
                            {
                                "payment_url": res_data['data']['authorization_url'],
                                "payment_method": payment_method,
                                "currency": currency
                            },
                            status=status.HTTP_201_CREATED
                        )
                except requests.exceptions.RequestException as e:
                    logger.error(f"Paystack API request failed: {str(e)}")
                    return Response(
                        {"error": "Payment service temporarily unavailable. Please try again later."},
                        status=status.HTTP_503_SERVICE_UNAVAILABLE
                    )
                except requests.exceptions.Timeout:
                    logger.error("Paystack API request timed out")
                    return Response(
                        {"error": "Payment service timed out. Please try again."},
                        status=status.HTTP_504_GATEWAY_TIMEOUT
                    )
            
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Unexpected error in payment initialization: {str(e)}")
            return Response(
                {"error": "An unexpected error occurred. Please try again later."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class ReviewAPIView(views.APIView):
    """
    API endpoint for creating and retrieving reviews.
    """
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        request_body=ReviewSerializer,
        responses={
            201: openapi.Response("Review created successfully", ReviewSerializer),
            400: "Review creation failed"
        }
    )
    def post(self, request):
        """Create a new review."""
        serializer = ReviewSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(
        responses={200: ReviewSerializer(many=True)}
    )
    def get(self, request):
        """Retrieve all reviews."""
        reviews = Review.objects.all()
        serializer = ReviewSerializer(reviews, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

class VerifyPaymentAPIView(views.APIView):
    permission_classes = [IsAuthenticated]
    """
    API endpoint for verifying a payment.
    """
    @swagger_auto_schema(responses={200: "Payment verified successfully", 400: "Payment verification failed"})
    def get(self, request, reference):
        """Verify a Paystack payment."""
        try:
            url = f"https://api.paystack.co/transaction/verify/{reference}"
            headers = {"Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}"}
            
            try:
                response = requests.get(url, headers=headers, timeout=30)
                response.raise_for_status()
                res_data = response.json()
                
                if not res_data.get("status"):
                    logger.warning(f"Paystack verification failed - Reference: {reference}")
                    return Response(
                        {"status": "failed", "message": "Payment verification failed"},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                if res_data["data"]["status"] == "success":
                    with transaction.atomic():
                        try:
                            # Get payment first to avoid order reference parsing issues
                            payment = Payment.objects.get(reference=reference)
                            order = payment.order
                            
                            order.status = "Paid"
                            order.save()
                            
                            payment.status = "Completed"
                            payment.transaction_id = res_data["data"]["id"]
                            payment.save()
                            
                            logger.info(
                                f"Payment verified successfully - Order: {order.id}, "
                                f"Transaction ID: {res_data['data']['id']}"
                            )
                            return Response(
                                {"status": "success", "message": "Payment verified successfully"},
                                status=status.HTTP_200_OK
                            )
                        except (Order.DoesNotExist, Payment.DoesNotExist) as e:
                            logger.error(f"Payment verification failed - {str(e)}")
                            return Response(
                                {"status": "failed", "message": "Payment or order not found"},
                                status=status.HTTP_404_NOT_FOUND
                            )
                else:
                    logger.warning(
                        f"Payment verification failed - Reference: {reference}, "
                        f"Status: {res_data.get('data', {}).get('status')}"
                    )
                    return Response(
                        {"status": "failed", "message": "Payment verification failed"},
                        status=status.HTTP_400_BAD_REQUEST
                    )
            except requests.exceptions.RequestException as e:
                logger.error(f"Paystack verification request failed: {str(e)}")
                return Response(
                    {"error": "Payment verification service temporarily unavailable"},
                    status=status.HTTP_503_SERVICE_UNAVAILABLE
                )
        except Exception as e:
            logger.error(f"Unexpected error in payment verification: {str(e)}")
            return Response(
                {"error": "An unexpected error occurred during payment verification"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class TransactionTotalAPIView(views.APIView):
    permission_classes = [IsAuthenticated]
    """
    API endpoint for retrieving the total transaction amount.
    """
    @swagger_auto_schema(responses={200: "Total transaction amount."})
    def get(self, request):
        """Retrieve total transactions amount of the user."""
        user = request.user
        total = Payment.objects.filter(user=user).aggregate(total=Sum("amount"))["total"]
        return Response({"total": total}, status=status.HTTP_200_OK)
    
class ListTransactionsAPIView(views.APIView):
    permission_classes = [IsAuthenticated]
    
    
    @swagger_auto_schema(
        operation_description="Retrieve a list of all transactions (payments) made by the authenticated user.",
        responses={200: PaymentSerializer(many=True)},
        tags=["Transactions"]
    )
    
    def get(self, request):
        user = request.user
        transactions = Payment.objects.filter(order__user=user)
        serializer = PaymentSerializer(transactions, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    

class RefundAPIView(views.APIView):
    permission_classes = [IsAuthenticated]
    """
    API endpoint for processing refunds.
    """
    @swagger_auto_schema(request_body=RefundSerializer, responses={201: RefundSerializer})
    def post(self, request):
        """Request a refund."""
        serializer = RefundSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@method_decorator(csrf_exempt, name='dispatch')
class PaystackWebhookView(views.APIView):
    """
    API endpoint for handling Paystack webhook notifications.
    """
    permission_classes = []  # No authentication required for webhooks
    
    def verify_signature(self, payload, signature):
        """Verify the webhook signature from Paystack."""
        if not signature:
            return False
        
        expected_signature = hmac.new(
            settings.PAYSTACK_SECRET_KEY.encode('utf-8'),
            payload,
            hashlib.sha512
        ).hexdigest()
        
        return hmac.compare_digest(expected_signature, signature)
    
    def post(self, request):
        """Handle Paystack webhook notifications."""
        try:
            # Get the signature from the header
            signature = request.headers.get('x-paystack-signature')
            
            # Verify the signature
            if not self.verify_signature(request.body, signature):
                logger.warning("Invalid webhook signature received")
                return Response(
                    {"error": "Invalid signature"},
                    status=status.HTTP_401_UNAUTHORIZED
                )
            
            # Parse the webhook payload
            payload = json.loads(request.body)
            event = payload.get('event')
            data = payload.get('data')
            
            if event == 'charge.success':
                # Handle successful payment
                reference = data.get('reference')
                try:
                    with transaction.atomic():
                        payment = Payment.objects.get(reference=reference)
                        payment.status = 'Completed'
                        payment.transaction_id = data.get('id')
                        payment.metadata.update({
                            'webhook_data': data,
                            'webhook_received_at': timezone.now().isoformat()
                        })
                        payment.save()
                        
                        order = payment.order
                        order.status = 'Paid'
                        order.save()
                        
                        logger.info(
                            f"Payment completed via webhook - Order: {order.id}, "
                            f"Transaction ID: {data.get('id')}"
                        )
                except Payment.DoesNotExist:
                    logger.error(f"Payment not found for reference: {reference}")
                    return Response(
                        {"error": "Payment not found"},
                        status=status.HTTP_404_NOT_FOUND
                    )
            
            elif event == 'charge.failed':
                # Handle failed payment
                reference = data.get('reference')
                try:
                    payment = Payment.objects.get(reference=reference)
                    payment.status = 'Failed'
                    payment.metadata.update({
                        'webhook_data': data,
                        'webhook_received_at': timezone.now().isoformat(),
                        'failure_reason': data.get('message')
                    })
                    payment.save()
                    
                    logger.warning(
                        f"Payment failed via webhook - Order: {payment.order.id}, "
                        f"Reason: {data.get('message')}"
                    )
                except Payment.DoesNotExist:
                    logger.error(f"Payment not found for reference: {reference}")
            
            elif event == 'refund.processed':
                # Handle refund
                reference = data.get('reference')
                try:
                    payment = Payment.objects.get(reference=reference)
                    payment.status = 'Refunded'
                    payment.metadata.update({
                        'webhook_data': data,
                        'webhook_received_at': timezone.now().isoformat(),
                        'refund_id': data.get('id')
                    })
                    payment.save()
                    
                    logger.info(
                        f"Payment refunded via webhook - Order: {payment.order.id}, "
                        f"Refund ID: {data.get('id')}"
                    )
                except Payment.DoesNotExist:
                    logger.error(f"Payment not found for reference: {reference}")
            
            return Response({"status": "success"}, status=status.HTTP_200_OK)
            
        except json.JSONDecodeError:
            logger.error("Invalid JSON payload received in webhook")
            return Response(
                {"error": "Invalid JSON payload"},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"Error processing webhook: {str(e)}")
            return Response(
                {"error": "Internal server error"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
