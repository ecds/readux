import json
from django.contrib import messages
from django.shortcuts import render_to_response
from django.utils.decorators import method_decorator
from django.utils.translation import ugettext_lazy as _
from django.views.generic import UpdateView
from django.views.generic import TemplateView
from django.core.urlresolvers import reverse_lazy, reverse
from django.shortcuts import get_object_or_404, Http404
from django.template import RequestContext, loader
from django.http import HttpResponseRedirect, HttpResponseNotAllowed, HttpResponse
from django.contrib.auth import get_user_model; User = get_user_model()

from toolware.utils.mixin import LoginRequiredMixin, CsrfProtectMixin, PostRequestOnlyMixin

from forms import UserPersonalForm, UserPreferencesForm
import signals

class UserPersonalUpdateView(
    LoginRequiredMixin,
    CsrfProtectMixin,
    UpdateView
    ):
    """ User update personal info view """

    form_class = UserPersonalForm
    template_name = "profile/personal_update_form.html"
    success_url = reverse_lazy('profileware_personal_update')

    def get_object(self, queryset=None):
        user = self.request.user
        return user

    def form_valid(self, form):
        self.object = form.save()
        messages.add_message (self.request, messages.SUCCESS,
                _('Your personal details saved'))
        signals.user_personal_updated.send(sender=User, request=self.request, user=self.object)
        return HttpResponseRedirect(self.get_success_url())

    def get(self, *args, **kwargs):
        self.object = self.get_object()
        if not self.object.first_name:
            messages.add_message(self.request, messages.WARNING,
                _('Your account must have first name and last name. Please enter your name now.'))
        return super(UserPersonalUpdateView, self).get(*args, **kwargs)


class UserPreferencesUpdateView(
    LoginRequiredMixin,
    CsrfProtectMixin,
    UpdateView
    ):
    """ User Profile preferences update view """

    form_class = UserPreferencesForm
    template_name = "profile/preferences_update_form.html"
    success_url = reverse_lazy('profileware_preferences_update')

    def get_object(self, queryset=None):
        obj = self.request.user
        return obj

    def form_valid(self, form):
        self.object = form.save()
        messages.add_message (self.request, messages.SUCCESS,
                _('Your account preferences saved'))
        signals.user_preferences_updated.send(sender=User, request=self.request, user=self.object)
        return HttpResponseRedirect(self.get_success_url())




