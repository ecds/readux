from django.contrib import admin
from apps.cms.models import ContentPage, HomePage, CollectionsPage, VolumesPage

class HomePageAdmin(admin.ModelAdmin):
    search_fields = ('featured_volumes', 'featured_collections')
    autocomplete_fields = ('featured_volumes',)
    class Meta:
        model = HomePage

class ContentPageAdmin(admin.ModelAdmin):
    class Meta:
        model = ContentPage
        
class CollectionsPageAdmin(admin.ModelAdmin):
    class Meta:
        model = CollectionsPage

class VolumesPageAdmin(admin.ModelAdmin):
    class Meta:
        model = VolumesPage

admin.site.register(ContentPage, ContentPageAdmin)
admin.site.register(HomePage, HomePageAdmin)
admin.site.register(CollectionsPage, CollectionsPageAdmin)
admin.site.register(VolumesPage, VolumesPageAdmin)
# Register your models here.
