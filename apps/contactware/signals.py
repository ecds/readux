from django.dispatch import Signal

contact_sent = Signal(providing_args=["request, contact"])


