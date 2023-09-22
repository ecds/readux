# Notes

## IIP Server Notes

The IIP server is running on a second Apache install `/root/apache` and a proxy is set up via the DreamHost panel.

All the image files are in `/home/images` and owned by dh_bb3cmt. That is the user for the fcgi process defined in `/root/apache/conf/httpd.conf`.

### Expired Certificates

Certbot should auto-renew the certificates. The most current certificates are located in

~~~sh
/etc/letsencrypt/live/iip.readux.io/
~~~

If cert has not been renewed, follow these steps as the root user.

~~~sh
certbot certonly -d iip.readux.io
~~~

Select option 2 "Place files in webroot directory (webroot)". Supply the following webroot:

~~~sh
/home/dh_bb3cmt/iip
~~~

New certs can be be added via the DreamHost panel Websites -> Secure certificates -> Settings -> Add New Cert -> Import

For the "Certificate", paste the contents of

~~~sh
cat /etc/letsencrypt/live/iip.readux.io/cert.pem
~~~

For the "RSA Private Key", paste the contents of

~~~sh
cat /etc/letsencrypt/live/iip.readux.io/privkey.pem
~~~

The other optional fields can be left blank.

## Elasticsearch Notes

### Expired Certs

The certs are managed by certbot but they have to be readable by the elasticsearch group. So we have to 1) add the elasticsearch group to the ownership and 2) copy the certs to a directory readable by the elasticsearch group. Certbot really locks down access to the certs it create.

Certbot should automatically create new certs, but if you need to make one, run:

~~~sh
sudo certbot renew --force-renewal
~~~

To copy the certs, we have to go full root:

~~~sh
sudo su -
cp /etc/letsencrypt/archive/search.readux.io/privkey{biggest number}.pem /etc/elasticsearch/certs/privkey.pem
cp /etc/letsencrypt/archive/search.readux.io/fullchain{biggest number}.pem /etc/elasticsearch/certs/fullchain.pem
exit
~~~

Add the elasticsearch group as an owner:

~~~sh
sudo chown root:elasticsearch /etc/elasticsearch/certs/*
~~~

Restart Elasticsearch

~~~sh
sudo service elasticsearch restart
~~~

## Convert existing SVG annotations

~~~python
import re
from bs4 import BeautifulSoup
from svgpathtools import Path
import re

for ua in j.userannotation_set.all():
    if ua.svg:
        soup = BeautifulSoup(ua.svg, 'xml')`
        d_path = soup.find('path')['d']
        path = Path(d_path)
        new_path = re.sub('[A-Za-z]\s', '', path.d())
        ua.oa_annotation['on'][0]['selector']['item']['value'] = f'<svg><polygon points="{new_path}"></polygon></svg>'
        ua.save()
~~~
