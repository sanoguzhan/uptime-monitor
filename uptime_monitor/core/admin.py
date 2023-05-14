from django.contrib import admin

from .models import ScheduleItem, SiteRegistry, SiteResponseHistory

admin.site.register(SiteRegistry)
admin.site.register(SiteResponseHistory)
admin.site.register(ScheduleItem)
