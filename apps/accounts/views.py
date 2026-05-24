from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from django.utils import timezone
from django.contrib.auth import update_session_auth_hash

from .models import User, OTP, Address, SupplierProfile, ModeratorProfile, DeliveryAgentProfile
from .serializers import (
    UserSerializer, RegisterSerializer,
    OTPRequestSerializer, OTPVerifySerializer,
    ChangePasswordSerializer, ForgotPasswordSerializer, ResetPasswordSerializer,
    AddressSerializer, SupplierProfileSerializer, SupplierProfileUpdateSerializer,
    DeliveryAgentProfileSerializer, CustomTokenObtainPairSerializer, ModeratorProfileUpdateSerializer,
    ModeratorProfileSerializer
)
from .permissions import IsSupplier, IsModerator, IsCustomer, IsDeliveryAgent

class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        if user.role == User.Role.SUPPLIER:
            SupplierProfile.objects.create(
                user=user,
                business_name=user.full_name or user.email
            )

        elif user.role == User.Role.MODERATOR:
            ModeratorProfile.objects.create(
                user=user,
            )

        return Response({
            'message': 'Registration successful. Please verify via OTP.'
        }, status=status.HTTP_201_CREATED)



class LogoutView(APIView):
    def post(self, request):
        try:
            refresh_token = request.data.get('refresh')
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response({'message': 'Logged out successfully.'})
        except Exception:
            return Response({'error': 'Invalid token.'}, status=status.HTTP_400_BAD_REQUEST)


class MeView(generics.RetrieveUpdateAPIView):
    serializer_class = UserSerializer

    def get_object(self):
        return self.request.user



class RequestOTPView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        phone = request.data.get('phone')
        email = request.data.get('email')
        role = request.data.get('role', User.Role.CUSTOMER)

        if not phone and not email:
            return Response({'error': 'Phone or email required'}, status=400)

        user, created = User.objects.get_or_create(
            phone=phone,
            defaults={
                "email": email,
                "role": role,
                "is_verified": False
            }
        )

        # Invalidate old OTPs
        OTP.objects.filter(user=user, is_used=False).update(is_used=True)

        otp = OTP.objects.create(
            user=user,
            purpose=OTP.Purpose.LOGIN
        )

        print("OTP:", otp.code)

        return Response({
            "message": "OTP sent successfully",
            "otp": otp.code,
            "is_new_user": created,
            "expires_at": otp.expires_at
        })

class VerifyOTPView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        phone = request.data.get('phone')
        email = request.data.get('email')
        code = request.data.get('code')

        if not phone and not email:
            return Response({'error': 'Phone or email required'}, status=400)

        user = User.objects.filter(
            phone=phone if phone else None,
            #email=email if email else None
        ).first()

        if not user:
            return Response({'error': 'User not found'}, status=404)

        otp = OTP.objects.filter(
            user=user,
            code=code,
            purpose=OTP.Purpose.LOGIN,
            is_used=False
        ).order_by('-created_at').first()

        if not otp:
            return Response({'error': 'Invalid OTP'}, status=400)

        if otp.is_expired:
            return Response({'error': 'OTP expired'}, status=400)

        otp.is_used = True
        otp.save()

        # ✅ FINAL USER CREATION POINT (verification)
        user.is_verified = True
        user.save()

        # Create supplier profile if needed
        if user.role == User.Role.SUPPLIER and not hasattr(user, 'supplier_profile'):
            SupplierProfile.objects.create(
                user=user,
                business_name=user.full_name or user.email
            )

        # Create moderator profile if needed
        if user.role == User.Role.MODERATOR and not hasattr(user, 'moderator_profile'):
            ModeratorProfile.objects.create(
                user=user,
                # email=user.email
            )

        refresh = RefreshToken.for_user(user)

        return Response({
            "message": "Login successful",
            "tokens": {
                "refresh": str(refresh),
                "access": str(refresh.access_token)
            },
            "user": UserSerializer(user).data
        })


