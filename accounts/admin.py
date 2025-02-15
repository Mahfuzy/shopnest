from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User

class CustomUserAdmin(UserAdmin):
    model = User
    list_display = ("id", "username", "email", "phone_number", "is_verified", "is_seller", "is_buyer", "is_staff", "is_superuser")
    list_filter = ("is_verified", "is_seller", "is_buyer", "is_staff", "is_superuser")
    search_fields = ("username", "email", "phone_number")
    ordering = ("email",)
    fieldsets = (
        (None, {"fields": ("username", "email", "password")}),
        ("Personal Info", {"fields": ("phone_number",)}),
        ("Verification", {"fields": ("is_verified", "verification_code", "code_expires_at")}),
        ("Roles", {"fields": ("is_seller", "is_buyer")}),
        ("Permissions", {"fields": ("is_staff", "is_superuser", "groups", "user_permissions")}),
        ("Important Dates", {"fields": ("last_login", "date_joined")}),
    )
    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("username", "email", "phone_number", "password1", "password2", "is_seller", "is_buyer"),
        }),
    )

admin.site.register(User, CustomUserAdmin)
