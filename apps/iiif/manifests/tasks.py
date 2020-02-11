from .export import JekyllSiteExport
from .models import Manifest
from apps.users.models import User

from background_task import background
import logging
import os


logger = logging.getLogger(__name__)

@background(schedule=1)
def github_export_task(manifest_pid, version, github_repo=None, user_email=None, user_id=None, owner_ids=None, deep_zoom=False):
    logger.info('Background github export started.')
    # need manifest ID
    # need deep_zoom
    manifest = Manifest.objects.get(pid=manifest_pid)
    user = User.objects.get(id=user_id)
    jekyll_exporter = JekyllSiteExport(manifest, version, github_repo=github_repo, deep_zoom=deep_zoom, owners=owner_ids, user=user);
    jekyll_exporter.github_export(user.email)
    logger.info('Background github export finished.')

@background(schedule=1)
def download_export_task(manifest_pid, version, github_repo=None, user_email=None, user_id=None, owner_ids=None, deep_zoom=False):
    logger.info('Background download export started.')
    # need manifest ID
    # need deep_zoom
    manifest = Manifest.objects.get(pid=manifest_pid)
    user = User.objects.get(id=user_id)
    jekyll_exporter = JekyllSiteExport(manifest, version, github_repo=github_repo, deep_zoom=deep_zoom, owners=owner_ids, user=user);
    zipfile_name = jekyll_exporter.download_export(user.email, manifest)
    delete_download_task(zipfile_name)
    logger.info('Background download export finished.')

@background(schedule=86400)
def delete_download_task(download_path):
    logger.info('Background download deletion started.')
    os.remove(download_path)
    logger.info('Background download deletion finished.')