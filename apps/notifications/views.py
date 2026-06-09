from django.db.models import Count, Q

from rest_framework import generics
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from .models import Notification
from .serializers import NotificationSerializer



class NotificationListView(generics.ListAPIView):
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Notification.objects.filter(
            user=self.request.user
        ).order_by('-created_at')
    

class UnreadCountView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        count = Notification.objects.filter(
            user=request.user,
            is_read=False
        ).count()

        return Response({
            "unread_count": count
        })
    
class MarkReadView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, pk=None):

        if pk:
            notification = Notification.objects.filter(
                id=pk,
                user=request.user
            ).first()

            if not notification:
                return Response(
                    {"detail": "Notification not found"},
                    status=status.HTTP_404_NOT_FOUND
                )

            notification.is_read = True
            notification.save(update_fields=['is_read'])

            return Response({
                "message": "Notification marked as read"
            })

        Notification.objects.filter(
            user=request.user,
            is_read=False
        ).update(is_read=True)

        return Response({
            "message": "All notifications marked as read"
        })
    
