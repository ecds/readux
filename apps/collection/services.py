import requests
import json

from django.conf import settings
from . import defaults as defs


def get_collections(url):
    """
    Given a url, this function returns a dictonary of all collections.
    """
    collections = []
    try:
        resp = requests.get(url, timeout=defs.HTTP_REQUEST_TIMEOUT)
    except requests.exceptions.Timeout as err:
        if (settings.DEBUG):
            print('Connection timeoutout for {}'.format(url))
        return collections
    except Exception as err:
        if (settings.DEBUG):
            print('Connection failed for {}'.format(str(err)))
        return collections
    
    if resp.status_code != 200:
        if (settings.DEBUG):
            print('Connection failed status {}'.format(resp.status_code))
        return collections

    try:
        jsonDict = resp.json()
        collections = jsonDict['collections']
    except KeyError as err:
        if (settings.DEBUG):
            print('No collections for {}'.format(url))

    return collections

def get_all_collections():
    """ Returns all top level collections """
    return get_collections(defs.IIIF_UNIVERSE_COLLECTION_URL)

