from django.test import TestCase
from .fetch import fetch_url
import httpretty
import json

class TestUtils(TestCase):
    @httpretty.activate
    def test_fetching_url_text(self):
        httpretty.register_uri(httpretty.GET, 'http://readux.org', body='The best thing ever!')
        response = fetch_url('http://readux.org', format='text')
        assert response == 'The best thing ever!'

    @httpretty.activate
    def test_fetching_url_json(self):
        httpretty.register_uri(httpretty.GET, 'http://readux.org', body='{"key": "value"}')
        response = fetch_url('http://readux.org')
        assert response == json.loads('{"key": "value"}')
    
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
