from eulxml import xmlmap
from readux.dyndzi import TILE_OVERLAP, TILE_SIZE, IMAGE_FORMAT

class _BaseDzi(xmlmap.XmlObject):
    # base class with common attributes for all dzi/dzc xml
    ROOT_NS = 'http://schemas.microsoft.com/deepzoom/2008'
    ROOT_NAMESPACES = {'dz' : ROOT_NS}

class DziImage(_BaseDzi):
    '''A simple :class:`~eulxml.xmlmap.XmlObject` subclass for
    generating generate the XML portion of a DZI file.

    Initialize with any object that has `width` and `height`
    attributes, e.g.::

       myimg = MyImageObject()
       mydzi = DziImage(myimg)
       print mydzi.serialize()

    '''
    ROOT_NAME = 'Image'
    tilesize = xmlmap.IntegerField('@TileSize')
    'tile size - `@TileSize` attribute'
    overlap = xmlmap.IntegerField('@Overlap')
    'tile overlap - `@Overlap` attribute'
    format = xmlmap.StringField('@Format')
    'image format - `@Format` attribute'
    width = xmlmap.IntegerField('dz:Size/@Width')
    'image width - `Size/@Width`'
    height = xmlmap.IntegerField('dz:Size/@Height')
    'image height - `Size/@Height`'

    def __init__(self, obj, *args, **kwargs):
        opts = {
            'tilesize': TILE_SIZE,
            'overlap': TILE_OVERLAP,
            'format': IMAGE_FORMAT,
            'width': obj.width,
            'height': obj.height
            }
        # passed in args should supercede defaults
        opts.update(kwargs)
        super(DziImage, self).__init__(*args, **opts)
        
