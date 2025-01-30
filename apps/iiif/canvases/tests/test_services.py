"""
Test cases for :class:`apps.iiif.canvases`
"""

import json
from os.path import join
import boto3
import httpretty
from moto import mock_aws
from django.test import TestCase, Client
from django.urls import reverse
from django.core.serializers import serialize
from lxml.etree import XMLSyntaxError
import config.settings.local as settings
from apps.iiif.manifests.tests.factories import ManifestFactory, ImageServerFactory
from apps.iiif.annotations.tests.factories import AnnotationFactory
from apps.users.tests.factories import UserFactory
from apps.utils.noid import encode_noid
from ..models import Canvas
from .. import services
from ..apps import CanvasesConfig
from .factories import CanvasFactory


class CanvasTests(TestCase):
    fixtures = [
        "kollections.json",
        "manifests.json",
        "canvases.json",
        "annotations.json",
    ]

    def setUp(self):
        self.client = Client()
        self.canvas = Canvas.objects.get(pk="7261fae2-a24e-4a1c-9743-516f6c4ea0c9")
        self.manifest = self.canvas.manifest
        self.assumed_canvas_pid = "fedora:emory:5622"
        self.assumed_canvas_resource = "5622"
        self.assumed_volume_pid = "readux:st7r6"
        self.assumed_iiif_base = "https://loris.library.emory.edu"

    def set_up_mock_aws(self, manifest):
        conn = boto3.resource("s3", region_name="us-east-1")
        conn.create_bucket(Bucket=manifest.image_server.storage_path)

    def test_app_config(self):
        assert CanvasesConfig.verbose_name == "Canvases"
        assert CanvasesConfig.name == "apps.iiif.canvases"

    def test_ia_ocr_creation(self):
        valid_ia_ocr_response = {
            "ocr": [
                [["III", [120, 1600, 180, 1494, 1597]]],
                [["chambray", [78, 1734, 116, 1674, 1734]]],
                [["tacos", [142, 1938, 188, 1854, 1938]]],
                [["freegan", [114, 2246, 196, 2156, 2245]]],
                [["Kombucha", [180, 2528, 220, 2444, 2528]]],
                [
                    ["succulents", [558, 535, 588, 501, 535]],
                    ["Thundercats", [928, 534, 1497, 478, 527]],
                ],
                [
                    ["poke", [557, 617, 646, 575, 614]],
                    ["VHS", [700, 612, 1147, 555, 610]],
                    ["chartreuse ", [1191, 616, 1209, 589, 609]],
                    ["pabst", [1266, 603, 1292, 569, 603]],
                    ["8-bit", [1354, 602, 1419, 549, 600]],
                    ["narwhal", [1471, 613, 1566, 553, 592]],
                    ["XOXO", [1609, 604, 1670, 538, 596]],
                    ["post-ironic", [1713, 603, 1826, 538, 590]],
                    ["synth", [1847, 588, 1859, 574, 588]],
                ],
                [["lumbersexual", [1741, 2928, 1904, 2881, 2922]]],
            ]
        }

        canvas = Canvas.objects.get(pid="15210893.5622.emory.edu$95")
        canvas.manifest.image_server.server_base = "https://iiif.archivelab.org/iiif/"
        ocr = services.add_positional_ocr(canvas, valid_ia_ocr_response)
        assert len(ocr) == 17
        for word in ocr:
            assert "w" in word
            assert "h" in word
            assert "x" in word
            assert "y" in word
            assert "content" in word
            assert isinstance(word["w"], int)
            assert isinstance(word["h"], int)
            assert isinstance(word["x"], int)
            assert isinstance(word["y"], int)
            assert isinstance(word["content"], str)

    def test_fedora_ocr_creation(self):
        valid_fedora_positional_response = """523\t 116\t 151\t  45\tDistillery\r\n 704\t 117\t 148\t  52\tplaid,"\r\n""".encode(
            "UTF-8-sig"
        )

        ocr = services.add_positional_ocr(self.canvas, valid_fedora_positional_response)
        assert len(ocr) == 2
        for word in ocr:
            assert "w" in word
            assert "h" in word
            assert "x" in word
            assert "y" in word
            assert "content" in word
            assert isinstance(word["w"], int)
            assert isinstance(word["h"], int)
            assert isinstance(word["x"], int)
            assert isinstance(word["y"], int)
            assert isinstance(word["content"], str)

    def test_ocr_from_tei(self):
        tei = open("apps/iiif/canvases/fixtures/tei.xml", "r").read()
        ocr = services.parse_tei_ocr(tei)
        assert ocr[1]["content"] == "AEN DEN LESIIU"
        assert ocr[1]["h"] == 28
        assert ocr[1]["w"] == 461
        assert ocr[1]["x"] == 814
        assert ocr[1]["y"] == 185

    def test_line_by_line_from_tei(self):
        canvas = CanvasFactory.create(
            default_ocr="line", manifest=ManifestFactory.create()
        )
        ocr_file = open(
            join(settings.APPS_DIR, "iiif/canvases/fixtures/tei.xml"), "r"
        ).read()
        tei = services.parse_tei_ocr(ocr_file)
        services.add_ocr_annotations(canvas, tei)
        updated_canvas = Canvas.objects.get(pk=canvas.pk)
        ocr = updated_canvas.annotation_set.first()
        assert "mm" in ocr.content
        assert ocr.h == 26
        assert ocr.w == 90
        assert ocr.x == 916
        assert ocr.y == 0

        for num, anno in enumerate(updated_canvas.annotation_set.all(), start=1):
            assert anno.order == num

    def test_ocr_from_tsv(self):
        manifest = ManifestFactory.create(
            image_server=ImageServerFactory.create(
                server_base="https://images.readux.ecds.emory.fake/"
            )
        )
        canvas = CanvasFactory(manifest=manifest, pid="boo")
        manifest.refresh_from_db()
        # AnnotationFactory.create(x=459, y=391, w=89, h=43, order=1, canvas=canvas)
        # AnnotationFactory.create(x=453, y=397, w=397, h=3, order=2, canvas=canvas)
        # TODO: TOO MANY STEPS TO MAKE OCR????
        fetched_ocr = services.fetch_positional_ocr(canvas)
        parsed_ocr = services.add_positional_ocr(canvas, fetched_ocr)
        services.add_ocr_annotations(canvas, parsed_ocr)
        ocr = canvas.annotation_set.all().first()
        assert ocr.x == 459
        assert ocr.y == 391
        assert ocr.w == 89
        assert ocr.h == 43
        assert "Jordan" in ocr.content
        ocr2 = canvas.annotation_set.all()[1]
        assert ocr2.x == 453
        assert ocr2.y == 397
        assert ocr2.w == 397
        assert ocr2.h == 3
        assert "> </span>" in ocr2.content
        assert canvas.annotation_set.all().count() == 5

    def test_no_tei_from_empty_result(self):
        ocr = services.parse_tei_ocr(None)
        assert ocr is None

    def test_from_bad_tei(self):
        tei = open("apps/iiif/canvases/fixtures/bad_tei.xml", "r").read()
        self.assertRaises(XMLSyntaxError, services.parse_tei_ocr, tei)

    def test_canvas_detail(self):
        kwargs = {"manifest": self.manifest.pid, "pid": self.canvas.pid}
        url = reverse("RenderCanvasDetail", kwargs=kwargs)
        response = self.client.get(url)
        serialized_canvas = json.loads(response.content.decode("UTF-8-sig"))
        assert response.status_code == 200
        assert serialized_canvas["@id"] == self.canvas.identifier
        assert serialized_canvas["label"] == str(self.canvas.position)
        assert serialized_canvas["images"][0]["@id"] == self.canvas.anno_id
        assert serialized_canvas["images"][0]["resource"][
            "@id"
        ] == "%s/full/full/0/default.jpg" % (self.canvas.resource_id)

    def test_canvas_list(self):
        kwargs = {"manifest": self.manifest.pid}
        url = reverse("RenderCanvasList", kwargs=kwargs)
        response = self.client.get(url)
        canvas_list = json.loads(response.content.decode("UTF-8-sig"))

        assert response.status_code == 200
        assert len(canvas_list) == 2

    def test_wide_image_crops(self):
        pid = "15210893.5622.emory.edu$95"
        canvas = Canvas.objects.get(pid=pid)
        assert (
            canvas.thumbnail_crop_landscape
            == "%s/%s/pct:25,0,50,100/,250/0/default.jpg"
            % (canvas.manifest.image_server.server_base, canvas.resource)
        )
        assert (
            canvas.thumbnail_crop_tallwide
            == "%s/%s/pct:5,5,90,90/250,/0/default.jpg"
            % (canvas.manifest.image_server.server_base, canvas.resource)
        )
        assert canvas.thumbnail_crop_volume == "%s/%s/square/,600/0/default.jpg" % (
            canvas.manifest.image_server.server_base,
            canvas.resource,
        )

    def test_result_property(self):
        canvas = CanvasFactory.create(manifest=ManifestFactory.create())
        for order, word in enumerate(["a", "retto", ",", "dio", "Quefìa", "de'"]):
            AnnotationFactory.create(content=word, canvas=canvas, order=order + 1)
        assert canvas.result == "a retto , dio Quef\u00eca de'"

    def test_no_tei_for_internet_archive(self):
        self.canvas.manifest.image_server.server_base = (
            "https://iiif.archivelab.org/iiif/"
        )
        assert services.fetch_tei_ocr(self.canvas) is None

    def test_fetch_positional_ocr(self):
        self.canvas.manifest.image_server.server_base = (
            "https://iiif.archivelab.org/iiif/"
        )
        self.canvas.manifest.pid = "atlantacitydirec1908foot"
        self.canvas.pid = "1"
        assert services.fetch_positional_ocr(self.canvas)["ocr"] is not None

    def test_fetch_positional_ocr_with_offset(self):
        self.canvas.manifest.image_server.server_base = (
            "https://iiif.archivelab.org/iiif/"
        )
        self.canvas.manifest.pid = "atlantacitydirec1908foot"
        self.canvas.pid = "$1"
        assert services.fetch_positional_ocr(self.canvas)["ocr"] is not None

    # def test_fetch_positional_ocr_that_return_none(self):
    #     self.canvas.manifest.image_server.server_base = 'oxford'
    #     assert services.fetch_positional_ocr(self.canvas) is None

    @mock_aws
    def test_ocr_in_s3(self):
        bucket_name = encode_noid()
        manifest = ManifestFactory.create(
            image_server=ImageServerFactory.create(
                storage_service="s3",
                storage_path=bucket_name,
                server_base="images.readux.ecds.emory",
            )
        )
        self.set_up_mock_aws(manifest)
        tsv_file_path = "apps/iiif/canvases/fixtures/00000002.tsv"
        canvas = manifest.canvas_set.first()
        canvas.ocr_file_path = f"{manifest.pid}/_*ocr*_/00000002.tsv"
        manifest.image_server.bucket.upload_file(
            tsv_file_path, f"{manifest.pid}/_*ocr*_/00000002.tsv"
        )
        fetched_ocr = services.fetch_positional_ocr(canvas)
        assert open(tsv_file_path, "rb").read() == fetched_ocr

    @mock_aws
    def test_fetched_ocr_result_is_string(self):
        """Test when fetched OCR is a string."""
        bucket_name = encode_noid()
        manifest = ManifestFactory.create(
            image_server=ImageServerFactory.create(
                storage_service="s3",
                storage_path=bucket_name,
                server_base="images.readux.ecds.emory",
            )
        )
        self.set_up_mock_aws(manifest)
        tsv_file_path = "apps/iiif/canvases/fixtures/00000002.tsv"
        canvas = manifest.canvas_set.first()
        canvas.ocr_file_path = f"{manifest.pid}/_*ocr*_/00000002.tsv"
        manifest.image_server.bucket.upload_file(
            tsv_file_path, f"{manifest.pid}/_*ocr*_/00000002.tsv"
        )
        ocr_result = open(tsv_file_path, "r").read()
        assert isinstance(ocr_result, str)
        ocr = services.add_positional_ocr(canvas, ocr_result)
        assert len(ocr) == 10
        assert ocr[0]["content"] == "Manuscript"

    @mock_aws
    def test_fetched_ocr_result_is_bytes(self):
        """Test when fetched OCR is a bytes."""
        bucket_name = encode_noid()
        manifest = ManifestFactory.create(
            image_server=ImageServerFactory.create(
                storage_service="s3",
                storage_path=bucket_name,
                server_base="images.readux.ecds.emory",
            )
        )
        self.set_up_mock_aws(manifest)
        tsv_file_path = "apps/iiif/canvases/fixtures/00000002.tsv"
        canvas = manifest.canvas_set.first()
        canvas.ocr_file_path = f"{manifest.pid}/_*ocr*_/00000002.tsv"
        manifest.image_server.bucket.upload_file(
            tsv_file_path, f"{manifest.pid}/_*ocr*_/00000002.tsv"
        )
        ocr_result = open(tsv_file_path, "rb").read()
        assert isinstance(ocr_result, bytes)
        ocr = services.add_positional_ocr(canvas, ocr_result)
        assert len(ocr) == 10
        assert ocr[0]["content"] == "Manuscript"

    def test_from_alto_ocr(self):
        """Test parsing ALTO OCR"""
        alto = open("apps/iiif/canvases/fixtures/alto.xml", "rb").read()
        ocr = services.parse_alto_ocr(alto)
        assert ocr[0]["content"] == "MAGNA"
        assert ocr[0]["h"] == 164
        assert ocr[0]["w"] == 758
        assert ocr[0]["x"] == 1894
        assert ocr[0]["y"] == 1787

    def test_from_hocr(self):
        """Test parsing hOCR"""
        hocr = open("apps/iiif/canvases/fixtures/hocr.hocr", "rb").read()
        ocr = services.parse_hocr_ocr(hocr)
        assert ocr[0]["content"] == "MAGNA"
        assert ocr[0]["h"] == 164
        assert ocr[0]["w"] == 758
        assert ocr[0]["x"] == 1894
        assert ocr[0]["y"] == 1787

    def test_from_bad_hocr(self):
        """Test parsing bad hOCR"""
        bad_hocr = open("apps/iiif/canvases/fixtures/bad_hocr.hocr", "rb").read()
        self.assertRaises(
            services.HocrValidationError, services.parse_hocr_ocr, bad_hocr
        )

    def test_identifying_alto_xml(self):
        """Test identifying XML file as ALTO OCR"""
        alto = open("apps/iiif/canvases/fixtures/alto.xml", "rb").read()
        ocr = services.parse_xml_ocr(alto)
        assert ocr[0]["content"] == "MAGNA"
        assert ocr[0]["h"] == 164
        assert ocr[0]["w"] == 758
        assert ocr[0]["x"] == 1894
        assert ocr[0]["y"] == 1787

    def test_identifying_hocr_xml(self):
        """Test identifying XML file as hOCR"""
        hocr = open("apps/iiif/canvases/fixtures/hocr.hocr", "rb").read()
        ocr = services.parse_xml_ocr(hocr)
        assert ocr[0]["content"] == "MAGNA"
        assert ocr[0]["h"] == 164
        assert ocr[0]["w"] == 758
        assert ocr[0]["x"] == 1894
        assert ocr[0]["y"] == 1787

    def test_identifying_tei_xml(self):
        """Test identifying XML file as hOCR"""
        tei = open("apps/iiif/canvases/fixtures/tei.xml", "r").read()
        ocr = services.parse_xml_ocr(tei)
        assert ocr[1]["content"] == "AEN DEN LESIIU"
        assert ocr[1]["h"] == 28
        assert ocr[1]["w"] == 461
        assert ocr[1]["x"] == 814
        assert ocr[1]["y"] == 185

    def test_identification_failure(self):
        """Test identifying XML on non-XML fails"""
        tsv = open("apps/iiif/canvases/fixtures/sample.tsv", "r").read()
        self.assertRaises(XMLSyntaxError, services.parse_xml_ocr, tsv)

    def test_unidentifiable_xml(self):
        """Test identifying XML that is not TEI, ALTO, or hOCR"""
        hops = open("apps/iiif/canvases/fixtures/hops.xml", "rb").read()
        ocr = services.parse_xml_ocr(hops)
        assert ocr is None

    @mock_aws
    def test_add_alto_ocr_by_filename(self):
        """Test get_ocr when OCR is ALTO file (by filename)."""
        bucket_name = encode_noid()
        manifest = ManifestFactory.create(
            image_server=ImageServerFactory.create(
                storage_service="s3",
                storage_path=bucket_name,
                server_base="images.readux.ecds.emory",
            )
        )
        self.set_up_mock_aws(manifest)
        tsv_file_path = "apps/iiif/canvases/fixtures/alto.xml"
        canvas = manifest.canvas_set.first()
        canvas.ocr_file_path = f"{manifest.pid}/_*ocr*_/alto.xml"
        manifest.image_server.bucket.upload_file(
            tsv_file_path, f"{manifest.pid}/_*ocr*_/alto.xml"
        )
        ocr = services.get_ocr(canvas)
        assert ocr[0]["content"] == "MAGNA"
        assert ocr[0]["h"] == 164
        assert ocr[0]["w"] == 758
        assert ocr[0]["x"] == 1894
        assert ocr[0]["y"] == 1787

    @mock_aws
    def test_add_hocr_by_filename(self):
        """Test get_ocr when OCR is hOCR file (by filename)."""
        bucket_name = encode_noid()
        manifest = ManifestFactory.create(
            image_server=ImageServerFactory.create(
                storage_service="s3",
                storage_path=bucket_name,
                server_base="images.readux.ecds.emory",
            )
        )
        self.set_up_mock_aws(manifest)
        tsv_file_path = "apps/iiif/canvases/fixtures/hocr.hocr"
        canvas = manifest.canvas_set.first()
        canvas.ocr_file_path = f"{manifest.pid}/_*ocr*_/hocr.hocr"
        manifest.image_server.bucket.upload_file(
            tsv_file_path, f"{manifest.pid}/_*ocr*_/hocr.hocr"
        )
        ocr = services.get_ocr(canvas)
        assert ocr[0]["content"] == "MAGNA"
        assert ocr[0]["h"] == 164
        assert ocr[0]["w"] == 758
        assert ocr[0]["x"] == 1894
        assert ocr[0]["y"] == 1787

    @mock_aws
    def test_add_json_ocr_by_filename(self):
        """Test get_ocr when OCR is JSON file (by filename)."""
        bucket_name = encode_noid()
        manifest = ManifestFactory.create(
            image_server=ImageServerFactory.create(
                storage_service="s3",
                storage_path=bucket_name,
                server_base="images.readux.ecds.emory",
            )
        )
        self.set_up_mock_aws(manifest)
        tsv_file_path = "apps/iiif/canvases/fixtures/ocr_words.json"
        canvas = manifest.canvas_set.first()
        canvas.ocr_file_path = f"{manifest.pid}/_*ocr*_/ocr_words.json"
        manifest.image_server.bucket.upload_file(
            tsv_file_path, f"{manifest.pid}/_*ocr*_/ocr_words.json"
        )
        ocr = services.get_ocr(canvas)
        assert ocr[0]["content"] == "Dope"

    def test_none_ocr(self):
        """Test add_positional_ocr when fetched OCR is None."""
        ocr = services.add_positional_ocr(self.canvas, None)
        assert ocr is None

    def test_none_alto_ocr(self):
        """Test add_positional_ocr when fetched OCR is None."""
        ocr = services.parse_alto_ocr(None)
        assert ocr is None

    def test_not_tsv(self):
        """Test is_tsv with something that is not TSV"""
        not_tsv = "test string"
        is_tsv = services.is_tsv(not_tsv)
        self.assertFalse(is_tsv)

    @httpretty.httprettified(allow_net_connect=False)
    def test_ocr_from_oa_annotation(self):
        """Test deserializing OA annotations"""
        canvas = CanvasFactory.create(manifest=ManifestFactory.create())

        for _ in range(0, 12):
            AnnotationFactory.create(canvas=canvas)

        anno_list = serialize(
            "annotation_list",
            [canvas],
            version="v2",
            owners=[UserFactory.create(username="ocr")],
        )

        canvas.annotation_set.clear()
        canvas.refresh_from_db()

        assert canvas.annotation_set.count() == 0

        httpretty.register_uri(
            httpretty.GET,
            f"https://readux.io/iiif/v2/{canvas.manifest.pid}/list/{canvas.pid}",
            body=anno_list,
            content_type="text/json",
        )

        services.add_oa_annotations(
            f"https://readux.io/iiif/v2/{canvas.manifest.pid}/list/{canvas.pid}"
        )
        canvas.refresh_from_db()
        assert canvas.annotation_set.count() == 12
