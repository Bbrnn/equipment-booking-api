from rest_framework import serializers
from django.contrib.auth import get_user_model

User = get_user_model()


class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'password', 'first_name', 'last_name', 'department', 'phone_number']

    def create(self, validated_data):
        return User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', ''),
            department=validated_data.get('department', ''),
            phone_number=validated_data.get('phone_number', ''),
            role='employee'  # Always default to lowest privilege
        )
 

class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'role', 'department', 'phone_number']
        read_only_fields = ['id', 'username', 'role']


class AdminUserUpdateSerializer(serializers.ModelSerializer):
    """Allows Admins to view users and change their roles or active status."""
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'role', 'department', 'phone_number', 'is_active']
        read_only_fields = ['id', 'username', 'email']

