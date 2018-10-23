##
# @license
# Copyright Neekware Inc. All Rights Reserved.
#
# Use of this source code is governed by an MIT-style license that can be
# found in the LICENSE file at http://neekware.com/license/MIT.html
###

from .. import defaults as defs


if defs.REMOTE_STORAGE_ENABLED:
    from . import s3 as backend
else:
    from . import fs as backend


class MediaFilesStorage(backend.MediaFilesStorage):
    pass


class StaticFilesStorage(backend.StaticFilesStorage):
    pass


class ManifestStaticFilesStorage(backend.ManifestStaticFilesStorage):
    pass
