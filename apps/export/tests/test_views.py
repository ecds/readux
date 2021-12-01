'''
'''
from django.test import TestCase
from django.contrib.auth import get_user_model
from allauth.socialaccount.models import SocialAccount
from apps.export.forms import JekyllExportForm

class ManifestTests(TestCase):
    fixtures = ['users.json']

    def setUp(self):
        self.user = get_user_model().objects.get(pk=111)

    def test_form_mode_choices_no_github(self):
        form = JekyllExportForm(user=self.user)
        assert len(form.fields['mode'].choices) == 1
        assert form.fields['mode'].choices[0] != 'github'

    def test_form_mode_choices_with_github(self):
        sa = SocialAccount(provider='github', user=self.user)
        sa.save()
        form = JekyllExportForm(user=self.user)
        assert len(form.fields['mode'].choices) == 2
        assert form.fields['mode'].choices[1][0] == 'github'