class ChangePasswordView(APIView):
    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = request.user

        if not user.check_password(serializer.validated_data['old_password']):
            return Response({'error': 'Old password is incorrect.'}, status=status.HTTP_400_BAD_REQUEST)

        user.set_password(serializer.validated_data['new_password'])
        user.save()
        return Response({'message': 'Password changed successfully.'})


class ForgotPasswordView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = ForgotPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            user = User.objects.get(email=serializer.validated_data['email'])
        except User.DoesNotExist:
            # Don't reveal if email exists
            return Response({'message': 'If this email exists, a reset code has been sent.'})

        OTP.objects.filter(user=user, purpose=OTP.Purpose.PASSWORD_RESET, is_used=False).update(is_used=True)
        otp = OTP.objects.create(user=user, purpose=OTP.Purpose.PASSWORD_RESET)

        # TODO: Send email with OTP
        # send_reset_email(user.email, otp.code)

        return Response({'message': 'If this email exists, a reset code has been sent.'})


class ResetPasswordView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = ResetPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        try:
            user = User.objects.get(email=data['email'])
        except User.DoesNotExist:
            return Response({'error': 'User not found.'}, status=status.HTTP_404_NOT_FOUND)

        otp = OTP.objects.filter(
            user=user, code=data['code'],
            purpose=OTP.Purpose.PASSWORD_RESET, is_used=False
        ).order_by('-created_at').first()

        if not otp or otp.is_expired:
            return Response({'error': 'Invalid or expired OTP.'}, status=status.HTTP_400_BAD_REQUEST)

        user.set_password(data['new_password'])
        user.save()
        otp.is_used = True
        otp.save()

        return Response({'message': 'Password reset successfully.'})


# ─── ADDRESS VIEWS ────────────────────────────────────────────────────────────
class AddressListView(generics.ListAPIView):
    serializer_class = AddressSerializer

    def get_queryset(self):
        return Address.objects.filter(user=self.request.user)

class AddressListCreateView(generics.ListCreateAPIView):
    serializer_class = AddressSerializer

    def get_queryset(self):
        return Address.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class AddressDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = AddressSerializer

    def get_queryset(self):
        return Address.objects.filter(user=self.request.user)


class SetDefaultAddressView(APIView):
    def post(self, request, pk):
        try:
            address = Address.objects.get(pk=pk, user=request.user)
        except Address.DoesNotExist:
            return Response({'error': 'Address not found.'}, status=status.HTTP_404_NOT_FOUND)
        address.is_default = True
        address.save()
        return Response({'message': 'Default address set.'})


# ─── SUPPLIER VIEWS ───────────────────────────────────────────────────────────

class SupplierProfileView(generics.RetrieveUpdateAPIView):
    permission_classes = [permissions.IsAuthenticated, IsSupplier]

    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return SupplierProfileUpdateSerializer
        return SupplierProfileSerializer

    def get_object(self):
        return self.request.user.supplier_profile

class ModeratorProfileView(generics.RetrieveUpdateAPIView):
    permission_classes = [permissions.IsAuthenticated, IsModerator]

    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return ModeratorProfileUpdateSerializer
        return ModeratorProfileSerializer

    def get_object(self):
        profile, created = ModeratorProfile.objects.get_or_create(
            user=self.request.user,
        )
        return profile
class DeliveryAgentProfileView(generics.RetrieveUpdateAPIView):
    permission_classes = [permissions.IsAuthenticated, IsDeliveryAgent]
    serializer_class = DeliveryAgentProfileSerializer

    def get_object(self):
        return self.request.user.delivery_profile

    def update(self, request, *args, **kwargs):
        profile = self.get_object()
        # Allow updating location
        lat = request.data.get('current_latitude')
        lng = request.data.get('current_longitude')
        if lat and lng:
            profile.current_latitude = lat
            profile.current_longitude = lng
            profile.save()
        return super().update(request, *args, **kwargs)
