from django.views.generic import TemplateView
from . import services as srv
from . import defaults as defs


class CollectionList(TemplateView):
  template_name = 'collection_list.html'

  def get_context_data(self, **kwargs):
    context = super().get_context_data(**kwargs)
    context['collections'] = srv.get_collections_recursively(defs.IIIF_UNIVERSE_COLLECTION_URL, 2)
    return context