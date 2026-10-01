from apps.utils.noid import encode_noid
from time import time
from unittest.mock import patch
from django.test import TestCase
from elasticsearch.dsl import connections
from apps.users.tests.factories import UserFactory
from apps.iiif.manifests.tests.factories import ManifestFactory, ImageServerFactory
from apps.iiif.canvases.tests.factories import CanvasFactory
from .fetch import fetch_url
from .noid import _digits, decode_noid, encode_noid
from .search_signals import ScopedCelerySignalProcessor
import httpretty
import json

class TestUtils(TestCase):
    @httpretty.activate
    def test_fetching_url_text(self):
        httpretty.register_uri(httpretty.GET, 'http://readux.org', body='The best thing ever!')
        response = fetch_url('http://readux.org', data_format='text')
        assert response == 'The best thing ever!'

    @httpretty.activate
    def test_fetching_url_json(self):
        httpretty.register_uri(httpretty.GET, 'http://readux.org', body='{"key": "value"}')
        response = fetch_url('http://readux.org')
        assert response == json.loads('{"key": "value"}')

    @httpretty.activate
    def test_returning_non_text_and_non_json_content(self):
        httpretty.register_uri(httpretty.GET, 'http://foo.info', body='hello')
        response = fetch_url('http://foo.info', data_format='other')
        assert response.decode('UTF-8') == 'hello'

    def test_timeout(self):
        with self.assertLogs('apps.utils', level='WARN') as cm:
            fetch_url('http://archive.org', timeout=.0000000001, verbosity=3)
            assert 'timeoutout' in cm.output[0]
            assert 'WARNING' in cm.output[0]

    def test_connection_refused(self):
        with self.assertLogs('apps.utils', level='WARN') as cm:
            fetch_url('http://localhost:666', verbosity=3)
            assert 'failed' in cm.output[0]
            assert 'WARNING' in cm.output[0]

    def test_response_bad_content(self):
        with self.assertLogs('apps.utils', level='WARN') as cm:
            fetch_url('http://cnn.com', verbosity=3)
            assert 'bad content' in cm.output[0]
            assert 'WARNING' in cm.output[0]

    def test_digits_with_empty_sting(self):
        assert _digits('') == []

    def test_noid_decode(self):
        now = int(time())
        noid = encode_noid(now)
        assert noid != now
        assert decode_noid(noid) == now


class TestScopedCelerySignalProcessor(TestCase):
    """CelerySignalProcessor connects post_save/post_delete globally (no
    sender=), dispatching two Celery tasks for every model save in the
    project -- ScopedCelerySignalProcessor should only fire for models
    actually registered (directly or via related_models) with the
    Elasticsearch document registry."""

    def setUp(self):
        self.processor = ScopedCelerySignalProcessor(connections)

    def tearDown(self):
        self.processor.teardown()

    def test_indexed_model_save_dispatches_tasks(self):
        manifest = ManifestFactory.create(image_server=ImageServerFactory.create())
        with patch.object(
            ScopedCelerySignalProcessor, "registry_update_task"
        ) as mock_task, patch.object(
            ScopedCelerySignalProcessor, "registry_update_related_task"
        ) as mock_related_task:
            CanvasFactory.create(manifest=manifest)

        assert mock_task.delay.called
        assert mock_related_task.delay.called

    def test_unrelated_model_save_does_not_dispatch_tasks(self):
        with patch.object(
            ScopedCelerySignalProcessor, "registry_update_task"
        ) as mock_task, patch.object(
            ScopedCelerySignalProcessor, "registry_update_related_task"
        ) as mock_related_task:
            UserFactory.create()

        assert not mock_task.delay.called
        assert not mock_related_task.delay.called
