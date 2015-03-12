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
        styles['left'] = '%spx' % (zone.ulx * scale)
        styles['top'] = '%spx' % (zone.uly * scale)
        styles['width'] = '%spx' % (zone.width * scale)
        styles['font-size'] = '%spx' % (zone.lry * scale - zone.uly * scale)

    return ';'.join(['%s:%s' % (k, v) for k, v in styles.iteritems()])