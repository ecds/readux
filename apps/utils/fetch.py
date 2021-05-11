""" Utility functions for fetching remote data. """
import json
import logging
import requests

logger = logging.getLogger(__name__)
logging.getLogger("urllib3").setLevel(logging.ERROR)

def fetch_url(url, timeout=30, data_format='json', verbosity=1):
    """ Given a url, this function returns the data."""
    data = None
    try:
        resp = requests.get(url, timeout=timeout, verify=True)
    except requests.exceptions.Timeout as err:
        if verbosity > 2:
            logger.warning('Connection timeoutout for {}'.format(url))
        return data
    except Exception as err:
        if verbosity > 2:
            logger.warning('Connection failed for {}. ({})'.format(url, str(err)))
        return data

    if resp.status_code != 200:
        if verbosity > 2:
            logger.warning('Connection failed status {}. ({})'.format(url, resp.status_code))
        return data

    if data_format == 'json':
        try:
            data = resp.json()
        except json.decoder.JSONDecodeError as err:
            if verbosity > 2:
                logger.warning('Server send success status with bad content {}'.format(url))
        return data

    if data_format == 'text':
        data = resp.text
    else:
        data = resp.content
    return data

# Not sure this is really needed for us, but not a bad thing to keep around.
# def rate_limited(max_per_second):
#     """ Throttle remote API calls by limiting api calls per seconds """
#     lock = threading.Lock()
#     min_interval = 1.0 / max_per_second

#     def decorate(func):
#         last_time_called = time.perf_counter()

#         @wraps(func)
#         def rate_limited_function(*args, **kwargs):
#             lock.acquire()
#             nonlocal last_time_called
#             elapsed = time.perf_counter() - last_time_called
#             left_to_wait = min_interval - elapsed

#             if left_to_wait > 0:
#                 time.sleep(left_to_wait)

#             ret = func(*args, **kwargs)
#             last_time_called = time.perf_counter()
#             lock.release()
#             return ret

#         return rate_limited_function

#     return decorate