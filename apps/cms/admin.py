from django.contrib import admin
from apps.cms.models import ContentPage, HomePage

class HomePageAdmin(admin.ModelAdmin):
    search_fields = ('featured_volume', 'featured_collection')
    autocomplete_fields = ('featured_volume', 'featured_collection')
    class Meta:
        model = HomePage

class ContentPageAdmin(admin.ModelAdmin):
    class Meta:
        model = ContentPage
        

admin.site.register(ContentPage, ContentPageAdmin)
admin.site.register(HomePage, HomePageAdmin)
# Register your models here.
