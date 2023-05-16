from rest_framework import status, viewsets
from rest_framework.response import Response

from .models import ScheduleItem, SiteRegistry, SiteResponseHistory
from .serializers import (
    ScheduleItemReadSerializer,
    ScheduleItemWriteSerializer,
    SiteRegistrySerializer,
    SiteResponseHistorySerializer,
)


class SiteRegistryModelViewSet(viewsets.ModelViewSet):
    queryset = SiteRegistry.objects.all()
    serializer_class = SiteRegistrySerializer

    def get_queryset(self):
        return self.queryset.filter(user=self.request.user) 
    

class ScheduleItemModelViewSet(viewsets.ModelViewSet):
    queryset = ScheduleItem.objects.select_related("check_registry", "schedule").all()
    serializer_class = ScheduleItemReadSerializer
    
    def get_queryset(self):
        return self.queryset.filter(check_registry__user=self.request.user).defer("periodic_task")
    
    def get_serializer_class(self):
        if self.action in ["create", "update", "partial_update"]:
            return ScheduleItemWriteSerializer
        return ScheduleItemReadSerializer
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        site_registry = serializer.validated_data["check_registry"]
        if site_registry.user != request.user:
            return Response(
                {"message": "You don't have permission to perform this action."},
                status=status.HTTP_403_FORBIDDEN,
            )
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)



class SiteResponseHistoryReadOnlyModelViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = SiteResponseHistory.objects.select_related("check_registry").all()
    serializer_class = SiteResponseHistorySerializer

    def get_queryset(self):
        return self.queryset.filter(check_registry__user=self.request.user).values(
            "id",
            "created_at",
            "response_time",
            "response_text",
            "response_code",
            "check_registry__user",
            "check_registry__url",
        )