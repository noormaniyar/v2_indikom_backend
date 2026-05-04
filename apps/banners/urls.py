from django.urls import path
from . import views

urlpatterns = [
    path('list/', views.BannerListView.as_view(), name='banner-list'),
]
