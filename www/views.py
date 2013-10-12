# -*- coding: utf-8 -*-
from django.conf import settings
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.http import HttpRequest, HttpResponseRedirect
from django.views.generic import TemplateView
from django.core.urlresolvers import reverse

from toolware.utils.mixin import CsrfProtectMixin
from profileware.utils import get_stats_count_member_per_country

class HomeView(TemplateView):
    """ This is where everything starts. home page or landing page """
    
    template_name = "entrance/main.html"

    def get_context_data(self, **kwargs):
        context = super(HomeView, self).get_context_data(**kwargs)
        context['country_stats'] = get_stats_count_member_per_country()
        return context


class PlainTextView(TemplateView):
    """ View for rendering plain text files """

    def render_to_response(self, context, **kwargs):
        return super(PlainTextView, self).render_to_response(
                        context, content_type='text/plain', **kwargs)



