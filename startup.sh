. venv/bin/activate
python manage.py runserver_plus --cert-file cert.pem --key-file key.pem 0.0.0.0:3000
# access the site with https://127.0.0.1:3000/
# adjust certificate settings in Chrome: https://stackoverflow.com/a/31900210/1792144 
