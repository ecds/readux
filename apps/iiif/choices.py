""" Collection of choices to be used in choice fields. """
from bcp47 import languages

class Choices():
    """ Collection of choices to be used in choice fields. """

    """ List of Mime type choices. """
    MIMETYPES = (
            ('text/html', 'HTML or web page'),
            ('application/json', 'JSON'),
            ('application/ld+json', 'JSON-LD'),
            ('application/pdf', 'PDF'),
            ('text/plain', 'Text'),
            ('application/xml', 'XML'),
            ('application/octet-stream', 'Other'),
        )

    """
    List of languages for use in model choice fields.
    """
    LANGUAGES = [(code, label,) for label, code in languages.items()]
