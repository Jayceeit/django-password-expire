# pylint:disable=missing-module-docstring
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import logout
from django.shortcuts import redirect
from django.urls import resolve

from .util import PasswordChecker, user_has_been_forced


class PasswordExpireMiddleware:
    """
    Adds Django message if password expires soon.
    Checks if user should be redirected to change password.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if self.is_page_for_warning(request):
            # add warning if within the notification window for password expiration
            if request.user.is_authenticated:
                checker = PasswordChecker(request.user)
                if checker.is_expired() or user_has_been_forced(request.user): # pylint:disable=line-too-long
                    msg = 'Please change your password. It has expired.'
                    self.add_warning(request, msg)
                else:
                    time_to_expire_string = checker.get_expire_time()
                    if time_to_expire_string:
                        msg = f'Please change your password. It expires in {time_to_expire_string}.'
                        self.add_warning(request, msg)

        response = self.get_response(request)

        # picks up flag for forcing password change
        if getattr(request, 'redirect_to_password_change', False):
            if request.expired_user.has_elevated_privileges() or request.expired_user.has_perm('users.change_password'): # pylint:disable=line-too-long
                url = settings.PASSWORD_EXPIRE_CHANGE_REDIRECT_URL
            else:
                url = settings.PASSWORD_EXPIRE_RESET_REDIRECT_URL

            logout(request) # ensure user is not logged in despite being flagged
            return redirect(url, username=request.expired_user.get_username())

        return response

    def is_page_for_warning(self, request):
        """
        Only warn on pages that are GET requests and not ajax. Also ignore logouts.
        """
        if request.method == "GET" and not request.is_ajax():
            match = resolve(request.path)
            if match and match.url_name == 'logout':
                return False
            return True
        return False

    def add_warning(self, request, text):
        """
        Provide a warning to users whose password is about to expire
        """
        storage = messages.get_messages(request)
        for message in storage:
            # only add this message once
            if message.extra_tags is not None and 'password_expire' in message.extra_tags:
                return
        messages.warning(request, text, extra_tags='password_expire')
