"""Django admin module for manifests"""

from django.contrib import admin
from django.http import HttpResponseRedirect
from django.urls.conf import path
from import_export import resources, fields
from import_export.admin import ImportExportModelAdmin
from import_export.widgets import ManyToManyWidget, ForeignKeyWidget
from django_summernote.admin import SummernoteModelAdmin
from .models import Manifest, Note, ImageServer, RelatedLink, Language
from .forms import ManifestAdminForm
from .views import AddToCollectionsView, MetadataImportView
from ..kollections.models import Collection


class ManifestResource(resources.ModelResource):
    """Django admin manifest resource."""

    collection_id = fields.Field(
        column_name="collections",
        attribute="collections",
        widget=ManyToManyWidget(Collection, field="label"),
    )
    image_server_link = fields.Field(
        column_name="image_server",
        attribute="image_server",
        widget=ForeignKeyWidget(ImageServer, "image_server"),
    )

    class Meta:  # pylint: disable=too-few-public-methods, missing-class-docstring
        model = Manifest
        import_id_fields = ("id",)
        fields = (
            "id",
            "pid",
            "label",
            "summary",
            "author",
            "searchable",
            "published_city",
            "published_date",
            "publisher",
            "image_server_link",
            "pdf",
            "metadata",
            "attribution",
            "logo",
            "logo_url",
            "license",
            "viewingdirection",
            "collection_id",
        )


class RelatedLinksInline(admin.TabularInline):
    model = RelatedLink
    exclude = ("id",)
    fields = (
        "link",
        "is_structured_data",
        "format",
    )
    extra = 1
    min_num = 0


class SummernoteMixin(SummernoteModelAdmin):
    class Media:
        # NOTE: have to include these js and css dependencies for summernote when not using iframe
        js = (
            "//code.jquery.com/jquery-3.7.1.min.js",
            "//cdn.jsdelivr.net/npm/jquery.ui.widget@1.10.3/jquery.ui.widget.min.js",
        )
        css = {
            "all": [
                "//cdn.jsdelivr.net/npm/summernote@0.8.20/dist/summernote-lite.min.css"
            ],
        }


class ManifestAdmin(ImportExportModelAdmin, SummernoteMixin, admin.ModelAdmin):
    """Django admin configuration for manifests"""

    resource_class = ManifestResource
    exclude = ("id",)
    filter_horizontal = ("collections",)
    list_display = (
        "id",
        "pid",
        "label",
        "created_at",
        "author",
        "published_date",
        "published_city",
        "publisher",
    )
    search_fields = ("id", "pid", "label", "author", "published_date")
    summernote_fields = ("summary",)
    form = ManifestAdminForm
    actions = ["add_to_collections_action"]
    inlines = [RelatedLinksInline]
    change_list_template = "admin/change_list_override.html"

    def add_to_collections_action(self, request, queryset):
        """Action choose manifests to add to collections"""
        selected = queryset.values_list("pk", flat=True)
        selected_ids = ",".join(str(pk) for pk in selected)
        return HttpResponseRedirect(f"add_to_collections/?ids={selected_ids}")

    add_to_collections_action.short_description = (
        "Add selected manifests to collection(s)"
    )

    def get_urls(self):
        urls = super().get_urls()
        my_urls = [
            path(
                "add_to_collections/",
                self.admin_site.admin_view(AddToCollectionsView.as_view()),
                {
                    "model_admin": self,
                },
                name="AddManifestsToCollections",
            ),
            path(
                "manifest_metadata_import/",
                self.admin_site.admin_view(MetadataImportView.as_view()),
                {
                    "model_admin": self,
                },
                name="MultiManifestMetadataImport",
            ),
        ]
        return my_urls + urls


class NoteAdmin(admin.ModelAdmin):
    """Django admin configuration for a note."""

    class Meta:  # pylint: disable=too-few-public-methods, missing-class-docstring
        model = Note


class ImageServerResource(resources.ModelResource):
    """Django admin ImageServer resource."""

    class Meta:  # pylint: disable=too-few-public-methods, missing-class-docstring
        model = ImageServer
        fields = ("id", "server_base", "storage_service", "storage_path")


class ImageServerAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    """Django admin settings for ImageServer."""

    resource_class = ImageServerResource
    list_display = ("server_base",)


class LanguageResource(resources.ModelResource):
    """Django admin Language resource."""

    class Meta:
        model = Language
        fields = ("code", "name")


class LanguageAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    """Django admin settings for Language."""

    resource_class = LanguageResource
    list_display = ("name", "code")


admin.site.register(Manifest, ManifestAdmin)
admin.site.register(Note, NoteAdmin)
admin.site.register(ImageServer, ImageServerAdmin)
admin.site.register(Language, LanguageAdmin)
