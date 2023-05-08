from django.contrib import admin
from .models import SiteRegistry, SiteResponseHistory, ScheduleItem


admin.site.register(SiteRegistry)
admin.site.register(SiteResponseHistory)
admin.site.register(ScheduleItem)
