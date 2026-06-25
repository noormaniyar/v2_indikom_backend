from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from phonenumber_field.modelfields import PhoneNumberField
import random
import string
from django.utils import timezone
from datetime import timedelta
from django.conf import settings

from django.contrib.auth.models import BaseUserManager


class IsActive(models.TextChoices):
    YES = 'yes', 'Yes'
    NO = 'no', 'No'

class UserManager(BaseUserManager):

    def create_user(self, phone, password=None, **extra_fields):
        if not phone:
            raise ValueError('Phone number is required')

        user = self.model(phone=phone, **extra_fields)
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()

        user.save(using=self._db)
        return user

    def create_superuser(self, phone, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', User.Role.ADMIN)
        extra_fields.setdefault('is_verified', True)

        if not password:
            raise ValueError('Superuser must have a password')

        return self.create_user(phone, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    class Role(models.TextChoices):
        CUSTOMER = 'customer', 'Customer'
        SUPPLIER = 'supplier', 'Supplier'
        MODERATOR = 'moderator', 'Moderator'
        DELIVERY_AGENT = 'delivery_agent', 'Delivery Agent'
        ADMIN = 'admin', 'Admin'

    phone = PhoneNumberField(unique=True)
    onesignal_player_id = models.CharField(max_length=255, blank=True, null=True, db_index=True)
    email = models.EmailField(blank=True, null=True)
    first_name = models.CharField(max_length=150, blank=True)
    last_name = models.CharField(max_length=150, blank=True)
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.CUSTOMER)
    is_active = models.CharField(max_length=20, choices=IsActive.choices, default=IsActive.YES)
    is_staff = models.BooleanField(default=False)
    is_verified = models.BooleanField(default=False)
    profile_picture = models.ImageField(upload_to='users/profiles/', blank=True, null=True)
    preferred_language = models.CharField(max_length=10, default='en')
    created_at = models.DateTimeField(auto_now_add=True)
    onesignal_updated_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = 'phone'
    REQUIRED_FIELDS = []

    objects = UserManager()

    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'

    def __str__(self):
        return f"{self.phone} ({self.role})"

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip() or self.email


class OTP(models.Model):
    class Purpose(models.TextChoices):
        PHONE_VERIFY = 'phone_verify', 'Phone Verification'
        EMAIL_VERIFY = 'email_verify', 'Email Verification'
        PASSWORD_RESET = 'password_reset', 'Password Reset'
        LOGIN = 'login', 'Login'

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='otps')
    code = models.CharField(max_length=10)
    purpose = models.CharField(max_length=20, choices=Purpose.choices)
    is_used = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    class Meta:
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.pk:
            self.expires_at = timezone.now() + timedelta(minutes=settings.OTP_EXPIRY_MINUTES)
            self.code = ''.join(random.choices(string.digits, k=settings.OTP_LENGTH))
        super().save(*args, **kwargs)

    @property
    def is_expired(self):
        return timezone.now() > self.expires_at

    def __str__(self):
        return f"OTP {self.code} for {self.user.phone} ({self.purpose})"


class Address(models.Model):
    class AddressType(models.TextChoices):
        HOME = 'home', 'Home'
        WORK = 'work', 'Work'
        OTHER = 'other', 'Other'

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='addresses')
    label = models.CharField(max_length=20, choices=AddressType.choices, default=AddressType.HOME)
    full_name = models.CharField(max_length=255)
    phone = PhoneNumberField()
    line1 = models.CharField(max_length=255)
    line2 = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    country = models.CharField(max_length=100, default='India')
    pincode = models.CharField(max_length=20)
    is_default = models.BooleanField(default=False)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = 'Addresses'

    def save(self, *args, **kwargs):
        # Only one default address per user
        if self.is_default:
            Address.objects.filter(user=self.user, is_default=True).exclude(pk=self.pk).update(is_default=False)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.full_name} - {self.city}, {self.state}"


class SupplierProfile(models.Model):
    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        APPROVED = 'approved', 'Approved'
        REJECTED = 'rejected', 'Rejected'
        SUSPENDED = 'suspended', 'Suspended'

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='supplier_profile')
    business_name = models.CharField(max_length=255, blank=True, null=True)
    business_email = models.EmailField(blank=True, null=True)
    business_phone = PhoneNumberField(blank=True, null=True)
    business_address = models.TextField(blank=True, null=True)
    gstin = models.CharField(max_length=20, blank=True)  # GST Identification Number
    pan = models.CharField(max_length=20, blank=True)
    bank_account_number = models.CharField(max_length=50, blank=True)
    bank_ifsc = models.CharField(max_length=20, blank=True)
    bank_name = models.CharField(max_length=100, blank=True)
    logo = models.ImageField(upload_to='suppliers/logos/', blank=True, null=True)
    banner = models.ImageField(upload_to='suppliers/banners/', blank=True, null=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    rejection_reason = models.TextField(blank=True)
    commission_rate = models.DecimalField(max_digits=5, decimal_places=2, default=10.00)  # % platform commission
    rating = models.DecimalField(max_digits=3, decimal_places=2, default=0.00)
    total_sales = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.business_name} ({self.status})"

class ModeratorProfile(models.Model):
    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        APPROVED = 'approved', 'Approved'
        REJECTED = 'rejected', 'Rejected'
        SUSPENDED = 'suspended', 'Suspended'

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='moderator_profile')
    email = models.EmailField(blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    bank_account_number = models.CharField(max_length=50, blank=True)
    bank_ifsc = models.CharField(max_length=20, blank=True)
    bank_name = models.CharField(max_length=100, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user} ({self.status})"

class DeliveryAgentProfile(models.Model):
    class Status(models.TextChoices):
        ACTIVE = 'active', 'Active'
        INACTIVE = 'inactive', 'Inactive'
        ON_DELIVERY = 'on_delivery', 'On Delivery'

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='delivery_profile')
    vehicle_type = models.CharField(max_length=50, blank=True)
    vehicle_number = models.CharField(max_length=20, blank=True)
    license_number = models.CharField(max_length=50, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.INACTIVE)
    current_latitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    current_longitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    rating = models.DecimalField(max_digits=3, decimal_places=2, default=0.00)
    total_deliveries = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.full_name} - {self.vehicle_type}"
