from django.conf import settings

# templates to render the message subject with
CONTACTWARE_MESSAGE_SUBJECT_TEMPLATE = getattr(settings, 
        'CONTACTWARE_MESSAGE_SUBJECT_TEMPLATE', "contact/contact_message_subject.txt")

# template to render the message body with
CONTACTWARE_MESSAGE_BODY_TEMPLATE = getattr(settings, 
        'CONTACTWARE_MESSAGE_BODY_TEMPLATE', 'contact/contact_message_body.txt')

# default from email
CONTACTWARE_DEFAULT_FROM_EMAIL = getattr(settings, 'DEFAULT_FROM_EMAIL', '')

# default recipient email list
CONTACTWARE_DEFAULT_TO_EMAILS = getattr(settings, 'CONTACTWARE_DEFAULT_TO_EMAILS', 
        [e[1] for e in getattr(settings, 'MANAGERS', [])])

# Site protocol : http or https
CONTACTWARE_SITE_PROTOCOL = getattr(settings, 'SITE_PROTOCOL', '')

# Send emails out or just store them in the database
CONTACTWARE_SEND_EMAIL = getattr(settings, 'CONTACTWARE_SEND_EMAIL', True)

# Verify existance of sender's email address
CONTACTWARE_VERIFY_EMAIL = getattr(settings, 'CONTACTWARE_VERIFY_EMAIL', True)

# Whether to save the messages in the database or not
CONTACTWARE_STORE_DB = getattr(settings, 'CONTACTWARE_STORE_DB', True)

# Expire (remove) contacts that are older than CONTACTWARE_EXPIRY_DAYS from the database 
CONTACTWARE_EXPIRY_DAYS = getattr(settings, 'CONTACTWARE_EXPIRY_DAYS', 365)

# Check if content is spam
CONTACTWARE_VERIFY_SPAM = getattr(settings, 'CONTACTWARE_VERIFY_SPAM', True)

# Total message per IP address per day (to prevent spams)
CONTACTWARE_TOTAL_DAILY_MESSAGES_BY_IP = getattr(settings, 'CONTACTWARE_TOTAL_DAILY_MESSAGES_BY_IP', 5)



