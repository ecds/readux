"""Admin module for managing pages."""
from django.contrib import admin
from apps.cms.models import ContentPage, HomePage, CollectionsPage

class HomePageAdmin(admin.ModelAdmin):
    """Home page admin class."""
    search_fields = ('featured_volumes', 'featured_collections')
    autocomplete_fields = ('featured_volumes',)
    class Meta: # pylint: disable=too-few-public-methods, missing-class-docstring
        model = HomePage

class ContentPageAdmin(admin.ModelAdmin):
    """Content page admin class."""
    # TODO: What are content pages? Add description to docstring above.
    class Meta: # pylint: disable=too-few-public-methods, missing-class-docstring
        model = ContentPage
        
class CollectionsPageAdmin(admin.ModelAdmin):
    """Collections page admin class."""
    class Meta: # pylint: disable=too-few-public-methods, missing-class-docstring
        model = CollectionsPage

admin.site.register(ContentPage, ContentPageAdmin)
admin.site.register(HomePage, HomePageAdmin)
admin.site.register(CollectionsPage, CollectionsPageAdmin)
