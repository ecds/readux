"""Admin module for custom styles."""
from django.contrib import admin
from .models import Style

class StyleAdmin(admin.ModelAdmin):
    pass

admin.site.register(Style, StyleAdmin)