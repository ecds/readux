##
# @license
# Copyright Neekware Inc. All Rights Reserved.
#
# Use of this source code is governed by an MIT-style license that can be
# found in the LICENSE file at http://neekware.com/license/MIT.html
###

import os


def get_api_version(module_name=None):
    """
    Returns the numeric version of the current API application.
    API version is calculated based on the directory layout.
    Example: api_v1 returns 1, api_v2 returns 2 ... etc.
    """
    if module_name is None:
        return None
    version = module_name.split('.')[0].split('api_v')[1]
    return version


def get_api_namespace(module_name=None):
    """
    Returns the namespace of the current API application.
    API version is calculated based on the directory layout.
    Returns: api_v1, api_v2, api_v3 ... etc.
    """
    version = get_api_version(module_name)
    if version is None:
        return None
    return 'api_v{}'.format(version)


def get_url_name(module_name, urlname):
    """
    Returns the namespace:urlname format ready to be reversed.
    Example: api_v1:login
    """
    return '{}:{}'.format(get_api_namespace(module_name), urlname)
