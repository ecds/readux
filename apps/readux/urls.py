"""URL patterns for the Readux app"""
from django.urls import path
from . import views, annotations
# from .search import SearchManifestCanvas

urlpatterns = [
    path('collection/', views.CollectionsList.as_view(), name='collections list'),
    path('volume/', views.VolumesList.as_view(), name='volumes list'),
    path('collection/<collection>/', views.CollectionDetail.as_view(), name="collection"),
    path('volume/<volume>', views.VolumeDetail.as_view(), name='volume'),
    path('volume/<volume>/page/all', views.PageDetail.as_view(), name='volumeall'),
    # url for page altered to prevent conflict with Wagtail
    # TODO: find another way to resolve this conflict
    path('volume/<volume>/page/<page>', views.PageDetail.as_view(), name='page'),
    path('volume/<volume>/export', views.ExportOptions.as_view(), name='export'),
    path(
        'volume/<volume>/<filename>/export_download',
        views.ExportDownload.as_view(),
        name='export_download'
    ),
    path(
        'volume/<filename>/export_download_zip',
        views.ExportDownloadZip.as_view(),
        name='export_download_zip'
    ),
    path('annotations/', annotations.Annotations.as_view(), name='post_user_annotations'),
    path(
        'annotations/<username>/<volume>/list/<canvas>',
        annotations.Annotations.as_view(),
        name='user_annotations'
    ),
    path('annotations-crud/', annotations.AnnotationCrud.as_view(), name='crud_user_annotation'),
    # path('search/', views.VolumeSearch.as_view(), name='search'),
    path('_anno_count/<volume>/<page>', views.AnnotationsCount.as_view(), name='_anno_count'),
    # path('search/volume/pages', SearchManifestCanvas.as_view(), name='search_pages'),
]
