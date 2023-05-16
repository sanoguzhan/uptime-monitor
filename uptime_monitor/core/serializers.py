from django_celery_beat.models import IntervalSchedule
from rest_framework import serializers

from .models import ScheduleItem, SiteRegistry, SiteResponseHistory


class ScheduleIntervalSerializer(serializers.Serializer):
    every = serializers.IntegerField(min_value=1, max_value=999, default=30)
    period = serializers.ChoiceField(
        choices=IntervalSchedule.PERIOD_CHOICES, default=IntervalSchedule.SECONDS
    )


class SiteRegistrySerializer(serializers.ModelSerializer):
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model = SiteRegistry
        read_only_fields = ("last_checked_at",)
        fields = "__all__"


class ScheduleItemReadSerializer(serializers.ModelSerializer):
    check_registry = SiteRegistrySerializer()
    schedule = ScheduleIntervalSerializer()

    class Meta:
        model = ScheduleItem
        exclude = ("periodic_task",)


class ScheduleItemWriteSerializer(serializers.ModelSerializer):
    periodic_task = serializers.HiddenField(default=None)
    schedule = ScheduleIntervalSerializer(required=False)

    class Meta:
        model = ScheduleItem
        fields = "__all__"

    def update(self, instance, validated_data):
        schedule_data = validated_data.pop("schedule", None)
        if schedule_data:
            schedule = instance.schedule
            schedule.every = schedule_data.get("every", schedule.every)
            schedule.period = schedule_data.get("period", schedule.period)
            schedule.save()
        return super().update(instance, validated_data)


class SiteResponseHistorySerializer(serializers.ModelSerializer):
    site = serializers.CharField(source="check_registry__url")
    class Meta:
        model = SiteResponseHistory
        read_only_fields = (
            "created_at",
            "response_time",
            "response_text",
            "response_code",
        )
        exclude = ("response_headers","check_registry")