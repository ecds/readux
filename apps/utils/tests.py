from django.test import TestCase
from .fetch import fetch_url
import httpretty
import json

class TestUtils(TestCase):
    @httpretty.activate
    def test_fetching_url_text(self):
        httpretty.register_uri(httpretty.GET, 'http://readux.org', body='The best thing ever!')
        response = fetch_url('http://readux.org', format='text')
        print(response)
        assert response == 'The best thing ever!'

    @httpretty.activate
    def test_fetching_url_json(self):
        httpretty.register_uri(httpretty.GET, 'http://readux.org', body='{"key": "value"}')
        response = fetch_url('http://readux.org')
        print(response)
        assert response == json.loads('{"key": "value"}')
    
    def test_timeout(self):
        with self.assertLogs('apps.utils', level='WARN') as cm:
            fetch_url('http://archive.org', timeout=.1, verbosity=3)
            self.assertEqual(cm.output[0], 'WARNING:apps.utils.fetch:Connection timeoutout for http://archive.org')
    
    def test_connection_refused(self):
        with self.assertLogs('apps.utils', level='WARN') as cm:
            fetch_url('http://localhost:666', verbosity=3)
            assert 'WARNING:apps.utils.fetch:Connection failed for http://localhost:666. ' in cm.output[0]
        
    def test_response_bad_content(self):
        with self.assertLogs('apps.utils', level='WARN') as cm:
            fetch_url('http://cnn.com', verbosity=3)
            self.assertEqual(cm.output[0], 'WARNING:apps.utils.fetch:Server send success status with bad content http://cnn.com')
