""" Collection of choices to be used in choice fields. """
from bcp47 import languages

class Choices():
    """ Collection of choices to be used in choice fields. """

    """ List of Mime type choices. """
    MIMETYPES = (
            ('text/html', 'HTML'),
            ('application/json', 'JSON'),
            ('application/ld+json', 'JSON-LD'),
            ('application/xml', 'XML'),
            ('text/plan', 'Text'),
        )

    """
    List of languages for use in model choice fields.
    """
    LANGUAGES = [(code, label,) for label, code in languages.items()]
