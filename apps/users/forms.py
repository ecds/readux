from django.contrib.auth import get_user_model, forms
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _
from allauth.socialaccount.forms import SignupForm
from django.forms import CharField

User = get_user_model()


class UserChangeForm(forms.UserChangeForm):

    class Meta(forms.UserChangeForm.Meta):
        model = User


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
    class Meta:
        model = get_user_model()
        fields = ['name']
    name = CharField(max_length=30, label='User Name to associate with Annotations')

    def signup(self):
        user = super(MyCustomSocialSignupForm, self).save()
        user.name = self.cleaned_data['name']
        user.save()