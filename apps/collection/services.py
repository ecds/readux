import requests
import json

def get_all_collections():
    url = 'http://ryanfb.github.io/iiif-universe/iiif-universe.json' 
    r = requests.get(url)
    return r.json()['collections']
