# IIP Server Notes

The IIP server is running on a second Apache install `/root/apache` and a proxy is set up via the DreamHost panel.

All the image files are in `/home/images` and owned by dh_bb3cmt. That is the user for the fcgi process defined in `/root/apache/conf/httpd.conf`.

# Convert existing SVG annotations

~~~python
import re
from bs4 import BeautifulSoup
from svgpathtools import Path
import re

for ua in j.userannotation_set.all():
    if ua.svg:
        soup = BeautifulSoup(ua.svg, 'xml')
        d_path = soup.find('path')['d']
        path = Path(d_path)
        new_path = re.sub('[A-Za-z]\s', '', path.d())
        ua.oa_annotation['on'][0]['selector']['item']['value'] = f'<svg><polygon points="{new_path}"></polygon></svg>'
        ua.save()
~~~
