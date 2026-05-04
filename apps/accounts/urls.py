from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from . import views

urlpatterns = [
    # Auth
    # path('register/', views.RegisterView.as_view(), name='register'),
    # path('login/', views.CustomTokenObtainPairView.as_view(), name='login'),
    # path('logout/', views.LogoutView.as_view(), name='logout'),
    # path('token/refresh/', TokenRefreshView.as_view(), name='token-refresh'),

    # Profile
    path('me/', views.MeView.as_view(), name='me'),
    # path('me/change-password/', views.ChangePasswordView.as_view(), name='change-password'),

    # OTP
    path('otp/request/', views.RequestOTPView.as_view(), name='otp-request'),
    path('otp/verify/', views.VerifyOTPView.as_view(), name='otp-verify'),

    # Password Reset
    # path('forgot-password/', views.ForgotPasswordView.as_view(), name='forgot-password'),
    # path('reset-password/', views.ResetPasswordView.as_view(), name='reset-password'),

    # Addresses
    path('addresses/list/', views.AddressListView.as_view(), name='address-list'),
    path('addresses/create/', views.AddressListCreateView.as_view(), name='address-create'),
    path('addresses/<int:pk>/', views.AddressDetailView.as_view(), name='address-detail'),
    path('addresses/<int:pk>/set-default/', views.SetDefaultAddressView.as_view(), name='address-set-default'),

    # Supplier
    path('supplier/profile/', views.SupplierProfileView.as_view(), name='supplier-profile'),

    # Delivery Agent
    path('delivery/profile/', views.DeliveryAgentProfileView.as_view(), name='delivery-profile'),
]
