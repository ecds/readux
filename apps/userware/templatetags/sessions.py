# import logging
# from django import template
# from ..utils import get_all_logged_in_users
# from ..utils import get_sessions_for_user
# 
# register = template.Library()
# 
# 
# @register.filter()
# def user_sessions(user):
#     return get_sessions_for_user(user)
# 
# 
# @register.filter()
# def logged_users():
#     return get_all_logged_in_users()
# 
# 
# 
