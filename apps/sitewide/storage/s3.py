##
# @license
# Copyright Neekware Inc. All Rights Reserved.
#
# Use of this source code is governed by an MIT-style license that can be
# found in the LICENSE file at http://neekware.com/license/MIT.html
###

from django.conf import settings

from storages.backends.s3boto import S3BotoStorage
from django.contrib.staticfiles.storage import ManifestFilesMixin

from toolware.utils.generic import get_domain

from .. import defaults as defs


class MediaFilesStorage(S3BotoStorage):
    """
    Custom S3 storage for uploaded assets. (any file type)
    """
    def __init__(self, *args, **kwargs):
        kwargs['bucket'] = settings.AWS_MEDIA_BUCKET_NAME
        kwargs['location'] = settings.MEDIA_ASSETS_PREFIX
        kwargs['custom_domain'] = get_domain(settings.AWS_MEDIA_CDN)
        super().__init__(*args, **kwargs)


class StaticFilesStorage(S3BotoStorage):
    """
    Custom S3 storage for static assets. (any file type)
    """
    def __init__(self, *args, **kwargs):
        kwargs['bucket'] = settings.AWS_STATIC_BUCKET_NAME
        kwargs['location'] = settings.STATIC_ASSETS_PREFIX
        kwargs['custom_domain'] = get_domain(settings.AWS_STATIC_CDN)
        super().__init__(*args, **kwargs)


class ManifestStaticFilesStorage(ManifestFilesMixin, S3BotoStorage):
    """
    Custom S3 storage for manifest static assets. (any file type).
    """
    def __init__(self, *args, **kwargs):
        kwargs['bucket'] = settings.AWS_STATIC_BUCKET_NAME
        kwargs['location'] = settings.STATIC_ASSETS_PREFIX
        kwargs['custom_domain'] = get_domain(settings.AWS_STATIC_CDN)
        super().__init__(*args, **kwargs)

    @property
    def manifest_name(self):
        filename = 'staticfiles-{}.json'.format(defs.MANIFEST_STATIC_FILE_VERSION)
        return filename
