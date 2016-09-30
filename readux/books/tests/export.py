from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from eulxml.xmlmap import load_xmlobject_from_file
from mock import patch, Mock
import os
import shutil
import subprocess
import tempfile

from readux.books.models import Volume
from readux.books.tei import AnnotatedFacsimile, Zone
from readux.books.export import VolumeExport, ExportException
from readux.books.tests.models import FIXTURE_DIR


class VolumeExportTest(TestCase):

    def setUp(self):
        self.vol = Volume(Mock())   # use a real volume, but Mock for api
        self.vol.pid = 'testvol:123'
        self.tei = load_xmlobject_from_file(os.path.join(FIXTURE_DIR,
                                                         'teifacsimile.xml'),
                                            AnnotatedFacsimile)

        self.tmpdir = tempfile.mkdtemp(prefix='rdx-export-test')
        # for now, use defaults for page one, callback, images
        self.exporter = VolumeExport(self.vol, self.tei)

    def tearDown(self):
        # remove tempdir and any temporary files created in it
        shutil.rmtree(self.tmpdir)

    def test_get_jekyll_site_dir(self):
        path = self.exporter.get_jekyll_site_dir('/tmp/')
        self.assertEqual('/tmp/123_annotated_jekyll_site', path)

    @patch('readux.books.export.logger')
    def test_log_status(self, mocklogger):
        mock_callback = Mock()
        exporter = VolumeExport(self.vol, self.tei,
                                update_callback=mock_callback)
        msg = 'test status update'
        exporter.log_status(msg)
        mocklogger.debug.assert_called_with(msg)
        mock_callback.assert_called_with(msg)

    def test_save_tei_file(self):
        teifile = self.exporter.save_tei_file(self.tmpdir)
        teifile_basename = os.path.basename(teifile.name)
        self.assert_(teifile_basename.endswith('.xml'))
        self.assert_(teifile_basename.startswith('tei-'))
        self.assertEqual(self.tmpdir, os.path.dirname(teifile.name))
        # check that filehandle is closed
        self.assertTrue(teifile.closed)

        # basic check of file contents
        # (could copare with fixture file... )
        with open(teifile.name) as teicontents:
            content = teicontents.read()
            self.assert_('<TEI' in content)
            self.assert_(content.endswith('</TEI>'))

    @patch('readux.books.export.subprocess')
    def test_import_tei_jekyll(self, mocksubprocess):
        teifile = self.exporter.save_tei_file(self.tmpdir)
        self.exporter.import_tei_jekyll(teifile, self.tmpdir)

        expected_cmd = [settings.JEKYLLIMPORT_TEI_SCRIPT, '-q', teifile.name]
        mocksubprocess.check_call.assert_called_with(expected_cmd,
                                                     cwd=self.tmpdir)

        # with page one option
        exporter = VolumeExport(self.vol, self.tei, page_one=5)
        expected_cmd.extend(['--page-one', '5'])
        exporter.import_tei_jekyll(teifile, self.tmpdir)
        mocksubprocess.check_call.assert_called_with(expected_cmd,
                                                     cwd=self.tmpdir)

        # with no deep zoom option
        exporter = VolumeExport(self.vol, self.tei, page_one=5,
                                deep_zoom='exclude')
        expected_cmd.extend(['--no-deep-zoom'])
        exporter.import_tei_jekyll(teifile, self.tmpdir)
        mocksubprocess.check_call.assert_called_with(expected_cmd,
                                                     cwd=self.tmpdir)

        mocksubprocess.check_call.side_effect = subprocess.CalledProcessError(-1, 'error')
        mocksubprocess.CalledProcessError = subprocess.CalledProcessError
        mock_callback = Mock()
        exporter = VolumeExport(self.vol, self.tei,
                                update_callback=mock_callback)

        # error
        with self.assertRaises(ExportException):
            exporter.import_tei_jekyll(teifile, self.tmpdir)
            mock_callback.assert_called_with(
                'Error running jekyll import on TEI facsimile', 'error')

    # TODO: test generate_website
    # TODO: test website_zip
    # TODO: test website_gitrepo
    # TODO: test update_gitrepo

    def test_iiif_url_to_local_path(self):
        # stock iiif image url from documentation
        defaults = '/full/full/0/default.jpg'
        path = 'abcd1234'
        iiif_url = 'http://www.example.org/image-service/%s%s' % \
            (path, defaults)
        image_path = self.exporter.iiif_url_to_local_path(iiif_url)
        self.assertEqual(image_path, 'images/%s%s' % (path, defaults))

        # info urls should return as info urls
        iiif_info = 'http://www.example.org/image-service/%s/info.json' % \
            path
        print iiif_info
        image_path = self.exporter.iiif_url_to_local_path(iiif_info)
        self.assertEqual(image_path, 'images/%s/info.json' % path)

        with override_settings(IIIF_ID_PREFIX='test:',
                               FEDORA_PIDSPACE='testpid'):
            image_id = '123|1'
            iiif_url = ''.join(['http://lor.is/test:testpid:',
                                image_id, defaults])
            image_path = self.exporter.iiif_url_to_local_path(iiif_url)
            self.assertEqual('images/%s%s' % (image_id, defaults),
                             image_path)

    @patch('readux.books.export.save_url_to_file')
    def test_save_page_images(self, mocksaveurl_to_file):
        # sample test iiif image url
        defaults = '/full/full/0/default.jpg'
        image_id = 'abcd1234'
        iiif_url = 'http://img.ex/image-service/%s%s' % (image_id, defaults)

        # update tei with page image urls to test
        self.tei.page_list[0].graphics[0].rend = 'full'
        self.tei.page_list[0].graphics[0].url = iiif_url
        self.exporter.save_page_images(self.tmpdir)

        local_imgurl = ''.join(['images/', image_id, defaults])
        # test that tei graphic url is updated as expected
        self.assertEqual(local_imgurl, self.tei.page_list[0].graphics[0].url)
        # test that expected dirs are created
        img_dir = os.path.dirname(local_imgurl)
        # work backwards through dirnames for each path portion
        while img_dir:
            self.assertTrue(os.path.isdir(os.path.join(self.tmpdir, img_dir)))
            img_dir = os.path.dirname(img_dir)

        img_path = os.path.join(self.tmpdir, local_imgurl)
        # test that save_url_to_file is called as expected
        mocksaveurl_to_file.assert_called_with(iiif_url, img_path)

    @patch('readux.books.export.IIIFStatic')
    @patch('readux.books.export.IIIFImageClient')
    def test_generate_deep_zoom(self, mockiiifimgclient, mockiiifstatic):
        # update tei with info url to test with
        defaults = '/full/full/0/default.jpg'
        image_id = 'abcd1234'
        iiif_url = '%s/%s%s' % (VolumeExport.image_dir, image_id, defaults)
        # deep zoom looks for master/full image as source for generating
        # deep zoom
        teigraphic = self.tei.page_list[0].graphics[0]
        teigraphic.rend = 'full'
        teigraphic.url = iiif_url
        mockiiifimgclient.init_from_url.return_value.image_id = image_id

        self.exporter.generate_deep_zoom(self.tmpdir)

        imgdir = os.path.join(self.tmpdir, 'images')
        mockiiifstatic.assert_called_with(dst=imgdir, prefix='/images/')
        mockiiifimgclient.init_from_url.assert_called_with(teigraphic.url)
        expected_src = os.path.join(self.tmpdir, teigraphic.url)
        mockiiifstatic.return_value.generate.assert_called_with(
            expected_src, identifier=image_id)
