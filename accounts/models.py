from datetime import timedelta
import secrets
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator
from django.core.exceptions import ValidationError
from django.utils import timezone

phone_regex = RegexValidator(
    regex=r'^\+\d{1,15}$',
    message="Phone number must be in E.164 format (e.g., +233501234567)."
)

class User(AbstractUser):
    username = models.CharField(max_length=30, unique=True)
    email = models.EmailField(unique=True, db_index=True)  # Added email field
    phone_number = models.CharField(max_length=15, unique=True, validators=[phone_regex])  # Removed comma
    verification_code = models.CharField(max_length=6, blank=True, null=True)
    code_expires_at = models.DateTimeField(null=True, blank=True)
    is_verified = models.BooleanField(default=False)
    is_seller = models.BooleanField(default=False)
    is_buyer = models.BooleanField(default=False)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username", "phone_number"]

    def __str__(self):
        return self.username

    def generate_otp_verification_code(self):
        """Generates a 6-digit OTP verification code and sets its expiration."""
        self.verification_code = str(secrets.randbelow(10**6)).zfill(6)
        self.code_expires_at = timezone.now() + timedelta(minutes=5)
        self.save()
        return self.verification_code

    def verify_otp_code(self, code):
        """Verifies the input OTP code and checks if it's expired."""
        if not self.verification_code or not self.code_expires_at:
            return False
        if code == self.verification_code and timezone.now() < self.code_expires_at:
            self.is_verified = True
            self.verification_code = None
            self.code_expires_at = None
            self.save()
            return True
        return False

    def save(self, *args, **kwargs):
        """Ensure a user cannot be both a seller and a buyer."""
        if self.is_seller and self.is_buyer:
            raise ValidationError("User cannot be both a seller and a buyer.")
        super().save(*args, **kwargs)
