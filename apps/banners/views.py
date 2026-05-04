from django.shortcuts import render
from rest_framework import generics, status, permissions, viewsets, mixins
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db import models
from .serializers import BannerSerializer
from .models import Banner

class BannerListView(generics.ListAPIView):
    serializer_class = BannerSerializer

    def get_queryset(self):
        return Banner.objects.all() #filter(user=self.request.user)
