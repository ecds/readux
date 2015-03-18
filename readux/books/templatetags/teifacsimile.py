'''
Custom template tags and filter for displaying TEI facsimile content
overlaid on top of a scaled page image.
'''

from django import template
from readux.books.models import TeiZone

register = template.Library()

def percent(a, b):
    # a as percentage of b
    # ensure both are cast to float, divide, then multiply by 100
    return (float(a) / float(b)) * 100

@register.filter
def zone_style(zone, scale):
    ''''Generate an HTMl attribute string for a
    :class:`readux.books.models.TeiZone` element, scaled to match the page
    image size.  Takes an element and a tuple of scale, which is used to
    adjust position information to the needed display size (i.e., the
    scale of the display image size relative to original OCR page image size).'''

    styles = {}
    if isinstance(zone, TeiZone):
        styles['width'] = '%.2f%%' % percent(zone.width, zone.page.width)

        if zone.type == 'textLine':
            # text lines are absolutely positioned boxes
            styles['left'] = '%.2f%%' % percent(zone.ulx, zone.page.width)
            styles['top'] = '%.2f%%' % percent(zone.uly, zone.page.height)
            # TODO: figure out how to determine this from ocr/teifacsimile
            # rather than assuming
            styles['text-align'] = 'left'
            # TODO: would be better to set font-size by the line, but
            # needs to be generated from word zones, not the line bounding box
        elif zone.type == 'string':
            # word strings are relatively positioned within a line

            if zone.preceding:
                # padding from end of previous word to beginning of the next
                styles['padding-left'] = '%.2f%%' % percent(zone.ulx - zone.preceding.lrx, zone.parent.width)
            elif zone.parent:
                # padding from beginning of the line to beginning of the first word,
                # if there is a difference
                if zone.ulx != zone.parent.ulx:
                    styles['padding-left'] = '%.2f%%' % percent(zone.ulx - zone.parent.ulx, zone.parent.width)

            styles['font-size'] = '%.2fpx' % (zone.lry * scale - zone.uly * scale)
            # NOTE: could *possibly* use viewport percentage sizing for font size,
            # but it would need javascript calculations to adjust when the page image is
            # smaller than the viewport
            # styles['font-size'] = '%.2fvw' % percent(zone.lry - zone.uly, zone.page.height)

            # may also want to attempt some letter-spacing styles to
            # get text to fill bounding boxes better

    if styles:
        return ';'.join(['%s:%s' % (k, v) for k, v in styles.iteritems()])
    # no styles
    return ''