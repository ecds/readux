""" Global template contexts. """

from os import environ
from git import Repo
from django.conf import settings
from . import __version__


def current_version(_=None):
    """Display current version. On non-production instances, display Git information.

    Example of return:

    {
        "DJANGO_ENV": "dev",
        "APP_VERSION": "Readux 2.3.0",
        "BRANCH": "develop",
        "COMMIT": "deeb939f41c001658d9f3ce82d6fa6add6158d5c",
        "COMMIT_DATE": "01/13/2025, 13:13:18"
    }

    Args:
        _ (WSGIRequest): Current request. Not used.

    Returns:
        dict: Dict of version and Git info.
    """
    repo = Repo(settings.ROOT_DIR.path())

    version_info = {"DJANGO_ENV": environ["DJANGO_ENV"], "APP_VERSION": __version__}

    if environ["DJANGO_ENV"] == "production":
        return version_info
    return {
        **version_info,
        "BRANCH": repo.active_branch.name,
        "COMMIT": repo.active_branch.commit.hexsha,
        "COMMIT_DATE": repo.active_branch.commit.committed_datetime.strftime(
            "%m/%d/%Y, %H:%M:%S"
        ),
    }


def footer_template(_):
    """Use configured footer template for the footer content or default.

    Args:
        _ (WSGIRequest): Current request. Not used.

    Returns:
        dict: Dict with key 'FOOTER_CONTENT_TEMPLATE'. Value is str.
    """
    return {
        "FOOTER_CONTENT_TEMPLATE": getattr(
            settings, "FOOTER_CONTENT_TEMPLATE", "_home/_footer_content.html"
        )
    }


def site_meta(_):
    """Use configured values for site meta tags.

    Args:
        _ (WSGIRequest): Current request. Not used.

    Returns:
        dict: Dict with keys 'META_KEYWORDS' and 'META_DESCRIPTION' for use in meta tags.
    """
    return {
        "META_KEYWORDS": getattr(settings, "META_KEYWORDS", ""),
        "META_DESCRIPTION": getattr(settings, "META_DESCRIPTION", ""),
    }
