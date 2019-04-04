from django.contrib import admin
from apps.cms.models import ContentPage, HomePage

class HomePageAdmin(admin.ModelAdmin):
    search_fields = ('featured_volumes', 'featured_collections')
    autocomplete_fields = ('featured_volumes', 'featured_collections')
    class Meta:
        model = HomePage

class ContentPageAdmin(admin.ModelAdmin):
    class Meta:
        model = ContentPage
        

admin.site.register(ContentPage, ContentPageAdmin)
admin.site.register(HomePage, HomePageAdmin)
# Register your models here.
