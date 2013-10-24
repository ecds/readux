from uuid import uuid4
from django import forms
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.forms import ReadOnlyPasswordHashField
from django.contrib.auth.forms import UserCreationForm as DjangoUserCreationForm
from django.contrib.auth.forms import UserChangeForm as DjangoUserChangeForm
from django.contrib.auth.forms import AuthenticationForm as DjangoAuthenticationForm
from django.contrib.auth.forms import PasswordResetForm as DjangoPasswordResetForm
from django.contrib.auth.forms import PasswordChangeForm as DjangoPasswordChangeForm
from django.contrib.auth.forms import SetPasswordForm as DjangoSetPasswordForm
from django.contrib.auth import get_user_model; User = get_user_model()

from toolware.utils.mixin import CleanSpacesMixin
from toolware.utils.generic import is_valid_email

from utils import force_logout
from utils import get_user_by_username_or_email
import defaults

class UserCreationForm(CleanSpacesMixin, DjangoUserCreationForm):
    """ Customized User Creation Form """

    required_css_class = 'required_field'
    pass_len = defaults.USERWARE_PASSWORD_MIN_LENGTH
    custom_error_messages = {
        'invalid_username': _("Username may only contain alphanumeric characters "
                              "or dashes and cannot begin or end with a dash. (maximum 30 characters)"),
        'duplicate_username': _("A user with that username already exists."),
        'duplicate_email': _("A user with that email already exists."),
        'password_too_short': _("Password too short! minimum length is") +" [{}]".format(defaults.USERWARE_PASSWORD_MIN_LENGTH),
    }
    
    username = forms.RegexField(
        label=_("Username"),
        min_length=defaults.USERWARE_USERNAME_MIN_LENGTH,
        max_length=defaults.USERWARE_USERNAME_MAX_LENGTH,
        regex=r"^[a-zA-Z0-9]+(-[a-zA-Z0-9]+)*$",
        help_text=_("Username may only contain alphanumeric or dashes and cannot begin or end with a dash."),
        error_messages={'invalid': custom_error_messages['invalid_username']},
    )

    email = forms.EmailField(required=True)

    def __init__(self, *args, **kwargs):
        super(UserCreationForm, self).__init__(*args, **kwargs)
        self.fields['email'].help_text = _("A valid email address")
        self.fields['password1'].help_text = _("Password minimum length is")+" [{}]".format(defaults.USERWARE_PASSWORD_MIN_LENGTH)
        self.fields.keyOrder = ['username','email', 'password1', 'password2']

    def clean_username(self):
        username = self.cleaned_data["username"]
        if username not in defaults.USERWARE_RESERVED_USERNAMES and len(username) >= defaults.USERWARE_USERNAME_MIN_LENGTH:
            try:
                User.objects.get(username__iexact=username)
            except User.DoesNotExist:
                return username
        raise forms.ValidationError(self.custom_error_messages['duplicate_username'])

    def clean_email(self):
        email = self.cleaned_data["email"]
        try:
            User.objects.get(email__iexact=email)
        except User.DoesNotExist:
            return email
        raise forms.ValidationError(self.custom_error_messages['duplicate_email'])

    def clean_password2(self):
        password2 = super(UserCreationForm, self).clean_password2()
        if len(password2) < self.pass_len:
            raise forms.ValidationError(self.custom_error_messages['password_too_short'])
        return password2


