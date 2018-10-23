import requests
import json

from django.conf import settings
from utils.fetch import fetch_url
from . import defaults as defs


def get_collections(url):
    """ Given a url, this function returns a dictonary of all collections."""
    results = fetch_url(url, timeout=defs.HTTP_REQUEST_TIMEOUT, format='json')
    return results

def get_all_collections():
    """ Returns all top level collections """
    return get_collections(defs.IIIF_UNIVERSE_COLLECTION_URL)


def get_collection_recursively(url, depth=1):
    """ Returns collections with their subcollection up to depth of '[n]`. """
    if depth < 1:
        return {}

    data = get_collections(url)
    if not data or data.get('@type') != 'sc:Collection':
        return {}

    if depth == 1:
        return data

    collections_with_sub = []
    for item in data.get('collections'):
        link = item.get('@id')
        if link:
            sub = get_collection_recursively(link, depth-1)
            item['sub'] = sub
        collections_with_sub.append(item)
        
    data['collections'] = collections_with_sub

    with open('collections.json', 'w') as outfile:
        json.dump(data, outfile, sort_keys = True, indent = 4,ensure_ascii = False)

    return data

