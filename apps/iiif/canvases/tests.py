from django.test import TestCase
from .models import Canvas
from . import services


class CanvasTests(TestCase):
    fixtures = ['kollections.json', 'manifests.json', 'canvases.json', 'annotations.json']
    def test_ia_ocr_creation(self):
        valid_ia_ocr_response = {
        'ocr': [
            [
            ['III', [120, 1600, 180, 1494, 1597]]
            ],
            [
            ['chambray', [78, 1734, 116, 1674, 1734]]
            ],
            [
            ['tacos', [142, 1938, 188, 1854, 1938]]
            ],
            [
            ['freegan', [114, 2246, 196, 2156, 2245]]
            ],
            [
            ['Kombucha', [180, 2528, 220, 2444, 2528]]
            ],
            [
            ['succulents', [558, 535, 588, 501, 535]],
            ['Thundercats', [928, 534, 1497, 478, 527]]
            ],
            [
            ['poke', [557, 617, 646, 575, 614]],
            ['VHS', [700, 612, 1147, 555, 610]],
            ['chartreuse ', [1191, 616, 1209, 589, 609]],
            ['pabst', [1266, 603, 1292, 569, 603]],
            ['8-bit', [1354, 602, 1419, 549, 600]],
            ['narwhal', [1471, 613, 1566, 553, 592]],
            ['XOXO', [1609, 604, 1670, 538, 596]],
            ['post-ironic', [1713, 603, 1826, 538, 590]],
            ['synth', [1847, 588, 1859, 574, 588]]
            ],
            [
            ['lumbersexual', [1741, 2928, 1904, 2881, 2922]]
            ]
        ]
        }

        canvas = Canvas.objects.get(pid='15210893.5622.emory.edu$95')
        ocr = services.add_positional_ocr(canvas, valid_ia_ocr_response)
        assert len(ocr) == 17
        for word in ocr:
            assert 'w' in word
            assert 'h' in word
            assert 'x' in word
            assert 'y' in word
            assert 'content' in word
            assert type(word['w']) == int
            assert type(word['h']) == int
            assert type(word['x']) == int
            assert type(word['y']) == int
            assert type(word['content']) == str

    def test_fedora_ocr_creation(self):
        valid_fedora_positional_response = """523\t 116\t 151\t  45\tDistillery\r\n 704\t 117\t 148\t  52\tplaid,"\r\n""".encode('UTF-8-sig')
        
        canvas = Canvas.objects.get(pid='fedora:emory:5622')
        ocr = services.add_positional_ocr(canvas, valid_fedora_positional_response)
        assert len(ocr) == 2
        for word in ocr:
            assert 'w' in word
            assert 'h' in word
            assert 'x' in word
            assert 'y' in word
            assert 'content' in word
            assert type(word['w']) == int
            assert type(word['h']) == int
            assert type(word['x']) == int
            assert type(word['y']) == int
            assert type(word['content']) == str
