from django.conf.urls import url
from django.views.generic import TemplateView

urlpatterns = [
    url(r'^error/', TemplateView.as_view(template_name="accounts/error.html"),
        name='error'),
]