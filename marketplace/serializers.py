from rest_framework import serializers
from decimal import Decimal
from .models import Product, Cart, Order, Payment, Refund,Category, Review

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = '__all__'

class ProductSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    class Meta:
        model = Product
        fields = '__all__'

class CartSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cart
        fields = '__all__'

class OrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = '__all__'

class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = ['order', 'amount', 'currency', 'payment_method']
        extra_kwargs = {
            'order': {'required': True},
            'amount': {'required': True},
            'currency': {'required': False, 'default': 'GHS'},
            'payment_method': {'required': False, 'default': 'card'}
        }

    def validate_amount(self, value):
        try:
            return Decimal(str(value))
        except (TypeError, ValueError):
            raise serializers.ValidationError("Amount must be a valid decimal number")

    def validate_order(self, value):
        if not isinstance(value, Order):
            try:
                value = Order.objects.get(id=value)
            except Order.DoesNotExist:
                raise serializers.ValidationError("Order does not exist")
        return value

    def validate_currency(self, value):
        valid_currencies = [choice[0] for choice in Payment.CURRENCY_CHOICES]
        if value not in valid_currencies:
            raise serializers.ValidationError(f"Invalid currency. Must be one of: {', '.join(valid_currencies)}")
        return value

    def validate_payment_method(self, value):
        valid_methods = [choice[0] for choice in Payment.PAYMENT_METHOD_CHOICES]
        if value not in valid_methods:
            raise serializers.ValidationError(f"Invalid payment method. Must be one of: {', '.join(valid_methods)}")
        return value

class RefundSerializer(serializers.ModelSerializer):
    class Meta:
        model = Refund
        fields = ['order', 'user', 'reason', 'status']
        extra_kwargs = {
            'order': {'required': True},
            'user': {'required': True},
            'reason': {'required': True},
            'status': {'required': False, 'default': 'pending'}
        }

    def validate_order(self, value):
        if not isinstance(value, Order):
            try:
                value = Order.objects.get(id=value)
            except Order.DoesNotExist:
                raise serializers.ValidationError("Order does not exist")
        return value

class ReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Review
        fields = ['product', 'rating', 'comment']
        extra_kwargs = {
            'product': {'required': True},
            'rating': {'required': True},
            'comment': {'required': True}
        }

    def validate_rating(self, value):
        if not 1 <= value <= 5:
            raise serializers.ValidationError("Rating must be between 1 and 5")
        return value

    def validate_product(self, value):
        if not isinstance(value, Product):
            try:
                value = Product.objects.get(id=value)
            except Product.DoesNotExist:
                raise serializers.ValidationError("Product does not exist")
        return value