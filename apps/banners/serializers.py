from rest_framework import serializers
from rest_framework.response import Response
from .models import Banner



class BannerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Banner
        fields = '__all__'
