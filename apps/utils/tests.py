from apps.utils.noid import encode_noid
from time import time
from django.test import TestCase
from .fetch import fetch_url
from .noid import _digits, decode_noid, encode_noid
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
