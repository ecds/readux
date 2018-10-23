import requests
import json

from django.conf import settings
from . import defaults as defs


def get_collections(url):
    """ Given a url, this function returns a dictonary of all collections."""
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
    except json.decoder.JSONDecodeError as err:
        if (settings.DEBUG):
            print('Server send success status with bad content')
        return collections

    try:
        collections = jsonDict['collections']
    except KeyError as err:
        if (settings.DEBUG):
            print('No collections for {}'.format(url))

    return collections


def get_all_collections():
    """ Returns all top level collections """
    return get_collections(defs.IIIF_UNIVERSE_COLLECTION_URL)


def get_collections_recursively(url, depth=1):
    """ Returns collections with their subcollection up to depth of '[n]`. """
    if depth < 1:
        return []

    collections = get_collections(url)
    if depth == 1:
        return collections

    results = []
    for col in collections:
        link = col.get('@id')
        if link:
            sub = get_collections_recursively(link, depth-1)
            col['collections'] = sub
            results.append(col)
    
    return results

