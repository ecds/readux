from django.contrib import messages
from django.utils.translation import ugettext_lazy as _
from django.views.generic.edit import CreateView
from django.views.generic import TemplateView
from django.core.urlresolvers import reverse_lazy
from django.contrib.sites.models import Site

from toolware.utils.mixin import CsrfProtectMixin
from ipware.ip import get_ip_address_from_request

from forms import ContactForm
from models import ContactMessage
import signals

class ContactFormView(CsrfProtectMixin, CreateView):
    """ Contact form view """

    form_class = ContactForm
    model = ContactMessage
    template_name = 'contact/contact_form.html'
    success_url = reverse_lazy('contactware_message_sent')

    def get_form_kwargs(self):
        kwargs = super(ContactFormView, self).get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

    def form_valid(self, form):
        self.object = form.save()
        signals.contact_sent.send(sender=ContactMessage, request=self.request, contact=self.object)
        return super(ContactFormView, self).form_valid(form)

    def get_initial(self):
        initial = super(ContactFormView, self).get_initial()
        initial = initial.copy()
        initial['referrer'] = self.request.META.get('HTTP_REFERER', 'Unknown')
        initial['ip_address'] = get_ip_address_from_request(self.request)
        if self.request.user.is_authenticated():
            initial['name'] = self.request.user.get_full_name()
            initial['email'] = self.request.user.email
            initial['subject'] = self.request.GET.get('page_title', '')
        return initial

class ContactMessageReceivedView(TemplateView):
    """ Message sent """

    template_name = 'contact/contact_message_received.html'

    def get_context_data(self, **kwargs):
        context = super(ContactMessageReceivedView, self).get_context_data(**kwargs)
        current_site = Site.objects.get_current()
        context.update({
            "site": current_site,
        })
        return context




