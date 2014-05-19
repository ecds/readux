import os
import httplib2
from urlparse import urlparse
from sunburnt import sunburnt

from django.conf import settings


def solr_interface():
    '''Wrapper function to initialize a
    :class:`sunburnt.SolrInterface` based on django settings and
    evironment.  Uses **SOLR_SERVER_URL** and **SOLR_CA_CERT_PATH** if
    one is set.  Additionally, if an **HTTP_PROXY** is set in the
    environment, it will be configured.
    '''
    http_opts = {}
    if hasattr(settings, 'SOLR_CA_CERT_PATH'):
        http_opts['ca_certs'] = settings.SOLR_CA_CERT_PATH
    if getattr(settings, 'SOLR_DISABLE_CERT_CHECK', False):
        http_opts['disable_ssl_certificate_validation'] = True

    # use http proxy if set in ENV
    http_proxy = os.getenv('HTTP_PROXY', None)
    solr_url = urlparse(settings.SOLR_SERVER_URL)
    # NOTE: using Squid with httplib2 requires no-tunneling proxy option
    # - non-tunnel proxy does not work with https
    if http_proxy and solr_url.scheme == 'http':
        parsed_proxy = urlparse(http_proxy)
        proxy_info = httplib2.ProxyInfo(proxy_type=httplib2.socks.PROXY_TYPE_HTTP_NO_TUNNEL,
                                        proxy_host=parsed_proxy.hostname,
                                        proxy_port=parsed_proxy.port)
        http_opts['proxy_info'] = proxy_info
    http = httplib2.Http(**http_opts)

    solr_opts = {'http_connection': http}
    # since we have the schema available, don't bother requesting it
    # from solr every time we initialize a new connection
    if hasattr(settings, 'SOLR_SCHEMA'):
        solr_opts['schemadoc'] = settings.SOLR_SCHEMA

    solr = sunburnt.SolrInterface(settings.SOLR_SERVER_URL,
                                  **solr_opts)
    return solr