import os
import requests
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

    session = requests.Session()

    if hasattr(settings, 'SOLR_CA_CERT_PATH'):
        session.cert = settings.SOLR_CA_CERT_PATH
        session.verify = True
    if getattr(settings, 'SOLR_DISABLE_CERT_CHECK', False):
        session.verify = False

    # configure requests to use http proxy if one is set in ENV
    http_proxy = os.getenv('HTTP_PROXY', None)
    if http_proxy:
        parsed_proxy = urlparse(http_proxy)
        session.proxies = {
           parsed_proxy.scheme: http_proxy   # i.e., 'http': 'hostname:3128'
        }

    # pass in the constructed requests session as the connection to be used
    # when making requests of solr
    solr_opts = {'http_connection': session}
    # since we have the schema available, don't bother requesting it
    # from solr every time we initialize a new connection
    if hasattr(settings, 'SOLR_SCHEMA'):
        solr_opts['schemadoc'] = settings.SOLR_SCHEMA

    solr = sunburnt.SolrInterface(settings.SOLR_SERVER_URL,
                                  **solr_opts)
    return solr