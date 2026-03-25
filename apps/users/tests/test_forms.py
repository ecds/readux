import pytest
from django.test import RequestFactory
from apps.users.tests.factories import UserFactory, SocialAccountFactory
from apps.users.forms import UserCreationForm, ReaduxSocialSignupForm

pytestmark = pytest.mark.django_db


class TestUserForm:

    def test_clean_username(self):
        # A user with proto_user params does not exist yet.
        proto_user = UserFactory.build()

        form = UserCreationForm(
            {
                "username": proto_user.username,
                "password1": proto_user._password,
                "password2": proto_user._password,
            }
        )

        assert form.is_valid()
        assert form.clean_username() == proto_user.username

        # Creating a user.
        form.save()

        # The user with proto_user params already exists,
        # hence cannot be created.
        form = UserCreationForm(
            {
                "username": proto_user.username,
                "password1": proto_user._password,
                "password2": proto_user._password,
            }
        )

        assert not form.is_valid()
        assert len(form.errors) == 1
        assert "username" in form.errors

    # class TestUserCreationForm:

    def test_signup(self):
        factory = RequestFactory()
        request = factory.post("/")
        proto_user = UserFactory.build()
        proto_sa = SocialAccountFactory.build(user=proto_user)
        form = ReaduxSocialSignupForm(
            {
                "name": proto_user.name,
                "agree": True,
                "sociallogin": proto_sa,
                "email": proto_user.email,
                "username": proto_user.username,
            },
            sociallogin=proto_sa,
        )
        assert form.is_valid()
        proto_user.save()
        proto_sa.user = proto_user
        saved_sa = form.signup(request, proto_sa)
        saved_sa = form.signup(request, proto_sa)
        assert not saved_sa._state.adding
        assert saved_sa.user == proto_user
