import pytest
from django.conf import settings
from django.urls import reverse, resolve

pytestmark = pytest.mark.django_db


def test_detail(user: settings.AUTH_USER_MODEL):
    # TODO: use f-strings once 3.5 support is dropped.
    # assert reverse("users:detail", kwargs={"username": user.username}) == f"/users/{user.username}/"
    assert reverse("users:detail", kwargs={"username": user.username}) == "/users/{u}/".format(u=user.username)
    # assert resolve(f"/users/{user.username}/").view_name == "users:detail"
    assert resolve("/users/{u}/".format(u=user.username)).view_name == "users:detail"


# def test_list():
#     assert reverse("users:list") == "/users/"
#     assert resolve("/users/").view_name == "users:list"


def test_update():
    assert reverse("users:update") == "/users/~update/"
    assert resolve("/users/~update/").view_name == "users:update"


def test_redirect():
    assert reverse("users:redirect") == "/users/~redirect/"
    assert resolve("/users/~redirect/").view_name == "users:redirect"
