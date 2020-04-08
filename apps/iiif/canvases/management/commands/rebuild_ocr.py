from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from apps.iiif.canvases.models import Canvas
from apps.iiif.annotations.models import Annotation
from apps.iiif.manifests.models import Manifest
from apps.iiif.canvases import services
from progress.bar import Bar

User = get_user_model()

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

    def handle(self, *args, **options):
        if options['manifest']:
            try:
                manifest = Manifest.objects.get(pid = options['manifest'])
                for canvas in manifest.canvas_set.all():
                    self.__rebuild(canvas)
                self.stdout.write(self.style.SUCCESS('OCR rebuilt for manifest {m}'.format(m=options['manifest'])))
            except Manifest.DoesNotExist:
                self.stdout.write(self.style.ERROR('ERROR: manifest not found with pid {m}'.format(m=options['manifest'])))
        elif options['canvas']:
            try:
                canvas = Canvas.objects.get(pid=options['canvas'])
                self.__rebuild(canvas)
                self.stdout.write(self.style.SUCCESS('OCR rebuilt for canvas {c}'.format(c=options['canvas'])))
            except Canvas.DoesNotExist:
                self.stdout.write(self.style.ERROR('ERROR: canvas not found with pid {p}'.format(p=options['canvas'])))
        else:
            self.stdout.write(self.style.ERROR('ERROR: your must provide a manifest or canvas pid'))

            # self.stdout.write(self.style.SUCCESS('Successfully closed poll "%s"' % poll_id))
    
    def __rebuild(self, canvas):
        if not canvas.annotation_set.exists():
            canvas.save()
        else:
            ocr = services.get_ocr(canvas)
            if ocr is None:
                return

            word_order = 1
            self.stdout.write('Adding OCR for canvas {c}'.format(c=canvas.pid))
            with Bar('Processing', max=len(ocr)) as bar:
                for word in ocr:
                    if word == '' or 'content' not in word or not word['content'] or word['content'].isspace():
                        contintue
                    anno = None
                    try:
                        anno = Annotation.objects.get(
                            w = word['w'],
                            h = word['h'],
                            x = word['x'],
                            y = word['y'],
                            owner = User.objects.get(username='ocr'),
                            canvas = canvas
                        )
                    except Annotation.DoesNotExist:
                        anno = Annotation(
                            w = word['w'],
                            h = word['h'],
                            x = word['x'],
                            y = word['y'],
                            canvas = canvas,
                            owner = User.objects.get(username='ocr'),
                            resource_type = Annotation.OCR
                        )
                    word_order += 1
                    anno.content = word['content']
                    anno.save()
                    bar.next()
                bar.finish()
