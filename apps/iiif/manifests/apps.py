"""Module for Django app config"""
from django.apps import AppConfig

class ManifestsConfig(AppConfig):
    """Configuration for manifest app"""
    name = 'apps.iiif.manifests'
    verbose_name = 'Manifests'
