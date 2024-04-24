# pylint:disable=missing-module-docstring
from django.apps import AppConfig

class PasswordExpireConfig(AppConfig):
    # pylint:disable=missing-class-docstring
    name = 'password_expire'

    def ready(self):
        from . import signals # pylint:disable=import-outside-toplevel
        signals.register_signals()
