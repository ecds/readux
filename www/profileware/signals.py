from django.dispatch import Signal

user_personal_updated = Signal(providing_args=["request, user"])
user_preferences_updated = Signal(providing_args=["request, user"])


