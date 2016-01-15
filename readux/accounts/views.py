from django.contrib import messages
from django.core.urlresolvers import reverse
from django.views.generic import TemplateView
from eulcommon.djangoextras.http import HttpResponseSeeOtherRedirect


class AccountErrorView(TemplateView):
    '''Display an informative error message when a user gets an
    error linking their accounts. Currently only has text specific
    for "account already in use" error when a user tries to link
    a social auth account that is already been created.
    '''

    template_name = 'accounts/error.html'

    def get(self, request, *args, **kwargs):
        # This page is only relevant when someone has encountered an
        # error (which should set a message). To avoid confusion
        # with users staying on this error page after logging in
        # or out, redirect to the site home page when there
        # is no error message.
        if not messages.get_messages(request):
            return HttpResponseSeeOtherRedirect(reverse('site-index'))
        return super(AccountErrorView, self).get(request, *args, **kwargs)
