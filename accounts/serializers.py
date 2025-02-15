from rest_framework import serializers

from accounts.services.hubtel_sms import send_sms
from .models import User
from django.contrib.auth import authenticate


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'is_seller', 'is_buyer', 'is_verified']
        
class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    
    class Meta:
        model = User
        fields = ["username", "phone_number", "password", "is_seller", "is_buyer"]

    def create(self, validated_data):
        """Creates a new user and generates an OTP for phone verification."""
        user = User.objects.create_user(
            username=validated_data["username"],
            phone_number=validated_data["phone_number"],
            password=validated_data["password"],
            is_seller=validated_data.get("is_seller", False),
            is_buyer=validated_data.get("is_buyer", False),
        )
        user.generate_otp_verification_code()
        send_sms(user.phone_number, f"Your OTP for verification is {user.verification_code}. It expires in 5 minutes.")
        return user

class OTPVerificationSerializer(serializers.Serializer):
    phone_number = serializers.CharField()
    verification_code = serializers.CharField(max_length=6)

    def validate(self, data):
        """Checks OTP code validity."""
        try:
            user = User.objects.get(phone_number=data["phone_number"])
        except User.DoesNotExist:
            raise serializers.ValidationError("User not found.")
        
        if not user.verify_otp_code(data["verification_code"]):
            raise serializers.ValidationError("Invalid or expired OTP.")
        
        user.is_active = True
        
        return {"message": "Phone number verified successfully!"}
        
class ResendOTPSerializer(serializers.Serializer):
    phone_number = serializers.CharField()

    def validate(self, data):
        """Finds user and generates a new OTP."""
        try:
            user = User.objects.get(phone_number=data["phone_number"])
        except User.DoesNotExist:
            raise serializers.ValidationError("User not found.")
        
        if user.is_verified:
            raise serializers.ValidationError("User is already verified.")
        
        user.generate_otp_verification_code()
        send_sms(user.phone_number, f"Your new OTP for verification is {user.verification_code}. It expires in 5 minutes.")
        return {"message": "A new OTP has been sent to your phone number."}
        
class PasswordResetRequestSerializer(serializers.Serializer):
    phone_number = serializers.CharField()

    def validate(self, data):
        """Finds user and generates a password reset OTP."""
        try:
            user = User.objects.get(phone_number=data["phone_number"])
        except User.DoesNotExist:
            raise serializers.ValidationError("User not found.")
        
        user.generate_otp_verification_code()
        send_sms(user.phone_number, f"Your OTP for password reset is {user.verification_code}. It expires in 5 minutes.")
        return {"message": "A password reset OTP has been sent to your phone number."}

class PasswordResetConfirmSerializer(serializers.Serializer):
    phone_number = serializers.CharField()
    verification_code = serializers.CharField(max_length=6)
    new_password = serializers.CharField(write_only=True, min_length=8)

    def validate(self, data):
        """Checks OTP and updates password."""
        try:
            user = User.objects.get(phone_number=data["phone_number"])
        except User.DoesNotExist:
            raise serializers.ValidationError("User not found.")

        if not user.verify_otp_code(data["verification_code"]):
            raise serializers.ValidationError("Invalid or expired OTP.")

        user.set_password(data["new_password"])
        user.save()
        return {"message": "Password reset successful!"}

class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, min_length=8)

    def validate(self, data):
        user = self.context["request"].user
        if not user.check_password(data["old_password"]):
            raise serializers.ValidationError("Old password is incorrect.")
        return data

    def save(self, **kwargs):
        user = self.context["request"].user
        user.set_password(self.validated_data["new_password"])
        user.save()
        return user

    
class UserLoginSerializer(serializers.Serializer):
    phone_number = serializers.CharField()
    password = serializers.CharField(write_only=True)
    def validate(self, data):
        phone_number = data.get('phone_number')
        password = data.get('password')
        
        # Adjust this line according to how authentication is implemented
        user = authenticate(phone_number=phone_number, password=password)
        
        if not user:
            raise serializers.ValidationError("Invalid phone number or password.")
        
        data['user'] = user
        return data
 