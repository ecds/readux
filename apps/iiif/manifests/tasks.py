from celery import Celery
from django.apps import apps

app = Celery('apps.iiif.manifests', result_extended=True)

@app.task(name='index_manifest', autoretry_for=(Exception,), retry_backoff=True, max_retries=20)
def index_manifest_task(manifest_id):
    """Background task index Manifest after save.

    :param manifest_id: Primary key for .models.Manifest object
    :type manifest_id: UUID

    """
    from .models import Manifest
    from .documents import ManifestDocument
    index = ManifestDocument()
    manifest = Manifest.objects.get(pk=manifest_id)
    index.update(manifest, True, 'index')


@app.task(name='de-index_manifest', autoretry_for=(Exception,), retry_backoff=True, max_retries=20)
def de_index_manifest_task(manifest_id):
    """Background task to de-index Manifest after delete.

    :param manifest_id: Primary key for .models.Manifest object
    :type manifest_id: UUID

    """
    from .models import Manifest
    from .documents import ManifestDocument
    index = ManifestDocument()
    manifest = Manifest.objects.get(pk=manifest_id)
    index.update(manifest, True, 'delete')
