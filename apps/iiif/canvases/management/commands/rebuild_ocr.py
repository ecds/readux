"""
Manage commands for Canvas objects.
"""
from progress.bar import Bar
import httpretty
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from ...models import Canvas
from ... import services
from ....annotations.models import Annotation
from ....manifests.models import Manifest

USER = get_user_model()

class Command(BaseCommand):
    help = 'Rebuild OCR for a canvas'

    def add_arguments(self, parser):
        parser.add_argument(
            '--canvas',
            help='Rebuild OCR for specific canvas with supplied pid.',
        )
        parser.add_argument(
            '--manifest',
            help='Rebuild OCR for entire manifest/volume with supplied pid.',
        )
        parser.add_argument(
            '--testing',
            help='Tells command to mock http requests with testing',
            default=False
        )

    def handle(self, *args, **options):
        if options['manifest']:
            try:
                manifest = Manifest.objects.get(pid=options['manifest'])
                for canvas in manifest.canvas_set.all():
                    self.__rebuild(canvas)
                self.stdout.write(
                    self.style.SUCCESS(
                        'OCR rebuilt for manifest {m}'.format(m=options['manifest'])
                    )
                )
            except Manifest.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(
                        'ERROR: manifest not found with pid {m}'.format(m=options['manifest'])
                    )
                )
        elif options['canvas']:
            try:
                canvas = Canvas.objects.get(pid=options['canvas'])

                self.__rebuild(canvas, options['testing'])
                self.stdout.write(
                    self.style.SUCCESS(
                        'OCR rebuilt for canvas {c}'.format(c=options['canvas'])
                    )
                )
            except Canvas.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(
                        'ERROR: canvas not found with pid {p}'.format(p=options['canvas'])
                    )
                )
        else:
            self.stdout.write(
                self.style.ERROR(
                    'ERROR: your must provide a manifest or canvas pid'
                )
            )

    def __rebuild(self, canvas, testing=False):
        if not canvas.annotation_set.exists():
            canvas.save()
        else:
            ocr = services.get_ocr(canvas)
            if ocr is None:
                return

            word_order = 1
            self.stdout.write('Adding OCR for canvas {c}'.format(c=canvas.pid))
            with Bar('Processing', max=len(ocr)) as prog_bar:
                for word in ocr:
                    if (
                            word == '' or
                            'content' not in word or
                            not word['content'] or
                            word['content'].isspace()
                    ):
                        continue
                    anno = None
                    try:
                        anno = Annotation.objects.get(
                            w=word['w'],
                            h=word['h'],
                            x=word['x'],
                            y=word['y'],
                            owner=USER.objects.get(username='ocr'),
                            canvas=canvas
                        )
                    except Annotation.DoesNotExist:
                        anno = Annotation(
                            w=word['w'],
                            h=word['h'],
                            x=word['x'],
                            y=word['y'],
                            canvas=canvas,
                            owner=USER.objects.get(username='ocr'),
                            resource_type=Annotation.OCR,
                            order=word_order
                        )
                    word_order += 1
                    anno.content = word['content']
                    anno.save()
                    prog_bar.next()
                prog_bar.finish()
