# pylint:disable=missing-module-docstring
from django.apps import AppConfig
from . import signals

class PasswordExpireConfig(AppConfig):
    # pylint:disable=missing-class-docstring
    name = 'password_expire'

    def ready(self):
        signals.register_signals()
