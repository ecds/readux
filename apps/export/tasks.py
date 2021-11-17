"""Module to manage background export task."""
import logging
import os
from celery import Celery
from django.conf import settings
from apps.users.models import User
from apps.iiif.manifests.models import Manifest
from .export import JekyllSiteExport

LOGGER = logging.getLogger(__name__)

app = Celery('apps.readux', result_extended=True)

@app.task(name='github_export', autoretry_for=(Exception,), retry_backoff=True, max_retries=20)
def github_export_task(
        manifest_pid, version, github_repo=None,
        user_id=None, owner_ids=None, deep_zoom=False):
    """Background GitHub export

    :param manifest_pid: Manifest pid
    :type manifest_pid: str
    :param version: IIIF API version
    :type version: str
    :param github_repo: GitHub repo name, defaults to None
    :type github_repo: str, optional
    :param user_id: ID of exporter's user, defaults to None
    :type user_id: UUID, optional
    :param owner_ids: List of annotation owners, defaults to None
    :type owner_ids: list, optional
    :param deep_zoom: If True, include deep zoom in export, defaults to False
    :type deep_zoom: bool, optional
    """
    LOGGER.info('Background github export started.')
    # need manifest ID
    # need deep_zoom
    manifest = Manifest.objects.get(pid=manifest_pid)
    user = User.objects.get(id=user_id)
    jekyll_exporter = JekyllSiteExport(
        manifest,
        version,
        github_repo=github_repo,
        deep_zoom=deep_zoom,
        owners=owner_ids,
        user=user
    )

    jekyll_exporter.github_export(user.email)
    LOGGER.info('Background github export finished.')

@app.task(name='download_export', autoretry_for=(Exception,), retry_backoff=True, max_retries=20)
def download_export_task(
        manifest_pid, version, github_repo=None,
        user_id=None, owner_ids=None, deep_zoom=False):
    """Background download export.

    :param manifest_pid: Manifest pid
    :type manifest_pid: str
    :param version: IIIF API version
    :type version: str
    :param github_repo: GitHub repo name, defaults to None
    :type github_repo: str, optional
    :param user_id: ID of exporter's user, defaults to None
    :type user_id: UUID, optional
    :param owner_ids: List of annotation owners, defaults to None
    :type owner_ids: list, optional
    :param deep_zoom: If True, include deep zoom in export, defaults to False
    :type deep_zoom: bool, optional
    """
    LOGGER.info('Background download export started.')
    # need manifest ID
    # need deep_zoom
    manifest = Manifest.objects.get(pid=manifest_pid)
    user = User.objects.get(id=user_id)
    jekyll_exporter = JekyllSiteExport(
        manifest,
        version,
        github_repo=github_repo,
        deep_zoom=deep_zoom,
        owners=owner_ids,
        user=user
    )

    zipfile_name = jekyll_exporter.download_export(user.email, manifest)
    delete_download_task.apply_async((zipfile_name), countdown=86400)
    LOGGER.info('Background download export finished.')

@app.task(name='delete_download', autoretry_for=(Exception,), retry_backoff=True, max_retries=20)
def delete_download_task(download_path):
    """Background delete download task.

    :param download_path: System path for download.
    :type download_path: str
    """
    LOGGER.info('Background download deletion started.')
    os.remove(download_path)
    LOGGER.info('Background download deletion finished.')
