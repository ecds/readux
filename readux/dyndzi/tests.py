from django.core.urlresolvers import reverse
from django.http import Http404
from django.test import TestCase
from eulfedora.util import RequestFailed
from mock import patch, Mock

from readux.dyndzi.models import DziImage
from readux.dyndzi.views import get_image_object_or_404


testimg = Mock()
testimg.width = 5
testimg.height = 9

class DziImageTest(TestCase):

    def test_init(self):
        dzimg = DziImage(testimg)
        self.assertEqual(testimg.width, dzimg.width)
        self.assertEqual(testimg.height, dzimg.height)

        # overrides
        dzimg = DziImage(testimg, tilesize=15, overlap=3,
                         format='png')
        self.assertEqual(15, dzimg.tilesize)
        self.assertEqual(3, dzimg.overlap)
        self.assertEqual('png', dzimg.format)

        
class DynDziViewsTestCase(TestCase):

    @patch('readux.dyndzi.views.TypeInferringRepository')
    def test_get_image_object_or_404(self, mockrepo):
        # simulate fedora error
        mockrepo.return_value.get_object.side_effect = Exception
        self.assertRaises(Http404, get_image_object_or_404, 'rqst', id)

    @patch('readux.dyndzi.views.TypeInferringRepository')
    def test_image_dzi(self, mockrepo):
        dzi_url = reverse('deepzoom:dzi', kwargs={'id': 'img:1'})
        mockrepo.return_value.get_object.return_value = testimg
        response = self.client.get(dzi_url)
        self.assertEqual('application/xml', response['Content-type'])
        self.assertContains(response, 'Width="%d' % testimg.width)
        self.assertContains(response, 'Height="%d' % testimg.height)

    @patch('readux.dyndzi.views.TypeInferringRepository')
    def test_dzi_tile(self, mockrepo):
        tile_args = {
            'id': 'img:1',
            'level': 1,
            'column': 1,
            'row': 1,
            'format': 'jpg'
        }
        dzitile_url = reverse('deepzoom:tile', kwargs=tile_args)
        mockrepo.return_value.get_object.return_value = testimg
        response = self.client.get(dzitile_url)
        self.assertEqual('image/jpeg', response['Content-type'])
        testimg.get_region_assert_called()
        # NOTE: for now, not testing resize/crop specifics

        bad_args = tile_args.copy()
        bad_args.update({'column': 55 })   # column out of range
        dzitile_bad_url = reverse('deepzoom:tile', kwargs=bad_args)
        response = self.client.get(dzitile_bad_url)
        expected, got = 400, response.status_code
        self.assertEqual(expected, got,
            'Expected %s (bad request) but returned %s for %s' \
                % (expected, got, dzitile_bad_url))
        
        bad_args = tile_args.copy()
        bad_args.update({'row': 87 })   # column out of range
        dzitile_bad_url = reverse('deepzoom:tile', kwargs=bad_args)
        response = self.client.get(dzitile_bad_url)
        expected, got = 400, response.status_code
        self.assertEqual(expected, got,
            'Expected %s (bad request) but returned %s for %s' \
                % (expected, got, dzitile_bad_url))
