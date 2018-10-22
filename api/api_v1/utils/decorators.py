##
# @license
# Copyright Neekware Inc. All Rights Reserved.
#
# Use of this source code is governed by an MIT-style license that can be
# found in the LICENSE file at http://neekware.com/license/MIT.html
###

import os


def serializer_class(serializer_class):
    def decorator(func):
        func.serializer_class = serializer_class
        return func
    return decorator
