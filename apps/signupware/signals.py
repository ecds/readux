from django.dispatch import Signal


# A new user just signed up
signup_new = Signal(providing_args=["request", "user"])



