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

from toolware.utils.mixin import LoginRequiredMixin, CsrfProtectMixin, PostRequestOnlyMixin

from forms import UserProfileForm
from models import UserProfile
import signals

class UserProfileUpdateView(
    LoginRequiredMixin,
    CsrfProtectMixin,
    UpdateView
    ):
    """ User Profile update view """

    form_class = UserProfileForm
    template_name = "profile/profile_update_form.html"
    success_url = reverse_lazy('profileware_update')

    def get_object(self, queryset=None):
        profile = self.request.user.profile
        if not profile.location:
            self.success_url = reverse_lazy('profileware_update_location')
        return profile

    def form_valid(self, form):
        self.object = form.save()
        messages.add_message (self.request, messages.SUCCESS,
                _('Your profile is saved'))
        signals.profile_updated.send(sender=UserProfile, request=self.request, profile=self.object)
        return HttpResponseRedirect(self.get_success_url())

    def get(self, *args, **kwargs):
        self.object = self.get_object()
        if not self.object.first_name:
            messages.add_message(self.request, messages.WARNING,
                _('Your account must have first name and last name. Please enter your name now.'))
        return super(UserProfileUpdateView, self).get(*args, **kwargs)

