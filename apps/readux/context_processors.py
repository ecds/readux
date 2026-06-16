"""Global template contexts."""

from os import environ
from git import Repo
from django.conf import settings
from . import __version__


def current_version(_=None):
    """Display current version. On non-production instances, display Git information.

    Example of return:

    {
        "DJANGO_ENV": "dev",
        "APP_VERSION": "Readux 3.0",
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

    # Prefer the Django setting (which has a default) over os.environ directly,
    # to avoid KeyError when DJANGO_ENV is not exported to the shell environment.
    django_env = getattr(settings, "DJANGO_ENV", environ.get("DJANGO_ENV", "develop"))

    version_info = {"DJANGO_ENV": django_env, "APP_VERSION": __version__}

    if django_env == "production":
        return version_info

    try:
        branch = repo.active_branch
        return {
            **version_info,
            "BRANCH": branch.name,
            "COMMIT": branch.commit.hexsha,
            "COMMIT_DATE": branch.commit.committed_datetime.strftime(
                "%m/%d/%Y, %H:%M:%S"
            ),
        }
    except TypeError:
        # HEAD is detached — e.g. during a git rebase or a CI checkout of a
        # specific commit.  Fall back to commit-level info without a branch name.
        commit = repo.head.commit
        return {
            **version_info,
            "BRANCH": commit.hexsha[:12],
            "COMMIT": commit.hexsha,
            "COMMIT_DATE": commit.committed_datetime.strftime("%m/%d/%Y, %H:%M:%S"),
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


def matomo_id(_):
    """Expose Matomo ID for analytics.
    Args:
        _ (WSGIRequest): Current request. Not used.

    Returns:
        dict: Dict with key 'MATOMO_ID' for use in analytics script tag.
    """
    return {"MATOMO_ID": getattr(settings, "MATOMO_ID", "")}
