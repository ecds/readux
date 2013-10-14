__author__ = 'Val Neekman [neekware.com]'
__version__ = '0.0.1'
__description__ = 'This application runs after all other applications'

from django.db.models import signals

from finalize import finalize
import defaults

# Latch to post syncdb signal
signals.post_syncdb.connect(finalize)

# Autoload templates tags that we might need
if defaults.AUTO_LOAD_TEMPLATE_TAGS_LIST:
    from django import template
    for t in defaults.AUTO_LOAD_TEMPLATE_TAGS_LIST:
        template.add_to_builtins(t)
