##
# @license
# Copyright Neekware Inc. All Rights Reserved.
#
# Use of this source code is governed by an MIT-style license that can be
# found in the LICENSE file at http://neekware.com/license/MIT.html
###

from django.conf import settings

from toolware.utils.generic import get_site_proto


def get_site_name():
    """ Retuns site's name """
    domain = getattr(settings, 'SITE_NAME')
    return domain


def get_site_domain():
    """ Retuns site's domain name """
    domain = getattr(settings, 'SITE_DOMAIN')
    return domain


def get_app_domain():
    """ Return app's domain name """
    domain = getattr(settings, 'SITE_APP_DOMAIN')
    return domain


def get_app_fqdn(proto=None):
    """ Return apps's fully qualified domain name """
    proto = proto or get_site_proto()
    domain = get_app_domain()
    fdqn = '{proto}://{domain}'.format(proto=proto, domain=domain)
    return fdqn


def get_api_domain():
    """ Return api's domain name """
    domain = getattr(settings, 'SITE_API_DOMAIN')
    return domain


def get_api_fqdn(proto=None):
    """ Return api's fully qualified domain name """
    proto = proto or get_site_proto()
    domain = get_api_domain()
    fdqn = '{proto}://{domain}'.format(proto=proto, domain=domain)
    return fdqn
