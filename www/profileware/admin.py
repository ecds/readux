from django.contrib import admin
from models import UserProfile

class UserProfileAdmin(admin.ModelAdmin):

    list_display = (
        'user',
        'id',
        'username',
        'first_name',
        'last_name',
        'personal_about', 
        'primary_email', 
        'updated_at',
        'created_at',
    )

    search_fields = [
        'id',
        'user__username',
        'primary_email',
        'first_name',
        'last_name', 
    ]

    list_per_page = 25

# Register Profile
admin.site.register(UserProfile, UserProfileAdmin)






