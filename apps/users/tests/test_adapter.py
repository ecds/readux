from django.test import RequestFactory, TestCase
from apps.users.adapters import AccountAdapter, SocialAccountAdapter
from apps.users.tests.factories import UserFactory, SocialAccountFactory
from apps.users.forms import ReaduxSocialSignupForm

class AdapterTest(TestCase):

    def setUp(self):
        self.factory = RequestFactory()
        self.request = self.factory.get('/')

    def test_account_adapter_signup(self):
        aa = AccountAdapter()
        assert aa.is_open_for_signup(self.request)
    
    def test_social_account_adapter_signup(self):
        saa = SocialAccountAdapter(self.request)
        assert saa.is_open_for_signup(self.request, 'google')

    def test_account_adapter_user_save(self):
        proto_user = UserFactory.build()
        proto_sa = SocialAccountFactory.build(user = proto_user)
        saa = SocialAccountAdapter(self.request)
        form = ReaduxSocialSignupForm(
            {
                "name": proto_user.name,
                "agree": True,
                "sociallogin": proto_sa,
                "email": proto_user.email,
                "username": proto_user.username
            },
            sociallogin=proto_sa
        )
        assert form.is_valid()
        proto_user.save()
        proto_sa.user = proto_user
        saa.save_user(self.request, proto_sa, form)
        assert proto_sa.user == proto_user
        assert not proto_sa._state.adding
