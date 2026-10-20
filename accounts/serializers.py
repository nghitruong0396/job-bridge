from django.conf import settings
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import IntegrityError, transaction
from rest_framework import serializers

from .models import User


class RegisterSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(max_length=254)
    password = serializers.CharField(write_only=True, trim_whitespace=False)

    class Meta:
        model = User
        fields = (
            "email", "password", "employee_code", "full_name", "department", "phone", "role",
        )

    def validate_email(self, value):
        email = value.strip().lower()
        if email.rsplit("@", 1)[1] != settings.COMPANY_EMAIL_DOMAIN:
            raise serializers.ValidationError("Vui lòng sử dụng email công ty.")
        if User.objects.filter(email=email).exists():
            raise serializers.ValidationError("Email đã được sử dụng.")
        return email

    def validate(self, attrs):
        try:
            validate_password(attrs["password"], user=User(**attrs))
        except DjangoValidationError as error:
            raise serializers.ValidationError({"password": error.messages})
        return attrs

    def create(self, validated_data):
        try:
            with transaction.atomic():
                return User.objects.create_user(
                    **validated_data, is_staff=False, is_superuser=False,
                )
        except IntegrityError:
            raise serializers.ValidationError("Email hoặc mã nhân viên đã tồn tại.")


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, trim_whitespace=False)

    def validate(self, attrs):
        user = authenticate(
            request=self.context.get("request"),
            email=attrs["email"],
            password=attrs["password"],
        )
        if user is None:
            raise serializers.ValidationError(
                "Email hoặc mật khẩu không hợp lệ."
            )

        attrs["user"] = user
        return attrs


class AccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            "id",
            "employee_code",
            "email",
            "full_name",
            "department",
            "phone",
            "role",
        )
        read_only_fields = fields
