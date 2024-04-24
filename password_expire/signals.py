# pylint:disable=missing-module-docstring
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model, logout, user_logged_in
from django.db import DEFAULT_DB_ALIAS
from django.db.models import signals
from django.utils import timezone

from .model import ForcePasswordChange, PasswordChange
from .util import PasswordChecker

UserModel = get_user_model()

def force_password_change_for_new_users(sender, instance, created, **kwargs): # pylint:disable=unused-argument
    """
    when the user is created, set password change flag
    """
    if created:
        queryset = ForcePasswordChange.objects
        if kwargs['using'] and kwargs['using'] != DEFAULT_DB_ALIAS:
            queryset.using(kwargs['using'])

        queryset.create(user=instance)


def redirect_to_change_password(sender, request, user, **kwargs): # pylint:disable=unused-argument
    """
    redirect if force password change is set
    """
    try:
        queryset = ForcePasswordChange.objects
        using = kwargs.get('using', DEFAULT_DB_ALIAS)
        if using and using != DEFAULT_DB_ALIAS:
            queryset = queryset.using(kwargs['using'])
        queryset.get(user=user)
        messages.error(request, "Your password has expired and must be changed.")
        # set flag for middleware to pick up
        request.redirect_to_password_change = True
        request.expired_user = request.user
    except ForcePasswordChange.DoesNotExist: # pylint:disable=no-member
        pass


def remove_force_password_record(sender, instance, **kwargs): # pylint:disable=unused-argument
    """
    user changing password so remove force change record
    contrib/auth/base_user.py sets _password in set_password()
    """
    if instance._password is None: # pylint:disable=protected-access
        return

    try:
        queryset = ForcePasswordChange.objects
        using = kwargs.get('using', DEFAULT_DB_ALIAS)
        if using and using != DEFAULT_DB_ALIAS:
            queryset = queryset.using(kwargs['using'])
        queryset.filter(user=instance).delete()
    except ForcePasswordChange.DoesNotExist: # pylint:disable=no-member
        pass


def create_user_handler(sender, instance, created, **kwargs): # pylint:disable=unused-argument
    """
    when the user is created, set the password last changed field to now
    """
    if created:
        queryset = PasswordChange.objects # pylint:disable=no-member
        using = kwargs.get('using', DEFAULT_DB_ALIAS)
        if using and using != DEFAULT_DB_ALIAS:
            queryset = queryset.using(kwargs['using'])
        queryset.create(user=instance, last_changed=timezone.now()) # pylint:disable=no-member


def change_password_handler(sender, instance, **kwargs): # pylint:disable=unused-argument
    """
    Checks if the user changed password
    contrib/auth/base_user.py sets _password in set_password()
    """
    if instance._password is None: # pylint:disable=protected-access
        return

    try:
        queryset = UserModel.objects
        using = kwargs.get('using', DEFAULT_DB_ALIAS)
        if using and using != DEFAULT_DB_ALIAS:
            queryset = queryset.using(kwargs['using'])
        queryset.get(uuid=instance.uuid)
    except UserModel.DoesNotExist:
        return

    queryset = PasswordChange.objects # pylint:disable=no-member
    using = kwargs.get('using', DEFAULT_DB_ALIAS)
    if using and using != DEFAULT_DB_ALIAS:
        queryset = queryset.using(kwargs['using'])

    record, _ign = queryset.get_or_create(user=instance)
    record.last_changed = timezone.now()
    record.save()


def login_handler(sender, request, user, **kwargs): # pylint:disable=unused-argument
    """
    Redirects to password change screen if password expired
    """
    checker = PasswordChecker(request.user)
    if checker.is_expired() or (timezone.now() > request.user.forced_password_expiration):
        if hasattr(settings, 'PASSWORD_EXPIRE_CONTACT'):
            contact = settings.PASSWORD_EXPIRE_CONTACT
        else:
            contact = "your administrator"

        # pylint:disable=line-too-long
        link = f'<a href="mailto:{settings.DEFAULT_FROM_EMAIL}?subject=Password Expiration Help" class="alert-link">{contact}</a>'
        messages.error(request, "Your password has expired and must be changed.")
        messages.error(request, f"If you need assistance, please contact {link}.", extra_tags='safe')
        # pylint:enable=line-too-long

        request.redirect_to_password_change = True
        request.expired_user = request.user
        logout(request)


def register_signals():
    """
    Connect the above handlers to Django's available signals.
    """
    if hasattr(settings, 'PASSWORD_EXPIRE_FORCE') and settings.PASSWORD_EXPIRE_FORCE:
        signals.post_save.connect(
            force_password_change_for_new_users,
            sender=settings.AUTH_USER_MODEL,
            dispatch_uid="password_expire:force_password_change_for_new_users",
        )

    user_logged_in.connect(
        redirect_to_change_password,
        dispatch_uid="password_expire:redirect_to_change_password"
    )

    signals.pre_save.connect(
        remove_force_password_record,
        sender=settings.AUTH_USER_MODEL,
        dispatch_uid="password_expire:remove_force_password_record",
    )

    signals.post_save.connect(
        create_user_handler,
        sender=settings.AUTH_USER_MODEL,
        dispatch_uid="password_expire:create_user_handler",
    )

    signals.pre_save.connect(
        change_password_handler,
        sender=settings.AUTH_USER_MODEL,
        dispatch_uid="password_expire:change_password_handler",
    )

    user_logged_in.connect(
        login_handler,
        dispatch_uid="password_expire:login_handler"
    )
