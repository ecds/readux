from forms import UserPasswordResetForm
from forms import UserSetPasswordForm
from django.conf.urls import patterns, include, url

from views import *

urlpatterns = patterns('',

    url(
        r'^login/$',
        UserLoginView.as_view(), 
        name='userware_login'
    ),

    url(
        r'^logout/$',
        UserLogoutView.as_view(), 
        name='userware_logout'
    ),

    url(
        r'^password/change/$',
        UserChangePassword.as_view(),
        name='userware_password_change'
    ),

    url(
        r'^delete/$',
        UserDeleteView.as_view(),
        name='userware_delete_account'
    ),

    url(
        r'^switch/on/$',
        UserSwitchOnView.as_view(),
        name='userware_switch_on'
    ),

    # user forgot his/her password again. ask for username or email and send a reset link
    url(
        r'^password/reset/$',
        'django.contrib.auth.views.password_reset',
        {
            'password_reset_form': UserPasswordResetForm,
            'template_name': 'user/password_reset_form.html',
            'subject_template_name': 'user/password_reset_email_subject.txt',
            'email_template_name': 'user/password_reset_email.txt',
            'post_reset_redirect': 'userware_password_reset_done',
        },
        name='userware_password_reset',
    ),

    # an email has been sent to the provided email address with the link to reset password
    url(
        r'^password/reset/done/$',
        'django.contrib.auth.views.password_reset_done',
        {
            'template_name': 'user/password_reset_done.html',
        },
        name='userware_password_reset_done',
    ),
       
    # password reset link has been clicked on, forms allows for a new password and confirmation
    url(
        r'^password/reset/confirm/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/$',
        'django.contrib.auth.views.password_reset_confirm',
        {
            'set_password_form': UserSetPasswordForm,
            'template_name': 'user/password_reset_confirm.html',
            'post_reset_redirect': 'userware_password_reset_complete',
        },
        name='userware_password_reset_confirm',
    ),

    # system has changed the password and redirect to this template for the final success message
    url(
        r'^password/reset/complete/$',
        'django.contrib.auth.views.password_reset_complete',
        {
            'template_name': 'user/password_reset_complete.html',
        },
        name='userware_password_reset_complete',
    ),

    url(
        r'^',
        UserAccountView.as_view(),
        name='userware_account_settings'
    ),

)


