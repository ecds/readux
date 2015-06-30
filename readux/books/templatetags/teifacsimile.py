'''
Custom template tags and filter for displaying TEI facsimile content
overlaid on top of a scaled page image.
'''

from django import template
from django.utils.safestring import mark_safe
from readux.books.models import TeiZone

register = template.Library()

def percent(a, b):
    # a as percentage of b
    # ensure both are cast to float, divide, then multiply by 100
    return (float(a) / float(b)) * 100

@register.filter
def zone_style(zone, scale):
    ''''Generate an HTML style and data attributes for a
    :class:`readux.books.models.TeiZone` element so that the text can be
    scaled and positioned for display on a resized page image.
    Takes a zone element (expected to have x/y coordinate attirbutes) and
    a scale, which is used for fallback sizing where percentages cannot
    be used.  Sets a vhfontsize data attribute for use with javascript
    to adjust font sizes relative to the viewport.'''

    styles = {}
    data = {}
    if isinstance(zone, TeiZone):

        if zone.type in ['textLine', 'line']:
            # text lines are absolutely positioned boxes
            styles['left'] = '%.2f%%' % percent(zone.ulx, zone.page.width)
            styles['top'] = '%.2f%%' % percent(zone.uly, zone.page.height)

            # width relative to page size
            styles['width'] = '%.2f%%' % percent(zone.width, zone.page.width)
            styles['height'] = '%.2f%%' % percent(zone.height, zone.page.height)

            # TODO: figure out how to determine this from ocr/teifacsimile
            # rather than assuming
            styles['text-align'] = 'left'

            # set pixel-based font size for browsers that don't support viewport based sizes.
            # for mets-alto, use average height of words in the line to calculate font size
            # for abbyy ocr, no word zones exist, so just use line height
            styles['font-size'] = '%.2fpx' % ((zone.avg_height or zone.height) * scale)

            # calculate font size as percentage of page height;
            # this will be used by javascript to calculate as % of viewport height
            data['vhfontsize'] = '%.2f' % percent(zone.lry - zone.uly, zone.page.height)

        elif zone.type == 'string':
            # set width & height relative to *parent* line, not the whole page
            styles['width'] = '%.2f%%' % percent(zone.width, zone.parent.width)
            styles['height'] = '%.2f%%' % percent(zone.height, zone.parent.height)

            # position words absolutely within the line
            styles['left'] = '%.2f%%' % percent(zone.ulx - zone.parent.ulx, zone.parent.width)

    attrs = []
    if styles:
        attrs.append('style="%s"' % ';'.join(['%s:%s' % (k, v) for k, v in styles.iteritems()]))
    if data:
        attrs.append(' '.join(['data-%s="%s"' % (k, v) for k, v in data.iteritems()]))
    if zone.id:
        attrs.append('id=%s' % zone.id)

    return mark_safe(' '.join(attrs))