import logging
from django.http import HttpResponse, HttpResponseBadRequest, Http404
from django.views.decorators.http import condition

from deepzoom import DeepZoomImageDescriptor

from eulfedora.server import TypeInferringRepository, Repository
from eulfedora.views import datastream_etag

from readux.books.models import Image
from readux.dyndzi import TILE_OVERLAP, TILE_SIZE
from readux.dyndzi.models import DziImage

logger = logging.getLogger(__name__)

def get_image_object_or_404(request, img_id):
    '''Utility method to get an image in Fedora or raise an
    :class:`~django.http.Http404` if the image is not found or accessible.

    :param img_id: image identifier (Fedora pid)
    '''
    try:
        # currently expected to return an Image cmodel with djatoka service
        repo = TypeInferringRepository()
        return repo.get_object(img_id)
    except:
        raise Http404

def image_etag(request, img_id, **kwargs):
    '''ETag method for Fedora Image datastream, to allow browser caching on DZI views

    :param img_id: image identifier (Fedora pid)
    '''
    return datastream_etag(request, img_id, Image.image.id, **kwargs)


def image_lastmodified(request, img_id , **kwargs):
    '''Last-modified for Fedora Image datastream, to allow browser caching
    on DZI views.

    :param img_id: image identifier (Fedora pid)
    '''
    # NOTE: next version of eulfedora should have a reusable datastream
    # last-modified method similar to existing datastream_etag
    repo = Repository()
    img = repo.get_object(img_id, type=Image)
    if img.image and img.image.exists:
        return img.image.created


@condition(etag_func=image_etag, last_modified_func=image_lastmodified)
def image_dzi(request, img_id):
    '''Generate and return the xml portion of a DZI file.

    :param img_id: image identifier (i.e. fedora object pid)
    '''
    img = get_image_object_or_404(request, img_id)
    return HttpResponse(DziImage(img).serialize(pretty=True),
                        content_type='application/xml')

@condition(etag_func=image_etag, last_modified_func=image_lastmodified)
def dzi_tile(request, img_id, level, column, row, fmt):
    '''Generate a single tile image for the specified level, column,
    row, and format.

    :param img_id: image identifier
    :param level: scale level in the dzi image pyramid
    :param column: column number for the requested tile
    :param row: row number for the requested tile
    :param fmt: image format (currently ignored)
    '''
    # NOTE: format is currently ignored

    # deepzoom functions expect numbers and not strings
    level = int(level)
    column = int(column)
    row = int(row)

    # calculate the appropriate djatoka call to make and return the appropriate scaled image tile
    # or error if any of the parameters are wrong

    # get the object (expected to be one of the image cmodels with djatoka services)
    img = get_image_object_or_404(request, img_id)

    # generate a deepzoom.py tile descriptor to help with level/scale/tile calculations
    tiledescriptor = DeepZoomImageDescriptor(width=img.width, height=img.height,
                                             tile_size=TILE_SIZE, tile_overlap=TILE_OVERLAP)

    # on invalid level or col/row, return 500 error
    columns, rows = tiledescriptor.get_num_tiles(float(level))
    if column == 1 and row == 1:
        logger.debug("level %d [%d x %d]", level, columns, rows)
    invalid_msg = None
    if column > columns:
        invalid_msg = 'requested column %d exceeds number of columns (%d) for this level' % \
                                       (column, columns)
    elif row > rows:
        invalid_msg = 'requested row %d exceeds number of rows (%d) for this level' % \
                      (row, rows)

    if invalid_msg is not None:
        return HttpResponseBadRequest('Cannot generate requested tile: %s' % invalid_msg)

    # for the smallest tile, if we need only one row and column
    # - scale only (djatoka doesn't like cropping to full size)
    if columns == 1 and rows == 1:
        # get the width and height for the full image at this zoom level
        levelwidth, levelheight = tiledescriptor.get_dimensions(level)
        # scale full image to needed level size and return
        logger.debug('Requesting scale=%d,%d', levelwidth, levelheight)
        return HttpResponse(img.get_region(scale='%d,%d' % (levelwidth, levelheight)),
                            content_type='image/jpeg')

    # otherwise, we need to crop and scale

    # get bounds for the currently requested tile on the current level
    sx1, sy1, sx2, sy2 = tiledescriptor.get_tile_bounds(level, column, row)

    # final size we want for the tile, after crop and scale
    scaledtilewidth = sx2 - sx1
    scaledtileheight = sy2 - sy1
    # get the scale factor for this level
    scale = tiledescriptor.get_scale(level)

    # deepzoom.py crops first and then scales, but djatoka does things
    # in the reverse order
    # scale the coordinates back up so we can crop based on the master image
    x1 = sx1/scale
    y1 = sy1/scale
    x2 = sx2/scale
    y2 = sy2/scale
    # calculate cropped portion width & height
    # (djatoka uses y,x,h,w for cropping)

    cropwidth = x2 - x1
    cropheight = y2 - y1
    # ... something about this may be slightly off, getting line
    # artifacts between tiles at certain zoom levels
    # (possibly a djatoka issue?)

    logger.debug("Requesting scale=%d,%d region=%d,%d,%d,%d",
                 scaledtilewidth, scaledtileheight,
                 y1, x1, cropheight, cropwidth)

    # call image/djatoka get_region with calculated region and scale
    return HttpResponse(img.get_region(scale='%s,%s' % \
                                       (scaledtilewidth, scaledtileheight),
                                       region='%d,%d,%d,%d' % \
                                       (y1, x1, cropheight, cropwidth)),
                        content_type='image/jpeg')
