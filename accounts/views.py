from django.shortcuts import render
from rest_framework import views
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from .serializers import (
    ChangePasswordSerializer,
    OTPVerificationSerializer,
    PasswordResetConfirmSerializer,
    PasswordResetRequestSerializer,
    ResendOTPSerializer,
    UserLoginSerializer,
    UserRegistrationSerializer,
)


class UserRegistrationView(views.APIView):

    @swagger_auto_schema(
        request_body=UserRegistrationSerializer,
        operation_summary="Register a new user",
        operation_description="Register a new user with phone number and password. Sends an OTP for verification.",
        responses={201: "User registered successfully", 400: "Invalid input"},
    )
    def post(self, request):
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "User registered successfully"}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class OTPVerificationView(views.APIView):
    @swagger_auto_schema(
        request_body=OTPVerificationSerializer,
        operation_summary="Verify OTP",
        operation_description="Verify the OTP sent to the user's phone number.",
        responses={200: "OTP verified successfully", 400: "Invalid OTP or expired"},
    )
    def post(self, request):
        serializer = OTPVerificationSerializer(data=request.data)
        if serializer.is_valid():
            return Response(serializer.validated_data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ResendOTPView(views.APIView):
    @swagger_auto_schema(
        request_body=ResendOTPSerializer,
        operation_summary="Resend OTP",
        operation_description="Resend the OTP to the user's phone number.",
        responses={200: "OTP resent successfully", 400: "Invalid phone number"},
    )
    def post(self, request):
        serializer = ResendOTPSerializer(data=request.data)
        if serializer.is_valid():
            return Response(serializer.validated_data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserLoginView(views.APIView):
    @swagger_auto_schema(
        request_body=UserLoginSerializer,
        operation_summary="User Login",
        operation_description="Login using phone number and password.",
        responses={200: "Login successful, returns access token", 400: "Invalid credentials"},
    )
    def post(self, request):
        serializer = UserLoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data["user"]
            refresh = RefreshToken.for_user(user)
            return Response({"access_token": str(refresh.access_token)}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PasswordResetRequestView(views.APIView):
    @swagger_auto_schema(
        request_body=PasswordResetRequestSerializer,
        operation_summary="Request Password Reset OTP",
        operation_description="Sends an OTP to reset the user's password.",
        responses={200: "Password reset OTP sent", 400: "Invalid phone number"},
    )
    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        if serializer.is_valid():
            return Response(serializer.validated_data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PasswordResetConfirmView(views.APIView):
    @swagger_auto_schema(
        request_body=PasswordResetConfirmSerializer,
        operation_summary="Confirm Password Reset",
        operation_description="Verify OTP and set a new password.",
        responses={200: "Password reset successful", 400: "Invalid OTP or expired"},
    )
    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        if serializer.is_valid():
            return Response(serializer.validated_data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ChangePasswordView(views.APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        request_body=ChangePasswordSerializer,
        operation_summary="Change Password",
        operation_description="Change password for authenticated users.",
        responses={200: "Password changed successfully", 400: "Invalid input"},
    )
    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data, context={"request": request})
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Password changed successfully."}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
