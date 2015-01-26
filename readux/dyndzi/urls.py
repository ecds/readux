# file dyndzi/urls.py
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

from django.conf.urls import patterns, url

urlpatterns = patterns('readux.dyndzi.views',
    url(r'^(?P<img_id>[^/]+).dzi$', 'image_dzi', name='dzi'),
    # url with standard naming convention for DZI tile images
    url(r'^(?P<img_id>[^/]+)_files/(?P<level>\d+)/(?P<column>\d+)_(?P<row>\d+).(?P<fmt>(jpg|png))$',
       'dzi_tile', name='tile'),
)
