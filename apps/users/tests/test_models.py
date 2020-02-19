import pytest
from allauth.socialaccount.models import SocialAccount
from apps.users.tests.factories import UserFactory, SocialAccountFactory

pytestmark = pytest.mark.django_db


class TestSocialAccountList:

    def test_socialaccount_list(self):
        # A user with proto_user params does not exist yet.
        proto_user = UserFactory.create()
        socialaccounts = SocialAccountFactory.create_batch(3, user=proto_user)

        assert len(proto_user.socialaccount_list) == 3
        for sa in proto_user.socialaccount_set.all():
            assert sa.provider in proto_user.socialaccount_list
