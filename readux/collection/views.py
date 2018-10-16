from django.views.generic import TemplateView
import readux.collection.services

# Create your views here.
class CollectionList(TemplateView):
  template_name = 'collection_list.html'

  def get_context_data(self, **kwargs):
    context = super().get_context_data(**kwargs)
    context['collections'] = readux.collection.services.get_all_collections()
    print(len(context['collections']))
    return context