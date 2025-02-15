from django.urls import path
from .views import (
    UserProfileView,
    UserRegistrationView,
    OTPVerificationView,
    ResendOTPView,
    UserLoginView,
    PasswordResetRequestView,
    PasswordResetConfirmView,
    ChangePasswordView,
)

urlpatterns = [
    path("profile/", UserProfileView.as_view(), name="user-profile"),
    path("register/", UserRegistrationView.as_view(), name="register"),
    path("verify-otp/", OTPVerificationView.as_view(), name="verify-otp"),
    path("resend-otp/", ResendOTPView.as_view(), name="resend-otp"),
    path("login/", UserLoginView.as_view(), name="login"),
    path("password-reset-request/", PasswordResetRequestView.as_view(), name="password-reset-request"),
    path("password-reset-confirm/", PasswordResetConfirmView.as_view(), name="password-reset-confirm"),
    path("change-password/", ChangePasswordView.as_view(), name="change-password"),
]
