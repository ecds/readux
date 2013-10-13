from django.dispatch import Signal

user_switched_on = Signal(providing_args=['request, switched_user'])
user_switched_off = Signal(providing_args=['request, switched_user'])



