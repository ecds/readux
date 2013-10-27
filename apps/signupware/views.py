# -*- coding: utf-8 -*-
from django.conf import settings
from django.shortcuts import render_to_response
from django.views.generic.edit import FormView
from django.contrib.auth import login
from django.contrib.auth import authenticate
from django.core.urlresolvers import reverse_lazy
from django.contrib import messages
from django.shortcuts import redirect
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth import get_user_model; User = get_user_model()

from toolware.utils.mixin import LoginRequiredMixin
from toolware.utils.mixin import CsrfProtectMixin
from toolware.utils.mixin import NeverCacheMixin
from toolware.utils.mixin import SensitivePostParametersMixin

from forms import SignupForm
import signals
import defaults

class SignupFormProcessView(
    SensitivePostParametersMixin,
    CsrfProtectMixin,
    NeverCacheMixin,
    FormView
    ):
    """ This is where the signup happens """

    form_class = SignupForm
    template_name = "signup/signup_form.html"
    success_url = reverse_lazy('profileware_personal_update')

    def _auth_login(self, request, *args, **kwargs):
        """ Authenticate new user and log'm in"""

        username, password = kwargs['username'], kwargs['password1']
        new_user = authenticate(username=username, password=password)
        login(request, new_user)
        messages.add_message(request, messages.SUCCESS, 
                _("Congratulations! You are now logged in as '%s'." % new_user.username))
        signals.signup_new.send(sender=self.__class__, request=request, user=new_user)

    def post(self, request, *args, **kwargs):
        """ Process user signup """

        import pdb; pdb.set_trace()
        form = self.get_form(self.get_form_class())
        if form.is_valid():
            form.save()
            self._auth_login(request, **form.cleaned_data)
            return self.form_valid(form)
        else:
            return self.form_invalid(form)

    def get(self, request, *args, **kwargs):
        """ Process user signup for unauthenticated users """

        if request.user.is_authenticated():
            return redirect(defaults.LOGIN_REDIRECT_URL)
        return super(SignupFormProcessView, self).get(request, *args, **kwargs)





