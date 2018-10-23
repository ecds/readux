import requests
import json

from django.conf import settings


def fetch_url(url, timeout=30, format='json'):
    """ Given a url, this function returns the data."""
    data = None
    try:
        resp = requests.get(url, timeout=timeout)
    except requests.exceptions.Timeout as err:
        if (settings.DEBUG):
            print('Connection timeoutout for {}'.format(url))
        return data
    except Exception as err:
        if (settings.DEBUG):
            print('Connection failed for {}. ({})'.format(url, str(err)))
        return data
    
    if resp.status_code != 200:
        if (settings.DEBUG):
            print('Connection failed status {}. ({})'.format(url, resp.status_code))
        return data

    if format == 'json':
      try:
          data = resp.json()
      except json.decoder.JSONDecodeError as err:
          if (settings.DEBUG):
              print('Server send success status with bad content {}'.format(url))
    elif format == 'text':
      data = resp.text
    else:
      data = resp.content

    return data

