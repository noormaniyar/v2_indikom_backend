from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from .models import User, OTP, Address, SupplierProfile, ModeratorProfile, DeliveryAgentProfile


class UserSerializer(serializers.ModelSerializer):
    full_name = serializers.ReadOnlyField()

    class Meta:
        model = User
        fields = [
            'id', 'email', 'phone', 'first_name', 'last_name',
            'full_name', 'role', 'is_verified', 'profile_picture',
            'preferred_language', 'created_at',
        ]
        read_only_fields = ['id', 'role', 'phone', 'is_verified', 'created_at']


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, validators=[validate_password])
    confirm_password = serializers.CharField(write_only=True)
    role = serializers.ChoiceField(
        choices=[User.Role.CUSTOMER, User.Role.SUPPLIER],
        default=User.Role.CUSTOMER
    )

    class Meta:
        model = User
        fields = ['email', 'phone', 'first_name', 'last_name', 'password', 'confirm_password', 'role']

    def validate(self, attrs):
        if attrs['password'] != attrs.pop('confirm_password'):
            raise serializers.ValidationError({'password': 'Passwords do not match.'})
        return attrs

    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        return user


class OTPRequestSerializer(serializers.Serializer):
    phone = serializers.CharField(required=False)
    email = serializers.EmailField(required=False)

    def validate(self, attrs):
        if not attrs.get('phone') and not attrs.get('email'):
            raise serializers.ValidationError("Phone or Email required")
        return attrs

class OTPVerifySerializer(serializers.Serializer):
    phone = serializers.CharField(required=False)
    email = serializers.EmailField(required=False)
    code = serializers.CharField()

    def validate(self, attrs):
        if not attrs.get('phone') and not attrs.get('email'):
            raise serializers.ValidationError("Phone or Email required")
        return attrs

class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, validators=[validate_password])
    confirm_password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        if attrs['new_password'] != attrs.pop('confirm_password'):
            raise serializers.ValidationError({'new_password': 'Passwords do not match.'})
        return attrs


class ForgotPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()


class ResetPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()
    code = serializers.CharField(max_length=10)
    new_password = serializers.CharField(validators=[validate_password])
    confirm_password = serializers.CharField()

    def validate(self, attrs):
        if attrs['new_password'] != attrs.pop('confirm_password'):
            raise serializers.ValidationError({'new_password': 'Passwords do not match.'})
        return attrs


class AddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = [
            'id', 'label', 'full_name', 'phone', 'line1', 'line2',
            'city', 'state', 'country', 'pincode', 'is_default',
            'latitude', 'longitude', 'created_at',
        ]
        read_only_fields = ['id', 'created_at']


class SupplierProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = SupplierProfile
        fields = [
            'id', 'user', 'business_name', 'business_email', 'business_phone',
            'business_address', 'gstin', 'pan', 'bank_account_number',
            'bank_ifsc', 'bank_name', 'logo', 'banner', 'status',
            'rejection_reason', 'commission_rate', 'rating', 'total_sales', 'created_at',
        ]
        read_only_fields = ['id', 'user', 'status', 'rejection_reason', 'commission_rate', 'rating', 'total_sales', 'created_at']


class SupplierProfileUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = SupplierProfile
        fields = [
            'business_name', 'business_email', 'business_phone',
            'business_address', 'gstin', 'pan', 'bank_account_number',
            'bank_ifsc', 'bank_name', 'logo', 'banner',
        ]


class ModeratorProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = ModeratorProfile
        fields = ['email', 'bank_account_number', 'bank_ifsc', 'bank_name']

class ModeratorProfileUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ModeratorProfile
        fields = ['email', 'bank_account_number', 'bank_ifsc', 'bank_name']

class DeliveryAgentProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = DeliveryAgentProfile
        fields = [
            'id', 'user', 'vehicle_type', 'vehicle_number', 'license_number',
            'status', 'current_latitude', 'current_longitude', 'rating', 'total_deliveries',
        ]
        read_only_fields = ['id', 'user', 'status', 'rating', 'total_deliveries']


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['email'] = user.email
        token['role'] = user.role
        token['full_name'] = user.full_name
        return token

    def validate(self, attrs):
        data = super().validate(attrs)
        data['user'] = UserSerializer(self.user).data
        return data
