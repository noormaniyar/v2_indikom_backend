from django.urls import path
from . import views

urlpatterns = [
    path('plans/', views.PlanListView.as_view(), name='subscription-plans'),
    path('my/', views.SupplierSubscriptionView.as_view(), name='my-subscriptions'),
    path('subscribe/', views.SubscribeView.as_view(), name='subscribe'),
]
