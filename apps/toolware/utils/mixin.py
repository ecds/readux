import json
from django.contrib.auth.decorators import login_required
from django.views.decorators.debug import sensitive_post_parameters
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.cache import never_cache
from django.views.generic import DeleteView
from django.utils.decorators import method_decorator
from django.shortcuts import redirect
from django.http import HttpResponse
from django.conf import settings
from django.views.decorators.http import require_http_methods

from .. import defaults

class LoginRequiredMixin(object):
    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(LoginRequiredMixin, self).dispatch(*args, **kwargs)


class StaffRequiredMixin(object):
    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_staff:
            return super(StaffRequiredMixin, self).dispatch(request, *args, **kwargs)
        messages.error( 
                request,
                'user lacks sufficient permissions to perform the requested operation')
        return redirect(defaults.LOGIN_URL)


class SuperUserRequiredMixin(object): 
    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_superuser:
            return super(SuperUserRequiredMixin, self).dispatch(request, *args, **kwargs)
        messages.error(
                request,
                'user lacks sufficient permissions to perform the requested operation')
        return redirect(defaults.LOGIN_URL)


class SensitivePostParametersMixin(object):
    @method_decorator(sensitive_post_parameters())
    def dispatch(self, *args, **kwargs):
        return super(SensitivePostParametersMixin, self).dispatch(*args, **kwargs)


class CsrfProtectMixin(object):
    @method_decorator(csrf_protect)
    def dispatch(self, *args, **kwargs):
        return super(CsrfProtectMixin, self).dispatch(*args, **kwargs)


class NeverCacheMixin(object):
    @method_decorator(never_cache)
    def dispatch(self, *args, **kwargs):
        return super(NeverCacheMixin, self).dispatch(*args, **kwargs)


class DeleteMixin(DeleteView):
    def delete(self, request, *args, **kwargs):
        if request.is_ajax():
            super(DeleteMixin, self).delete(request, *args, **kwargs)
            return HttpResponse(json.dumps("success"), mimetype="application/json")
        else:
            return super(DeleteMixin, self).delete(request, *args, **kwargs)

class PostRequestOnlyMixin(object):
    @require_http_methods(["POST"])
    def dispatch(self, *args, **kwargs):
        return super(PostRequestOnlyMixin, self).dispatch(*args, **kwargs)

class GetRequestOnlyMixin(object):
    @require_http_methods(["GET"])
    def dispatch(self, *args, **kwargs):
        return super(GetRequestOnlyMixin, self).dispatch(*args, **kwargs)

class GetOrHeadOnlyMixin(object):
    @require_http_methods(["GET", "HEAD"])
    def dispatch(self, *args, **kwargs):
        return super(GetOrHeadOnlyMixin, self).dispatch(*args, **kwargs)


class CleanSpacesMixin(object):
    def clean(self):
        for field in self.cleaned_data:
            if isinstance(self.cleaned_data[field], basestring):
                self.cleaned_data[field] = self.cleaned_data[field].strip()
        return super(CleanSpacesMixin, self).clean()

    class Meta:
        abstract = True



