from readux.annotations.models import Annotation
from django.contrib.auth.models import User
from rest_framework import generics
from readux.annotations.serializers import AnnotationSerializer, AnnotationPostSerializer

class AnnotationListCreate(generics.ListCreateAPIView):
  """
  Endpoint that allows annotations to be listed or edited.
  """
  queryset = Annotation.objects.all()
  serializer_class = AnnotationSerializer

class AnnotationForPage(generics.ListAPIView):
  """
  Endpoint to to display annotations for a page.
  """
  serializer_class = AnnotationSerializer

  def get_queryset(self):
    return Annotation.objects.filter(volume_identifier=self.kwargs['vol']).filter(page=self.kwargs['page'])

class AnnotationDetail(generics.RetrieveUpdateDestroyAPIView):
  """
  Endpoint to update annotation.
  """
  serializer_class = AnnotationPostSerializer

  def get_queryset(self):
    return Annotation.objects.all()
