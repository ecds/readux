from django.contrib.auth.models import AbstractUser
from django.db.models import CharField, BooleanField
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _


class User(AbstractUser):

    # First Name and Last Name do not cover name patterns
    # around the globe.
    name = CharField(_("Name of User"), blank=True, max_length=255)
    agree = BooleanField(blank=True, null=True)

    def get_absolute_url(self):
        return reverse("users:detail", kwargs={"username": self.username})

    def fullname(self):
    	return str(self.first_name) + " " + str(self.last_name)

    @property
    def socialaccount_list(self):
        if self.socialaccount_set.all().exists():
            return [account.provider for account in self.socialaccount_set.all()]
        else:
            return []