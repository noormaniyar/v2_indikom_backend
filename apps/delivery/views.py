from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import serializers
from django.shortcuts import get_object_or_404

from .models import Shipment, ShipmentTracking
from apps.accounts.permissions import IsDeliveryAgent, IsModerator
from apps.orders.models import Order


# ─── SERIALIZERS ──────────────────────────────────────────────────────────────

class ShipmentTrackingSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShipmentTracking
        fields = ['id', 'status', 'location', 'description', 'latitude', 'longitude', 'created_at']


class ShipmentSerializer(serializers.ModelSerializer):
    tracking_events = ShipmentTrackingSerializer(many=True, read_only=True)
    delivery_agent_name = serializers.CharField(source='delivery_agent.user.full_name', read_only=True)

    class Meta:
        model = Shipment
        fields = [
            'id', 'order', 'tracking_id', 'courier_partner', 'status',
            'current_location', 'estimated_delivery', 'delivered_at',
            'delivery_agent_name', 'tracking_events', 'created_at',
        ]
        read_only_fields = ['tracking_id', 'created_at']


# ─── VIEWS ────────────────────────────────────────────────────────────────────

class TrackShipmentView(APIView):
    """Public tracking via tracking ID"""
    permission_classes = [permissions.AllowAny]

    def get(self, request, tracking_id):
        shipment = get_object_or_404(Shipment, tracking_id=tracking_id)
        serializer = ShipmentSerializer(shipment)
        return Response(serializer.data)


class OrderShipmentView(APIView):
    """Customer tracks their order shipment"""
    def get(self, request, order_id):
        order = get_object_or_404(Order, order_id=order_id, user=request.user)
        try:
            shipment = order.shipment
        except Shipment.DoesNotExist:
            return Response({'message': 'Shipment not yet created.'}, status=status.HTTP_404_NOT_FOUND)
        return Response(ShipmentSerializer(shipment).data)


class DeliveryAgentShipmentsView(generics.ListAPIView):
    """Delivery agent sees assigned shipments"""
    serializer_class = ShipmentSerializer
    permission_classes = [permissions.IsAuthenticated, IsDeliveryAgent]

    def get_queryset(self):
        return Shipment.objects.filter(
            delivery_agent=self.request.user.delivery_profile
        ).exclude(status=Shipment.Status.DELIVERED)


class UpdateShipmentStatusView(APIView):
    """Delivery agent updates shipment status"""
    permission_classes = [permissions.IsAuthenticated, IsDeliveryAgent]

    def patch(self, request, pk):
        shipment = get_object_or_404(
            Shipment, pk=pk, delivery_agent=request.user.delivery_profile
        )
        new_status = request.data.get('status')
        location = request.data.get('location', '')
        description = request.data.get('description', '')
        lat = request.data.get('latitude')
        lng = request.data.get('longitude')

        valid_statuses = [s[0] for s in Shipment.Status.choices]
        if new_status not in valid_statuses:
            return Response({'error': 'Invalid status.'}, status=status.HTTP_400_BAD_REQUEST)

        shipment.status = new_status
        shipment.current_location = location
        if new_status == Shipment.Status.DELIVERED:
            from django.utils import timezone
            shipment.delivered_at = timezone.now()
            shipment.order.status = Order.Status.DELIVERED
            shipment.order.delivered_at = timezone.now()
            shipment.order.save()

        shipment.save()

        ShipmentTracking.objects.create(
            shipment=shipment, status=new_status,
            location=location, description=description,
            latitude=lat, longitude=lng
        )

        return Response({'message': f'Shipment updated to {new_status}.', 'shipment': ShipmentSerializer(shipment).data})


class AdminCreateShipmentView(APIView):
    """Admin/Moderator creates shipment for an order"""
    permission_classes = [permissions.IsAuthenticated, IsModerator]

    def post(self, request):
        order_id = request.data.get('order_id')
        order = get_object_or_404(Order, order_id=order_id)

        if hasattr(order, 'shipment'):
            return Response({'error': 'Shipment already exists for this order.'}, status=status.HTTP_400_BAD_REQUEST)

        agent_id = request.data.get('delivery_agent_id')
        shipment = Shipment.objects.create(
            order=order,
            courier_partner=request.data.get('courier_partner', ''),
            estimated_delivery=request.data.get('estimated_delivery'),
        )
        if agent_id:
            from apps.accounts.models import DeliveryAgentProfile
            agent = get_object_or_404(DeliveryAgentProfile, id=agent_id)
            shipment.delivery_agent = agent
            shipment.save()

        order.status = Order.Status.SHIPPED
        order.save()

        return Response({'message': 'Shipment created.', 'shipment': ShipmentSerializer(shipment).data})


# ─── URLS ─────────────────────────────────────────────────────────────────────
from django.urls import path
from apps.orders.models import Order as _Order

urlpatterns = [
    path('track/<str:tracking_id>/', TrackShipmentView.as_view(), name='track-shipment'),
    path('order/<str:order_id>/', OrderShipmentView.as_view(), name='order-shipment'),
    path('agent/shipments/', DeliveryAgentShipmentsView.as_view(), name='agent-shipments'),
    path('agent/shipments/<int:pk>/update/', UpdateShipmentStatusView.as_view(), name='agent-update-shipment'),
    path('admin/create/', AdminCreateShipmentView.as_view(), name='admin-create-shipment'),
]
