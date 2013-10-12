from django.contrib import admin
from django.contrib.sites.models import Site

# Register Site Model with Django Admin
class SiteAdmin(admin.ModelAdmin):
    list_display = ('id', 'domain', 'name',)
    search_fields = ('domain', 'name', 'id',)
    ordering = ('id', 'domain')

# Unregister and re-register Site Models with Django Admin
try:
    admin.site.unregister(Site)
except:
    pass
admin.site.register(Site, SiteAdmin)
