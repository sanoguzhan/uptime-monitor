from django.contrib.auth import get_user_model
from rest_framework import exceptions
from django.conf import settings

User = get_user_model()


class LocalAuth:
    def authenticate(self, request, username=None, password=None):
        if not settings.DEBUG:
            return None
        try:
            admins = list(zip(*settings.ADMINS))[1]
            if username not in admins:
                return None
            user, _ = User.objects.get_or_create(username=username)
            user.name = username
            user.is_superuser = True
            user.is_staff = True
            user.save()

        except exceptions.AuthenticationFailed as e:
            return None
        return user

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            # Djano Admin treats None user as anonymous your who have no right at all.
            return None
