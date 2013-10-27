from django import forms
from django.forms import ModelForm
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth import get_user_model; User = get_user_model()

from userware.forms import UserCreationForm
from utils import check_email
import defaults

class SignupForm(UserCreationForm):
    """ Simple Signup Form """

    required_css_class = 'required_field'

    def clean_email(self):
        email = super(SignupForm, self).clean_email()
        if check_email(email):
            return email
        raise forms.ValidationError(_("Email address does not exist. Please try again."))

    def save(self):
        username = self.cleaned_data["username"]
        email = self.cleaned_data["email"]
        password = self.cleaned_data["password1"]

        new_user = User.objects.create_user(username, email, password)
        new_user.is_active = True
        new_user.save()
        return new_user

    class Meta:
        model = User
        fields = ("username", "email")





