from django.test import TestCase, Client, override_settings
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from unittest.mock import patch, MagicMock
import json
from decimal import Decimal
from django.utils import timezone
from datetime import timedelta
import hmac
import hashlib
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile

from .models import Category, Product, Order, Payment, Review, Refund
from .views import PaystackWebhookView

User = get_user_model()

@override_settings(
    PAYSTACK_SECRET_KEY='test_secret_key',
    PAYSTACK_PUBLIC_KEY='test_public_key'
)
class MarketplaceTests(TestCase):
    def setUp(self):
        # Create test users
        self.seller = User.objects.create_user(
            username='seller',
            email='seller@example.com',
            password='testpass123',
            phone_number='+233501234567',
            is_seller=True
        )
        self.buyer = User.objects.create_user(
            username='buyer',
            email='buyer@example.com',
            password='testpass123',
            phone_number='+233501234568',
            is_buyer=True
        )
        
        # Create test category
        self.category = Category.objects.create(
            name='Test Category',
            description='Test Description'
        )
        
        # Create test product
        self.product = Product.objects.create(
            seller=self.seller,
            title='Test Product',
            description='Test Description',
            price=Decimal('100.00'),
            stock=10,
            category=self.category
        )
        
        # Create test order
        self.order = Order.objects.create(
            user=self.buyer,
            total_price=Decimal('100.00'),
            status='pending'
        )
        
        # Create API clients
        self.seller_client = APIClient()
        self.seller_client.force_authenticate(user=self.seller)
        
        self.buyer_client = APIClient()
        self.buyer_client.force_authenticate(user=self.buyer)
        
        # Test data
        self.payment_data = {
            'order': self.order.id,
            'amount': '100.00',
            'currency': 'GHS',
            'payment_method': 'card'
        }
        
        # Mock Paystack response
        self.mock_paystack_response = {
            'status': True,
            'message': 'Authorization URL created',
            'data': {
                'authorization_url': 'https://checkout.paystack.com/test',
                'reference': 'test_ref_123'
            }
        }

    # Category Tests
    def test_category_creation(self):
        """Test category creation and retrieval"""
        category = Category.objects.create(
            name='New Category',
            description='New Description'
        )
        self.assertEqual(category.name, 'New Category')
        self.assertEqual(category.description, 'New Description')

    def test_category_list_api(self):
        """Test category list API endpoint"""
        response = self.buyer_client.get(reverse('category-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['name'], 'Test Category')

    # Product Tests
    def test_product_creation(self):
        """Test product creation and retrieval"""
        product = Product.objects.create(
            seller=self.seller,
            title='New Product',
            description='New Description',
            price=Decimal('50.00'),
            stock=5,
            category=self.category
        )
        self.assertEqual(product.title, 'New Product')
        self.assertEqual(product.price, Decimal('50.00'))
        self.assertEqual(product.stock, 5)

    def test_product_list_api(self):
        """Test product list API endpoint"""
        response = self.buyer_client.get(reverse('product-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['title'], 'Test Product')

    def test_product_detail_api(self):
        """Test product detail API endpoint"""
        response = self.buyer_client.get(reverse('product-detail', args=[self.product.id]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], 'Test Product')

    def test_product_update_api(self):
        """Test product update API endpoint"""
        data = {
            'title': 'Updated Product',
            'price': '150.00',
            'stock': 15
        }
        response = self.seller_client.put(
            reverse('product-detail', args=[self.product.id]),
            data=data
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.product.refresh_from_db()
        self.assertEqual(self.product.title, 'Updated Product')
        self.assertEqual(self.product.price, Decimal('150.00'))

    def test_product_delete_api(self):
        """Test product delete API endpoint"""
        response = self.seller_client.delete(
            reverse('product-detail', args=[self.product.id])
        )
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Product.objects.filter(id=self.product.id).exists())

    # Order Tests
    def test_order_creation(self):
        """Test order creation and retrieval"""
        order = Order.objects.create(
            user=self.buyer,
            total_price=Decimal('200.00'),
            status='pending'
        )
        self.assertEqual(order.user, self.buyer)
        self.assertEqual(order.total_price, Decimal('200.00'))
        self.assertEqual(order.status, 'pending')

    def test_order_list_api(self):
        """Test order list API endpoint"""
        response = self.buyer_client.get(reverse('orders'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['total_price'], '100.00')

    def test_order_detail_api(self):
        """Test order detail API endpoint"""
        response = self.buyer_client.get(reverse('orders'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data[0]['total_price'], '100.00')

    # Payment Tests
    @patch('requests.post')
    def test_payment_initialization(self, mock_post):
        """Test successful payment initialization"""
        mock_post.return_value = MagicMock(
            status_code=200,
            json=lambda: self.mock_paystack_response
        )
        
        response = self.buyer_client.post(
            reverse('payment'),
            data=self.payment_data,
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['payment_url'], 'https://checkout.paystack.com/test')
        
        payment = Payment.objects.get(reference='test_ref_123')
        self.assertEqual(payment.amount, Decimal('100.00'))
        self.assertEqual(payment.currency, 'GHS')
        self.assertEqual(payment.payment_method, 'card')
        self.assertEqual(payment.status, 'Pending')

    @patch('requests.get')
    def test_payment_verification(self, mock_get):
        """Test successful payment verification"""
        payment = Payment.objects.create(
            order=self.order,
            amount=Decimal('100.00'),
            status='Pending',
            reference='test_ref_123'
        )
        
        mock_get.return_value = MagicMock(
            status_code=200,
            json=lambda: {
                'status': True,
                'data': {
                    'status': 'success',
                    'id': 'test_transaction_123'
                }
            }
        )
        
        response = self.buyer_client.get(
            reverse('verify-payment', kwargs={'reference': 'test_ref_123'})
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        payment.refresh_from_db()
        self.assertEqual(payment.status, 'Completed')
        self.assertEqual(payment.transaction_id, 'test_transaction_123')
        
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, 'Paid')

    # Review Tests
    def test_review_creation(self):
        # Create a buyer
        buyer = User.objects.create_user(
            username='review_buyer',
            email='review_buyer@example.com',
            password='testpass123'
        )
        buyer_client = APIClient()
        buyer_client.force_authenticate(user=buyer)

        # Create a product
        product = Product.objects.create(
            title='Test Product',
            description='Test Description',
            price=10.00,
            stock=10,
            category=self.category,
            seller=self.seller
        )

        # Create a review
        response = buyer_client.post(
            reverse('reviews'),
            {
                'product': product.id,
                'user': buyer.id,
                'rating': 5,
                'comment': 'Great product!'
            }
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['rating'], 5)
        self.assertEqual(response.data['comment'], 'Great product!')

        # Try to create a review with invalid rating
        response = buyer_client.post(
            reverse('reviews'),
            {
                'product': product.id,
                'user': buyer.id,
                'rating': 6,
                'comment': 'Invalid rating'
            }
        )
        self.assertEqual(response.status_code, 400)

        # Try to create a review for non-existent product
        response = buyer_client.post(
            reverse('reviews'),
            {
                'product': 999,
                'user': buyer.id,
                'rating': 5,
                'comment': 'Non-existent product'
            }
        )
        self.assertEqual(response.status_code, 400)

    def test_review_list_api(self):
        """Test review list API endpoint"""
        Review.objects.create(
            user=self.buyer,
            product=self.product,
            rating=5,
            comment='Great product!'
        )
        
        response = self.buyer_client.get(reverse('reviews'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['rating'], 5)

    # Refund Tests
    def test_refund_creation(self):
        # Create a buyer user
        buyer = User.objects.create_user(
            username='refund_buyer',
            email='refund_buyer@example.com',
            password='testpass123'
        )
        client = APIClient()
        client.force_authenticate(user=buyer)

        # Create a refund
        refund_data = {
            'order': self.order.id,
            'user': buyer.id,
            'reason': 'Product not as described'
        }
        response = client.post(reverse('refund-list'), refund_data)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Refund.objects.count(), 1)
        refund = Refund.objects.first()
        self.assertEqual(refund.order, self.order)
        self.assertEqual(refund.user, buyer)
        self.assertEqual(refund.reason, 'Product not as described')
        self.assertEqual(refund.status, 'pending')

    # Webhook Tests
    def test_webhook_signature_verification(self):
        """Test webhook signature verification"""
        payload = json.dumps({
            'event': 'charge.success',
            'data': {
                'reference': 'test_ref_123',
                'id': 'test_transaction_123'
            }
        }).encode('utf-8')
        
        signature = hmac.new(
            settings.PAYSTACK_SECRET_KEY.encode('utf-8'),
            payload,
            hashlib.sha512
        ).hexdigest()
        
        view = PaystackWebhookView()
        self.assertTrue(view.verify_signature(payload, signature))
        self.assertFalse(view.verify_signature(payload, 'invalid_signature'))

    @patch('requests.get')
    def test_webhook_processing(self, mock_get):
        """Test webhook processing"""
        payment = Payment.objects.create(
            order=self.order,
            amount=Decimal('100.00'),
            status='Pending',
            reference='test_ref_123'
        )
        
        payload = {
            'event': 'charge.success',
            'data': {
                'reference': 'test_ref_123',
                'id': 'test_transaction_123'
            }
        }
        
        signature = hmac.new(
            settings.PAYSTACK_SECRET_KEY.encode('utf-8'),
            json.dumps(payload).encode('utf-8'),
            hashlib.sha512
        ).hexdigest()
        
        response = self.client.post(
            reverse('paystack-webhook'),
            data=payload,
            content_type='application/json',
            HTTP_X_PAYSTACK_SIGNATURE=signature
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        payment.refresh_from_db()
        self.assertEqual(payment.status, 'Completed')
        self.assertEqual(payment.transaction_id, 'test_transaction_123')
        
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, 'Paid')

    # Permission Tests
    def test_seller_permissions(self):
        # Create a seller
        seller = User.objects.create_user(
            username='test_seller',
            email='test_seller@example.com',
            password='testpass123'
        )
        seller_client = APIClient()
        seller_client.force_authenticate(user=seller)

        # Create a test image file
        image = SimpleUploadedFile(
            name='test_image.jpg',
            content=b'\x00\x01\x02\x03',  # Valid image content
            content_type='image/jpeg'
        )

        # Create a product as the seller
        response = seller_client.post(
            reverse('product-create'),
            {
                'title': 'Test Product',
                'description': 'Test Description',
                'price': '10.00',
                'stock': 10,
                'category': self.category.id,
                'image': image
            },
            format='multipart'
        )
        self.assertEqual(response.status_code, 201)
        product_id = response.data['id']

        # Try to update another seller's product
        other_seller = User.objects.create_user(
            username='other_seller',
            email='other_seller@example.com',
            password='testpass123'
        )
        other_seller_client = APIClient()
        other_seller_client.force_authenticate(user=other_seller)

        response = other_seller_client.patch(
            reverse('product-detail', kwargs={'product_id': product_id}),
            {'price': '20.00'}
        )
        self.assertEqual(response.status_code, 403)

    def test_buyer_permissions(self):
        """Test buyer-specific permissions"""
        # Test that buyer can create reviews
        data = {
            'product': self.product.id,
            'rating': 5,
            'comment': 'Great product!'
        }
        response = self.buyer_client.post(
            reverse('reviews'),
            data=data,
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Test that buyer cannot update products
        data = {'title': 'Updated by Buyer'}
        response = self.buyer_client.put(
            reverse('product-detail', kwargs={'product_id': self.product.id}),
            data=data
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
