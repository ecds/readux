from django.contrib.auth import get_user_model, forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _
from allauth.socialaccount.forms import SignupForm
from django.forms import CharField, BooleanField, TextInput

User = get_user_model()


class UserChangeForm(forms.UserChangeForm):

    class Meta(forms.UserChangeForm.Meta):
        model = User


class ReduxUserChangeForm(UserChangeForm):
    password = None
    # username = CharField(
    #     widget=TextInput(attrs={'class': 'rdx-input uk-input'})
    # )
    # first_name = CharField(
    #     widget=TextInput(attrs={'class': 'rdx-input uk-input'})
    # )
    # last_name = CharField(
    #     widget=TextInput(attrs={'class': 'rdx-input uk-input'})
    # )
    name = CharField(
        widget=TextInput(attrs={"class": "rdx-input uk-input"}),
        help_text="User Name to associate with Annotations",
    )

    class Meta:  # pylint: disable=too-few-public-methods, missing-class-docstring
        model = User
        fields = []


class UserCreationForm(forms.UserCreationForm):

    error_message = forms.UserCreationForm.error_messages.update(
        {"duplicate_username": _("This username has already been taken.")}
    )

    class Meta(forms.UserCreationForm.Meta):
        model = User

    def clean_username(self):
        username = self.cleaned_data["username"]

        try:
            User.objects.get(username=username)
        except User.DoesNotExist:
            return username

        raise ValidationError(self.error_messages["duplicate_username"])


class ReaduxSocialSignupForm(SignupForm):
    class Meta:  # pylint: disable=too-few-public-methods, missing-class-docstring
        model = User
        fields = ["name"]

    name = CharField(max_length=30, label="User Name to associate with Annotations")
    agree = BooleanField(
        label='Check this box to confirm that you agree to the full Readux Terms of Service found on the Terms of Service page. By creating an account on Readux, you acknowledge that: Any information I personally create and enter (from here "Data") will be stored and may be accessible to site administrators. My Data will not be publicly accessible unless I elect to make my Data public. The host of this site and the makers of Readux are not responsible for ensuring the stability or privacy of my Data. I agree to the full Readux Terms of Service.'
    )

    def signup(self, request, user):
        # user = super(ReaduxSocialSignupForm, self).save(request)
        cleaned_data = self.clean()
        user.name = cleaned_data["name"]
        user.save()
        return user
