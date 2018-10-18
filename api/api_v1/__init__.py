##
# @license
# Copyright Neekware Inc. All Rights Reserved.
#
# Use of this source code is governed by an MIT-style license that can be
# found in the LICENSE file at http://neekware.com/license/MIT.html
###


from .utils.common import get_api_namespace

__author__ = 'Val Neekman [neekware.com]'
__description__ = 'API Version 1'
__version__ = '0.0.1'
__api__ = get_api_namespace(__name__)


default_app_config = '{}.apps.AppConfig'.format(__api__)
