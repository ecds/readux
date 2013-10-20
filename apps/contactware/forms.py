import warnings
from django import forms
from django.conf import settings
from django.core.mail import send_mail
from django.template import loader
from django.template import RequestContext
from django.contrib.sites.models import Site
from django.utils.translation import ugettext as _
from django.utils import timezone

from django.core.mail import send_mail

from toolware.utils.mixin import CleanSpacesMixin


from models import ContactMessage
from utils import check_email, check_spam, daily_message_limit_reached
import defaults


class ContactForm(CleanSpacesMixin, forms.ModelForm):

    required_css_class = 'required_field'

    def __init__(self, *args, **kwargs):
        """ Check for the required configuration settings """

        self.request = kwargs.pop('request')

        super(ContactForm, self).__init__(*args, **kwargs)
        self.fields['referrer'].widget = forms.HiddenInput()
        self.fields['ip_address'].widget = forms.HiddenInput()
        if not defaults.CONTACTWARE_DEFAULT_FROM_EMAIL:
            raise ValidationError(_("You need to set DEFAULT_FROM_EMAIL in your settings"))
        if not defaults.CONTACTWARE_DEFAULT_TO_EMAILS:
            raise ValidationError(_("You need to set MANAGERS in your settings"))
        self.site = Site.objects.get_current()
        self.email_sent = False


    def get_message_subject(self):
        """ Returns the rendered version of the message subject without linebreak """

        subject = loader.render_to_string(
                        defaults.CONTACTWARE_MESSAGE_SUBJECT_TEMPLATE,
                        self.get_rendering_context())
        return ''.join(subject.splitlines())


    def get_message_body(self):
        """ Returns the rendered version of the message body """

        return loader.render_to_string(
                    defaults.CONTACTWARE_MESSAGE_BODY_TEMPLATE,
                    self.get_rendering_context())

    def get_message_dict(self):
        """ Returns a dict with all the required fields required for delivery """

        message_dict = {
            "subject": self.get_message_subject(),
            "message": self.get_message_body(),
            "from_email": defaults.CONTACTWARE_DEFAULT_FROM_EMAIL,
            "recipient_list": defaults.CONTACTWARE_DEFAULT_TO_EMAILS,
        }
        return message_dict


    def get_rendering_context(self):
        """ Returns the context that is used to render the subject/message """

        extra_context = dict(self.cleaned_data, site=self.site, time=timezone.now())
        return RequestContext(self.request, extra_context)


    def clean_name(self):
        """ Check to see if daily message limit is reached """

        name = self.cleaned_data.get('name', '')
        if daily_message_limit_reached(self.request):
            raise forms.ValidationError(_("Sorry, daily message limit has been reached!"))
        return name


    def clean_email(self):
        """ Check to see if email address exists and vouched for by the provider """

        email = self.cleaned_data['email']
        from_host = self.site.domain
        from_email = 'verify@{0}'.format(from_host)
        if 'spamware' in settings.INSTALLED_APPS:
            if not check_email(email, from_host, from_email):
                raise forms.ValidationError(_("Email address does not exist. Please enter a valid email."))
        return email


    def clean_message(self):
        """ Check to see if all required info are provided, then check message body for spam prior to sending email """

        name = self.cleaned_data.get('name', '')
        email = self.cleaned_data.get('email', '')
        message = self.cleaned_data['message']
        if name and email and message:
            if check_spam(self.request, name, email, message):
                raise forms.ValidationError(_("Sorry, but your message is flagged as spam!"))
        return message


    def save(self, fail_silently=False, commit=True, *args, **kwargs):
        """ Send the email out if the SEND flag is set, Save to DB if the SAVE flag is Set """

        if defaults.CONTACTWARE_SEND_EMAIL and not self.email_sent:
            send_mail(fail_silently=fail_silently, **self.get_message_dict())
            self.email_sent = True
            commit = defaults.CONTACTWARE_STORE_DB
        return super(ContactForm, self).save(commit, *args, **kwargs)


    class Meta:
        model = ContactMessage
        fields = ('name', 'email', 'subject', 'message', 'referrer', 'ip_address',)





