# file dyndzi/__init__.py
# 
#   Copyright 2012 Emory University Libraries
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.

'''

:mod:`readux.dyndzi` is a Django application for dynamically
generating and displaying `Deep Zoom Images`_ (DZI).

The current implementation uses `Fedora-Commons Repository`_ content
(by way of :mod:`eulfedora`) which has the `Djatoka Image server`_
configured as an image service, although it shoudl be possible te generalize this to work with arbitrary images and alternative image services.

.. _Deep Zoom Images: http://msdn.microsoft.com/en-us/library/cc645077%28v=vs.95%29.aspx
.. _Fedora-Commons repository: http://fedora-commons.org/
.. _Djatoka Image server: http://sourceforge.net/apps/mediawiki/djatoka

.. Note::

  :mod:`readux.dyndzi` currently depends on `DeepZoomTools`_ for some
  of the DZI image tile calculations; however, that package is
  currently not available on PyPi and so is not installable via pip.
  To install directly from github with pip, use the following::
  
    $ pip install -e git://github.com/openzoom/deepzoom.py.git#egg=deepzoom

The following configurations can be set in Django settings to
customize the DZI images and tiles:

 * **DYNDZI_TILE_SIZE** (default: 256)
 * **DYNDZI_TILE_OVERLAP** (default: 1)
 * **DYNDZI_IMAGE_FORMAT** (default: jpg)

:mod:`readux.dyndzi` includes a copy of the `Seadragon Ajax
Javascript`_ and default button images for embedding and displaying
DZI.

.. _Seadragon Ajax Javascript: http://expression.microsoft.com/en-us/gg413362

To use this module, include :mod:`dyndzi` in your **INSTALLED_APPS**,
and then bind the urls in your project, e.g.::

  url(r'^dzi/', include('readux.dyndzi.urls', namespace='deepzoom')),


Then include and the necessary javascript in the template where you
will be displaying the DZI content::

  <script type="text/javascript" src="{{ STATIC_URL }}js/seadragon-min.js"></script> 
  <script type="text/javascript" charset="utf-8">
     $(document).ready(function () {
        // init seadragon
        Seadragon.Config.imagePath = "{{ STATIC_URL }}/js/seadragon/img/"; 
        viewer = new Seadragon.Viewer("dzi-container");
        viewer.openDzi("{% url deepzoom:dzi image_id %}");
     });
  </script>

  ...

  <div id="dzi-container"> </div>


See the `Seadragon Ajax Javascript`_ documentation for more details.

'''

import logging
from django.conf import settings

logger = logging.getLogger(__name__)

TILE_SIZE = getattr(settings, 'DYNDZI_TILE_SIZE', 256)
TILE_OVERLAP = getattr(settings, 'DYNDZI_TILE_OVERLAP', 1)
IMAGE_FORMAT = getattr(settings, 'DYNDZI_IMAGE_FORMAT', 'jpg')

logger.info('tile size=%d overlap=%d format=%s' \
            % (TILE_SIZE, TILE_OVERLAP, IMAGE_FORMAT))
