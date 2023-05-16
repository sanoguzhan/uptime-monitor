from rest_framework import routers


from .views import ScheduleItemModelViewSet, SiteRegistryModelViewSet, SiteResponseHistoryReadOnlyModelViewSet

router = routers.DefaultRouter()
router.register(r'sites-registry', SiteRegistryModelViewSet)
router.register(r'schedule-items', ScheduleItemModelViewSet)
router.register(r'sites-history', SiteResponseHistoryReadOnlyModelViewSet)