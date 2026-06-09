from . import views
from django.urls import path

urlpatterns = [
    path('', views.NotificationListView.as_view(), name='notification-list'),
    path('unread-count/', views.UnreadCountView.as_view(), name='notification-unread'),
    path('mark-read/', views.MarkReadView.as_view(), name='notification-mark-all-read'),
    path('<int:pk>/mark-read/', views.MarkReadView.as_view(), name='notification-mark-read'),
]