class UserChangeForm(CleanSpacesMixin, DjangoUserChangeForm):
    """ Customized User Change Form """

    required_css_class = 'required_field'
    custom_error_messages = {
        'invalid_username': _("Username may only contain alphanumeric characters "
                              "or dashes and cannot begin or end with a dash. (maximum 30 characters)"),
        'duplicate_username': _("A user with that username already exists."),
        'duplicate_email': _("A user with that email already exists."),
    }

    username = forms.RegexField(
        label=_("Username"),
        min_length=defaults.USERWARE_USERNAME_MIN_LENGTH,
        max_length=defaults.USERWARE_USERNAME_MAX_LENGTH,
        regex=r"^[a-zA-Z0-9]+(-[a-zA-Z0-9]+)*$",
        help_text=_("Username may only contain alphanumeric or dashes and cannot begin or end with a dash."),
        error_messages={'invalid': custom_error_messages['invalid_username']},
    )

    def clean_username(self):
        username = self.cleaned_data["username"]
        if username not in defaults.USERWARE_RESERVED_USERNAMES and len(username) >= defaults.USERWARE_USERNAME_MIN_LENGTH:
            users = User.objects.filter(username__iexact=username).exclude(id=self.instance.id)
            if not users:
                return username
        raise forms.ValidationError(self.custom_error_messages['duplicate_username'])

    def clean_email(self):        
        email = self.cleaned_data["email"]
        users = User.objects.filter(email__iexact=email).exclude(id=self.instance.id)
        if users:
            raise forms.ValidationError(self.custom_error_messages['duplicate_email'])
        return email


class UserAuthenticationForm(CleanSpacesMixin, DjangoAuthenticationForm):
    """ Customized authentication form """

    required_css_class = 'required_field'

    def __init__(self, *args, **kwargs):
        super(UserAuthenticationForm, self).__init__(*args, **kwargs)
        self.error_messages['invalid_login'] = _("Please enter your username or email address.")
        self.fields['username'].label = "Username or Email"
        self.fields['username'].help_text = _("Enter your username or email address.")


class UserPasswordResetForm(CleanSpacesMixin, DjangoPasswordResetForm):
    """ Customized password reset form """

    required_css_class = 'required_field'
    custom_error_messages = {
        'unknown_email': _("That email address doesn't have an associated "
                     "user account. Are you registered?"),
        'unusable_email': _("The user account associated with this email "
                      "address cannot reset the password."),
        'unknown_username': _("That username doesn't have an associated "
                     "user account. Are you registered?"),
        'unusable_username': _("The user account associated with this username "
                      "address cannot reset the password."),
    }

    # accept username or email
    email = forms.CharField(
            label=_("Username or Email"), 
            max_length=254,
            help_text = _("Enter your username or email address to receive "
                          "instructions on how to reset your password.")
    )

    def clean_email(self):
        """ Validates that an active user exists with the given username / email address """

        username_or_email = self.cleaned_data["email"]
        if is_valid_email(username_or_email):
            try:
                user = User.objects.get(email__iexact=username_or_email)
            except User.DoesNotExist:
                raise forms.ValidationError(self.custom_error_messages['unknown_email'])
            if not user.is_active:
                raise forms.ValidationError(self.custom_error_messages['unknown_email'])
            if not user.has_usable_password():
                raise forms.ValidationError(self.custom_error_messages['unusable_email'])
        else:
            try:
                user = User.objects.get(username__iexact=username_or_email)
            except User.DoesNotExist:
                raise forms.ValidationError(self.custom_error_messages['unknown_username'])
            if not user.is_active:
                raise forms.ValidationError(self.custom_error_messages['unknown_username'])
            if not user.has_usable_password():
                raise forms.ValidationError(self.custom_error_messages['unusable_username'])

        return user.email


