from typing import Any, Sequence
from allauth.socialaccount.models import SocialAccount, SocialApp, SocialToken
from django.contrib.auth import get_user_model
from factory.django import DjangoModelFactory
from factory import Faker, post_generation

class UserFactory(DjangoModelFactory):

    username = Faker("user_name")
    email = Faker("email")
    name = Faker("name")
    is_superuser = False
    is_staff = False
    is_active = True

    @post_generation
    def password(self, create: bool, extracted: Sequence[Any], **kwargs):
        self.set_password('Pa55word!$')

    class Meta: # pylint: disable=too-few-public-methods, missing-class-docstring
        model = get_user_model()
        django_get_or_create = ["username"]

class SocialAccountFactory(DjangoModelFactory):
    provider = Faker("user_name")
    uid = Faker("uuid4")
    class Meta: # pylint: disable=too-few-public-methods, missing-class-docstring
        model = SocialAccount

class SocialAppFactory(DjangoModelFactory):
    provider = Faker('name')
    name = Faker('name')
    client_id = Faker('ssn')
    secret = Faker("postalcode")

    class Meta: # pylint: disable=too-few-public-methods, missing-class-docstring
        model = SocialApp
        django_get_or_create = ["provider"]

class SocialTokenFactory(DjangoModelFactory):
    token = Faker('postalcode')
    token_secret = Faker('ssn')

    class Meta: # pylint: disable=too-few-public-methods, missing-class-docstring
        model = SocialToken