from django.contrib.auth import authenticate
from rest_framework import serializers

from .models import User


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
