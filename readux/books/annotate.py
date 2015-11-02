# methods for generating annotated tei
from readux.books.models import TeiZone


def annotated_tei(tei, annotations):
    # iterate throuth the annotations associated with this volume
    # and insert them into the tei based on the content they reference

    # perhaps some sanity-checking: compare annotation total vs
    # number actually added as we go page-by-page
    for note in annotations.all():
        ark = note.info()['ark']
        print note

    for page in tei.page_list:
        print 'tei page %s' % page.id
        page_annotations = annotations.filter(extra_data__contains=page.id)
        print page_annotations
        if page_annotations.exists():
            print 'page annotations'
            for note in page_annotations:
                print note.id
                insert_note(page, note)


    return tei


def annotation_to_tei(annotation):
    # todo: generate a tei note with annotation content
    # needs to handle formatting, tags, etc
    pass

def html_xpath_to_tei(xpath):
    # convert xpaths generated on the readux site to the
    # equivalent xpaths for the corresponding tei content
    return xpath.replace('div', 'tei:zone') \
                .replace('span', 'tei:w') \
                .replace('@id', '@xml:id')

def insert_note(teipage, annotation):

    info = annotation.info()
    # convert html xpaths to tei
    if info['ranges']:
        # NOTE: assuming single range selection for now
        # annotator model supports multiple, but UI does not currently
        # support it
        start_xpath = html_xpath_to_tei(info['ranges'][0]['start'])
        end_xpath = html_xpath_to_tei(info['ranges'][0]['end'])
        print 'xpaths - ', start_xpath, end_xpath
        start = teipage.node.xpath(start_xpath, namespaces=TeiZone.ROOT_NAMESPACES)
        end = teipage.node.xpath(end_xpath, namespaces=TeiZone.ROOT_NAMESPACES)
        print 'start node = ', start, ' end node = ', end
        # insert reference using start/end xpaths & offsets

    # if no ranges, then image annotation;
    # create a new surface/zone referencing the coordinates (?)


    # {u'ranges': [
    #     {u'start': u'//div[@id="fnstr.idm291623100992"]/span[1]',
    #     u'end': u'//div[@id="fnstr.idm291623092160"]/span[1]',
    #     u'startOffset': 0,
    #     u'endOffset': 5}], u'permissions': {},
    #     u'ark': u'http://testpid.library.emory.edu/ark:/25593/ntdfb', u'tags': [u'test', u' text-annotation']}
