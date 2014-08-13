
'''
Objects to interact with the Digitization Workflow API in order to
retrieve information about LSDI content.

'''

import requests
from eulxml import xmlmap


class Client(object):
    """A simple client to query the Digitization Workflow REST(ish)
    API for information about files associated with LSDI/DigWF items.

    :param baseurl: base url of the api for the DigWF REST service., e.g.
                    ``http://my.domain.com/digwf_api/``
    """

    def __init__(self, url):
        self.base_url = url.rstrip('/')

    def get_items(self, **kwargs):
        '''Query the DigWF API getItems method.  If no search terms
        are specified, getItems returns any items that are in the
        **Ready for Repository** state.  Any keyword arguments will be
        passed to getItems as query arguments.  Currently supports:

          * control_key (e.g., ocm or ocn number) - may match more
            than one item
          * item_id - the item id for the record in the DigWF
          * pid - the noid portion of the pid/ARK for the item

        :returns: :class:`Items`
        '''
        url = '%s/getItems' % self.base_url
        r = requests.get(url, params=kwargs)
        if r.status_code == requests.codes.ok:
            return xmlmap.load_xmlobject_from_string(r.content, Items)  # possible r.text ?


class Item(xmlmap.XmlObject):
    '''class:`~eulxml.xmlmap.XmlObject` to read Item information returned
    by the DigWF API.

    (Not all fields provided by DigWF are mapped here; only those
    currently in use.)
    '''

    pid = xmlmap.StringField('@pid')
    'pid (noid portion of the ARK or Fedora pid)'
    item_id = xmlmap.StringField('@id')
    'item_id within the DigWF'
    control_key = xmlmap.StringField('@control_key')
    'control key (e.g., ocm or ocn number in euclid; unique per book, not per volume)'
    display_image_path = xmlmap.StringField('display_images_path')
    # do we need display images count ?
    'display image path'
    ocr_file_path = xmlmap.StringField('ocr_files_path')
    'path to OCR files (text & word position)'
    pdf = xmlmap.StringField('pdf_file')
    'path to PDF file'

    # incomplete - only mapping needed fields for now


class Items(xmlmap.XmlObject):
    '''class:`~eulxml.xmlmap.XmlObject` for the response returned by getItems.
    Has a count of the number of items found, and a list of :class:`Item`
    objects with details about each item.'''
    count = xmlmap.IntegerField('@count')
    'number of items in the result'
    items = xmlmap.NodeListField('item', Item)
    'List of items as instances of :class:`~readux.books.digwf.Item`'
