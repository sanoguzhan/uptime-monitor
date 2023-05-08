from .models import SiteRegistry, SiteResponseHistory
from rest_framework import serializers


class SiteRegistrySerializer(serializers.ModelSerializer):
    class Meta:
        model = SiteRegistry
        fields = "__all__"


class SiteResponseHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = SiteResponseHistory
        fields = "__all__"
