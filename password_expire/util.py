# pylint:disable=missing-module-docstring
from datetime import timedelta

from django.conf import settings
from django.utils import timezone
import humanize

from .model import PasswordChange


def change_forced_by_admin(user):
    """
    Checks for the presence of a forced password expiration date, set by admin;
    true if date is in the past relative to now.
    """
    if not user.forced_password_expiration:
        return False

    return timezone.now() > user.forced_password_expiration

class PasswordChecker:
    """
    Checks if password has expired or if it will expire soon
    """
    def __init__(self, user):
        # password expires: last_changed + password_duration
        self.password_allowed_duration = timedelta(seconds=settings.PASSWORD_EXPIRE_SECONDS)
        # start warning at password expiration - duration
        self.password_warning_duration = timedelta(seconds=settings.PASSWORD_EXPIRE_WARN_SECONDS)

        self.user = user
        self.last_changed = self.get_last_changed()
        self.expiration = self.last_changed + self.password_allowed_duration
        self.warning = self.expiration - self.password_warning_duration

    def is_expired(self): # pylint:disable=missing-function-docstring
        if self.is_user_excluded():
            return False
        return timezone.now() > self.expiration

    def is_warning(self): # pylint:disable=missing-function-docstring
        if self.is_user_excluded():
            return False
        return timezone.now() > self.warning

    def get_expire_time(self):
        """
        Gets the expiration time as string if within the warning duration.
        Otherwise, returns None.
        """
        if self.is_warning():
            time_left = self.expiration - timezone.now()
            return humanize.naturaldelta(time_left)

        return None

    def get_last_changed(self):
        """
        if no record, return now()
        """
        try:
            record = PasswordChange.objects.get(user=self.user) # pylint:disable=no-member
            last_changed = record.last_changed
        except PasswordChange.DoesNotExist: # pylint:disable=no-member
            last_changed = timezone.now()
        return last_changed

    def is_user_excluded(self):
        """
        admin can configure so superusers are excluded from check
        """
        if hasattr(settings, 'PASSWORD_EXPIRE_EXCLUDE_SUPERUSERS') and\
                settings.PASSWORD_EXPIRE_EXCLUDE_SUPERUSERS:
            return self.user.is_superuser
        return False
