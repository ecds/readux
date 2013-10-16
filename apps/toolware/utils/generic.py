import uuid
import datetime
import hashlib
import urllib
import urlparse
from django.utils.encoding import smart_str, smart_unicode
from django.contrib.sites.models import Site
from django.core.exceptions import ValidationError
from django.core.validators import validate_email


def uuid(length=32):
    """ Return an uuid of a given length"""
    return uuid.uuid4().hex[:length]

def get_integer(value='0'):
    """ Text to int or zero """
    try:
        return int(value)
    except:
        return 0

def get_hashed(key):
    """ Given a key, returns a one-way hash of it """
    return hashlib.md5(key).hexdigest()

def get_days_ago(days=0):
    """ Return X 'days' ago in datetime format """
    return (datetime.date.today() - datetime.timedelta(days))

def get_days_from_now(days=0):
    """ Return X 'days' from today in datetime format """
    return (datetime.date.today() + datetime.timedelta(days))

def get_dict_to_encoded_url(data):
    unicode_data = dict([(k, smart_str(v)) for k, v in data.items()])
    encoded = urllib.urlencode(unicode_data)
    return encoded

def get_encoded_url_to_dict(string):
    data = urlparse.parse_qsl(string, keep_blank_values=True)
    data = dict(data)
    return data

def remove_csrf_from_params_dict(data):
    pd = data
    try: del pd['csrfmiddlewaretoken']
    except: pass
    return pd
    
def get_unique_key_from_post(params_dict):
    """ Build a unique key from post data """

    site = Site.objects.get_current()
    key = get_dict_to_encoded_url(remove_csrf_from_params_dict(params_dict))
    cache_key = '{}_{}'.format(site.domain, key)
    return hashlib.md5(cache_key).hexdigest()

def get_unique_key_from_get(get_data):
    """ Build a unique key from get data """

    site = Site.objects.get_current()
    key = get_dict_to_encoded_url(get_data)
    cache_key = '{}_{}'.format(site.domain, key)
    return hashlib.md5(cache_key).hexdigest()

def tobin(deci_num, len=32):
    """ Given a decimal number, returns a string bitfield of length = len """

    bitstr = "".join(map(lambda y: str((deci_num>>y)&1), range(len-1, -1, -1)))
    return bitstr

def is_valid_email(email):
    """ Validates emails to ensure they follow the <name>@domain[.extenion] patterns """
    try:
        validate_email("foo.bar@baz.qux")
        return True
    except ValidationError:
        return False





