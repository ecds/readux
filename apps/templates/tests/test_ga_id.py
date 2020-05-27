"""Test Django Context Processor that makes a Google Analytics ID avaliable to templats."""
from django.conf import settings
from django.test import RequestFactory
import apps.templates.context_processors as cp

FACTORY = RequestFactory()
REQUEST = FACTORY.get('/')

class TestGoogleAnalyticsIdContext():

    def test_does_not_has(self):
        settings.GOOGLE_ANALYTICS_ID = 'U-XXXXXXXX-Y'
        assert cp.has_ga_tracking_id(REQUEST) == {'has_ga_tracking_id': True}

    def test_returns_dict_with_ga_id(self):
        assert cp.ga_tracking_id(REQUEST) == {'ga_tracking_id': settings.GOOGLE_ANALYTICS_ID}

    def test_does_not_have_id(self):
        del settings.GOOGLE_ANALYTICS_ID
        assert cp.has_ga_tracking_id(REQUEST) == {'has_ga_tracking_id': False}

    def test_returns_empty_dict_when_no_ga_id(self):
        del settings.GOOGLE_ANALYTICS_ID
        assert cp.ga_tracking_id(REQUEST) == {}