class UserPasswordChangeForm(CleanSpacesMixin, DjangoPasswordChangeForm):
    """Customized password change form"""

    required_css_class = 'required_field'
    custom_error_messages = {
        'password_too_short': _("Password too short! minimum length is") +" [{}]".format(defaults.USERWARE_PASSWORD_MIN_LENGTH),
        'password_same_as_before': _("New password is too similar to the old password. Please choose a different password."),
    }

    USERWARE_STAY_LOGGED_IN = 1
    USERWARE_LOGOUT_OTHER_DEVICES = 2
    LOGOUT_OPTIONS=[
        (USERWARE_STAY_LOGGED_IN, _('Keep me logged in')),
        (USERWARE_LOGOUT_OTHER_DEVICES, _('Log me out of other devices')),
    ]

    logout_options = forms.ChoiceField(
        choices=LOGOUT_OPTIONS,
    )

    def __init__(self, *args, **kwargs):
        super(UserPasswordChangeForm, self).__init__(*args, **kwargs)
        self.fields['old_password'].label = _("Current Password")
        self.fields['old_password'].help_text = _("Please enter your current password.")
        self.fields['new_password1'].help_text = _("Please enter your new password.  Minimum length is")+" [{}].".format(defaults.USERWARE_PASSWORD_MIN_LENGTH)
        self.fields['new_password2'].help_text = _("Please confirm your new password.")

    def clean_new_password2(self):
        new_password2 = super(UserPasswordChangeForm, self).clean_new_password2()
        if len(new_password2) < defaults.USERWARE_PASSWORD_MIN_LENGTH:
            raise forms.ValidationError(self.custom_error_messages['password_too_short'])
        if self.user.check_password(new_password2):
            raise forms.ValidationError(self.custom_error_messages['password_same_as_before'])
        return new_password2


class UserSetPasswordForm(CleanSpacesMixin, DjangoSetPasswordForm):
    """ Customized password reset form """

    required_css_class = 'required_field'
    custom_error_messages = {
        'password_too_short': _("Password too short! minimum length is") +" [{}].".format(defaults.USERWARE_PASSWORD_MIN_LENGTH),
        'password_same_as_before': _("New password is too similar to the old password. Please choose a different password."),
    }

    def __init__(self, user, *args, **kwargs):
        super(UserSetPasswordForm, self).__init__(user, *args, **kwargs)
        self.fields['new_password1'].help_text = _("Password minimum length is")+" [{}]".format(defaults.USERWARE_PASSWORD_MIN_LENGTH)
        self.fields['new_password2'].help_text = _("For extra security, resetting your password will log you out on all other devices")

    def clean_new_password2(self):
        new_password2 = super(UserSetPasswordForm, self).clean_new_password2()
        if len(new_password2) < defaults.USERWARE_PASSWORD_MIN_LENGTH:
            raise forms.ValidationError(self.custom_error_messages['password_too_short'])
        if self.user.check_password(new_password2):
            raise forms.ValidationError(self.custom_error_messages['password_same_as_before'])
        force_logout(self.user)
        return new_password2


class UserDeletionForm(CleanSpacesMixin, forms.Form):
    """ Delete a user (account) form """

    required_css_class = 'required_field'

    username = forms.CharField(
            label=_("Username Confirmation"),
            help_text=_("Please enter your username to confirm."))

    password = forms.CharField(
            label=_("Password Confirmation"),
            widget=forms.PasswordInput,
            help_text=_("Please enter your password to confirm."))

    def __init__(self, user, *args, **kwargs):
        self.user = user
        super(UserDeletionForm, self).__init__(*args, **kwargs)

    def clean_username(self):
        username = self.cleaned_data['username']
        user = None
        try:
            user = User.objects.get(username=username)
        except:
            pass
        if self.user != user:
            raise forms.ValidationError(_("Invalid username. Your username is not") + " [{}].".format(username))
        return username

    def clean_password(self):
        password = self.cleaned_data["password"]
        if not self.user.check_password(password):
            raise forms.ValidationError(_("Invalid password, please try again."))
        return password


class UserSwitchForm(CleanSpacesMixin, forms.Form):
    """ Switch user """

    required_css_class = 'required_field'

    switched_username = forms.CharField(max_length=30, label=_('Username'),
                    help_text=_("Enter the username or the email address of the account you want to switch to."))

    def clean_switched_username(self):
        username = self.cleaned_data['switched_username']
        to_user = get_user_by_username_or_email(username)
        if not to_user:
            raise forms.ValidationError(_("Invalid username"))
        elif to_user.is_superuser:
            raise forms.ValidationError(_("Switching to a superuser account is not permitted."))
        return username



