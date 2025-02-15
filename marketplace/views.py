from django.conf import settings
from django.db.models import Sum
from django.shortcuts import get_object_or_404
import requests
from rest_framework import views, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from marketplace.models import Category, Payment, Product
from marketplace.serializers import (
    CategorySerializer, ProductSerializer, CartSerializer, OrderSerializer, PaymentSerializer, 
    RefundSerializer, Cart, Order, ReviewSerializer
)

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
    @swagger_auto_schema(request_body=PaymentSerializer, responses={201: "Payment URL generated"})
    def post(self, request):
        """Initialize a new payment with Paystack."""
        serializer = PaymentSerializer(data=request.data)
        if serializer.is_valid():
            order = serializer.validated_data["order"]
            amount = serializer.validated_data["amount"]
            
            headers = {
                "Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}",
                "Content-Type": "application/json"
            }
            data = {
                "email": request.user.email,
                "amount": amount,
                "currency": "GHS",
                "reference": f"{order.id}-{request.user.id}",
            }
            response = requests.post("https://api.paystack.co/transaction/initialize", json=data, headers=headers)
            res_data = response.json()
            
            if response.status_code == 200:
                serializer.save(reference=res_data['data']['reference'])
                return Response({"payment_url": res_data['data']['authorization_url']}, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
class ReviewAPIView(views.APIView):
    """
    API endpoint for creating a review.
    """
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        request_body=ReviewSerializer,  # ✅ Adds the serializer for request body in Swagger
        responses={
            201: openapi.Response("Review created successfully", ReviewSerializer),
            400: "Review creation failed"
        }
    )
    def post(self, request):
        serializer = ReviewSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response(
                {"message": "Review created successfully", "data": serializer.data}, 
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
class VerifyPaymentAPIView(views.APIView):
    permission_classes = [IsAuthenticated]
    """
    API endpoint for verifying a payment.
    """
    @swagger_auto_schema(responses={200: "Payment verified successfully", 400: "Payment verification failed"})
    def get(self, request, reference):
        """Verify a Paystack payment."""
        url = f"https://api.paystack.co/transaction/verify/{reference}"
        headers = {"Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}"}
        response = requests.get(url, headers=headers)
        res_data = response.json()
        
        if res_data["status"] and res_data["data"]["status"] == "success":
            order = Order.objects.get(id=int(reference.split("-")[0]))
            order.status = "Paid"
            order.save()
            
            payment = Payment.objects.get(reference=reference)
            payment.status = "Completed"
            payment.transaction_id = res_data["data"]["id"]
            payment.save()
            return Response({"message": "Payment verified successfully"}, status=status.HTTP_200_OK)
        return Response({"message": "Payment verification failed"}, status=status.HTTP_400_BAD_REQUEST)

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
