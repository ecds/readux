from django.contrib import messages
from django.core.cache import cache
from django.core.urlresolvers import reverse
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.cache import cache_page
from django.views.decorators.vary import vary_on_cookie
from django.views.generic import TemplateView, View
from django.utils.decorators import method_decorator
from eulcommon.djangoextras.http import HttpResponseSeeOtherRedirect

from readux.books.github import GithubApi, GithubAccountNotFound


class AccountErrorView(TemplateView):
    '''Display an informative error message when a user gets an
    error linking their accounts. Currently only has text specific
    for "account already in use" error when a user tries to link
    a social auth account that is already been created.
    '''

    template_name = 'accounts/error.html'

    def get(self, request, *args, **kwargs):
        # This page is only relevant when someone has encountered an
        # error (which should set a message). To avoid confusion
        # with users staying on this error page after logging in
        # or out, redirect to the site home page when there
        # is no error message.
        if not messages.get_messages(request):
            return HttpResponseSeeOtherRedirect(reverse('site-index'))
        return super(AccountErrorView, self).get(request, *args, **kwargs)


class GithubRepositoryList(View):
    '''List of the current user's GitHub repositories, in a json format
    for use with jquery-ui autocomplete.

    GitHub repository list is cached to avoid hitting the GitHub API
    more frequently than necessary.  Caching currently uses the default
    configured cache timeout.
    '''

    def cache_key(self):
        return 'github-repos-%s' % self.request.user

    def get(self, request, *args, **kwargs):
        # cache repo list to avoid hitting github too frequently
        # using default cache timeout for now
        repo_list = cache.get(self.cache_key())
        if repo_list is None:
            try:
                github = GithubApi.connect_as_user(request.user)
            except GithubAccountNotFound:
                return HttpResponseBadRequest('GitHub account not found')

            repos = github.list_user_repos()
            # convert into format expected by jqueryui
            repo_list = [{'label': repo['full_name'], 'value': repo['html_url']}
                         for repo in repos]
            cache.set(self.cache_key(), repo_list)
        return JsonResponse(repo_list, safe=False)

