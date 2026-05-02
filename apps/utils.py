"""
apps/utils.py  —  shared helpers used across multiple apps
"""
import random
import string
import hmac
import hashlib
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string


# ─── OTP / CODE ───────────────────────────────────────────────────────────────

def generate_otp(length=6) -> str:
    return ''.join(random.choices(string.digits, k=length))


def generate_ref_code(prefix='INK', length=8) -> str:
    chars = string.ascii_uppercase + string.digits
    return prefix + ''.join(random.choices(chars, k=length))


# ─── EMAIL ────────────────────────────────────────────────────────────────────

def send_otp_email(email: str, otp_code: str, purpose: str):
    subject_map = {
        'email_verify': 'Verify your IndiKom email',
        'password_reset': 'IndiKom password reset code',
        'login': 'Your IndiKom login OTP',
    }
    subject = subject_map.get(purpose, 'IndiKom OTP')
    message = (
        f"Your IndiKom OTP is: {otp_code}\n\n"
        f"This code expires in {settings.OTP_EXPIRY_MINUTES} minutes.\n"
        f"Do not share this code with anyone."
    )
    try:
        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [email], fail_silently=True)
    except Exception:
        pass


def send_order_confirmation_email(user, order):
    subject = f"Order Confirmed — {order.order_id}"
    message = (
        f"Hi {user.first_name or user.email},\n\n"
        f"Your order {order.order_id} has been placed successfully!\n"
        f"Total: ₹{order.total_amount}\n\n"
        f"We'll notify you when it ships.\n\nThank you for shopping with IndiKom!"
    )
    try:
        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [user.email], fail_silently=True)
    except Exception:
        pass


def send_supplier_approval_email(supplier_profile, approved: bool, reason: str = ''):
    user = supplier_profile.user
    if approved:
        subject = "🎉 Your IndiKom supplier account is approved!"
        message = (
            f"Hi {user.first_name or supplier_profile.business_name},\n\n"
            f"Your supplier account has been approved. You can now start listing products!\n\n"
            f"Login at https://indikom.com/supplier"
        )
    else:
        subject = "IndiKom supplier application update"
        message = (
            f"Hi {user.first_name or supplier_profile.business_name},\n\n"
            f"Unfortunately your supplier application was not approved.\n"
            f"Reason: {reason or 'Not specified'}\n\n"
            f"You may contact support for assistance."
        )
    try:
        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [user.email], fail_silently=True)
    except Exception:
        pass


# ─── RAZORPAY SIGNATURE VERIFICATION ─────────────────────────────────────────

def verify_razorpay_signature(order_id: str, payment_id: str, signature: str) -> bool:
    msg = f"{order_id}|{payment_id}"
    generated = hmac.new(
        settings.RAZORPAY_KEY_SECRET.encode(),
        msg.encode(),
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(generated, signature)


# ─── PAGINATION HELPERS ───────────────────────────────────────────────────────

def paginate_queryset(queryset, request, serializer_class):
    from config.pagination import StandardResultsPagination
    paginator = StandardResultsPagination()
    page = paginator.paginate_queryset(queryset, request)
    if page is not None:
        serializer = serializer_class(page, many=True, context={'request': request})
        return paginator.get_paginated_response(serializer.data)
    serializer = serializer_class(queryset, many=True, context={'request': request})
    from rest_framework.response import Response
    return Response(serializer.data)


# ─── SLUG GENERATION ─────────────────────────────────────────────────────────

def unique_slug(model_class, name: str, slug_field='slug') -> str:
    from django.utils.text import slugify
    import uuid
    base = slugify(name)
    slug = base
    if model_class.objects.filter(**{slug_field: slug}).exists():
        slug = f"{base}-{str(uuid.uuid4())[:8]}"
    return slug
