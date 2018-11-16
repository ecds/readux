import json
import time
import threading
import requests
from functools import wraps
from django.conf import settings


def fetch_url(url, timeout=30, format='json', verbosity=1):
    """ Given a url, this function returns the data."""
    data = None
    try:
        resp = requests.get(url, timeout=timeout, verify=False)
    except requests.exceptions.Timeout as err:
        if (verbosity > 2):
            print('Connection timeoutout for {}'.format(url))
        return data
    except Exception as err:
        if (verbosity > 2):
            print('Connection failed for {}. ({})'.format(url, str(err)))
        return data
    
    if resp.status_code != 200:
        if (verbosity > 2):
            print('Connection failed status {}. ({})'.format(url, resp.status_code))
        return data

    if format == 'json':
      try:
          data = resp.json()
      except json.decoder.JSONDecodeError as err:
        if (verbosity > 2):
            print('Server send success status with bad content {}'.format(url))
        return data
        
    elif format == 'text':
      data = resp.text
    else:
      data = resp.content

    return data


def rate_limited(max_per_second):
    """ Throttle remote API calls by limiting api calls per seconds """
    lock = threading.Lock()
    min_interval = 1.0 / max_per_second

    def decorate(func):
        last_time_called = time.perf_counter()

        @wraps(func)
        def rate_limited_function(*args, **kwargs):
            lock.acquire()
            nonlocal last_time_called
            elapsed = time.perf_counter() - last_time_called
            left_to_wait = min_interval - elapsed

            if left_to_wait > 0:
                time.sleep(left_to_wait)

            ret = func(*args, **kwargs)
            last_time_called = time.perf_counter()
            lock.release()
            return ret

        return rate_limited_function

    return decorate