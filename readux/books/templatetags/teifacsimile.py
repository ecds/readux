'''
Custom template tags and filter for displaying TEI facsimile content
overlaid on top of a scaled page image.
'''

from django import template
from readux.books.models import TeiZone

register = template.Library()

@register.filter
def zone_style(zone, scale):
    ''''Generate an HTMl attribute string for a
    :class:`readux.books.models.TeiZone` element, scaled to match the page
    image size.  Takes an element and a tuple of scale, which is used to
    adjust position information to the needed display size (i.e., the
    scale of the display image size relative to original OCR page image size).'''

    styles = {}
    if isinstance(zone, TeiZone):
        styles['width'] = '%.2fpx' % (zone.width * scale)

        if zone.type == 'textLine':
            # text lines are absolutely positioned boxes
            styles['left'] = '%.2fpx' % (zone.ulx * scale)
            styles['top'] = '%.2fpx' % (zone.uly * scale)
            # TODO: figure out how to determine this from ocr/teifacsimile
            # rather than assuming
            styles['text-align'] = 'left'
            # TODO: would be better to set font-size by the line, but
            # needs to be generated from word zones, not the line bounding box
        elif zone.type == 'string':
            # word strings are relatively positioned within a line
            if zone.preceding:
                # padding from end of previous word to beginning of the next
                styles['padding-left'] = '%.2fpx' % ((zone.ulx - zone.preceding.lrx) * scale)
            elif zone.parent:
                # padding from beginning of the line to beginning of the first word
                styles['padding-left'] = '%.2fpx' % (zone.ulx * scale - zone.parent.ulx * scale)

            styles['font-size'] = '%.2fpx' % (zone.lry * scale - zone.uly * scale)

    if styles:
        return ';'.join(['%s:%s' % (k, v) for k, v in styles.iteritems()])
    # no styles
    return ''