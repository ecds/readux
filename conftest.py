""" Disable annoying logs for tests """
import logging

loggers_to_disable = [
    'httpretty',
    'httpretty.core',
    'elasticsearch',
    'wagtailmenus'
]

for logger in loggers_to_disable:
    logging.getLogger(logger).disabled = True
