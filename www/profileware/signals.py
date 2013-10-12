from django.dispatch import Signal

profile_updated = Signal(providing_args=["request, profile"])


