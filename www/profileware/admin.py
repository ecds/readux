from django import forms
from django.contrib import admin
from django.contrib.auth import get_user_model; User = get_user_model()
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

try:
    from userware.forms import UserCreationForm
    from userware.forms import UserChangeForm
except ImportError:
    from django.contrib.auth.forms import UserCreationForm
    from django.contrib.auth.forms import UserChangeForm

class UserAdmin(DjangoUserAdmin):
    """ Customize Admin """
    
    fieldsets = (
        (
            _('Required info'), 
            { 
                'fields': (
                    'username', 
                    'email',
                    'password',
                )
            }
        ),
        (   
            _('Personal info'), 
            {
                'fields': (
                    'first_name',
                    'last_name',
                    'about',
                )
            }
        ),
        (
            _('Permissions'), 
            {
                'fields': (
                    'is_active',
                    'is_staff',
                    'is_superuser',
                    'groups',
                    'user_permissions',
                )
            }
        ),
        (
            _('Important dates'), 
            {
                'fields': (
                    'last_login',
                    'date_joined',
                )
            }
        ),

    )
    
    add_fieldsets = (
        (
            _('Required info'),
            {
                'classes': ('wide',),
                'fields': ('username', 'email', 'password1', 'password2',)
            }
        ),
    )
    
    form = UserChangeForm
    add_form = UserCreationForm

    list_display = ('id', 'username', 'email', 'first_name', 'last_name', 'slug', 'is_staff', 'last_login', 'date_updated', 'date_joined',  )
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'groups',)
    search_fields = ('first_name', 'last_name', 'username', 'email', 'id',)
    ordering = ('username', 'email',)
    filter_horizontal = ('groups', 'user_permissions',)

# Now Register the User
try:
    admin.site.unregister(User)
except:
    pass
admin.site.register(User, UserAdmin)


