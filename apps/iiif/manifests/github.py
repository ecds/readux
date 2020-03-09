from django.contrib.auth.models import User
import json
import requests

#from readux import __version__

__version__="2.0.0"

class GithubApiException(Exception):
    pass

class GithubAccountNotFound(GithubApiException):
    pass


class GithubApi(object):
    '''Partial GitHub API access.
    Does **NOT** implement the full API, only those portions currently
    needed for readux export functionality.'''

    url = 'https://api.github.com'

    def __init__(self, token):
        # initialize a request session that will pass the oauth token
        # as an authorization header
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': 'token %s' % token,
            'Accept': 'application/vnd.github.v3+json',
            'User-Agent': 'Readux %s / python-requests %s' % (__version__, __version__),
        })

    @staticmethod
    def github_account(user):
        '''Static method to find a user's GitHub account (current or
        linked account via python-social-auth); raises
        :class:`GithubAccountNotFound` if none is found.'''
        account = user.socialaccount_set.filter(provider='github').first()
        if account is None:
            raise GithubAccountNotFound
        return account

    @staticmethod
    def github_token(user):
        '''Retrieve a GitHub user account's token'''
        # TODO: handle no github account, check for appropriate scope
        sa = GithubApi.github_account(user)
        sa.socialtoken_set.first().token
        return sa.socialtoken_set.first().token

    @staticmethod
    def github_username(user):
        '''Retrieve the GitHub username for a linked GitHub social auth
        account'''
        return GithubApi.github_account(user).extra_data['login']

    @classmethod
    def connect_as_user(cls, user):
        '''Initialize a new GithubApi connection for the specified user.
        '''
        return cls(cls.github_token(user))

    def oauth_scopes(self, test=False):
        'Get a list of scopes available for the current oauth token'
        # TODO: httpretty does not like the HEAD method, so this is a quick
        # workaround for testing. It might be fine to just use GET.
        if test:
            response = self.session.get('%s/user' % self.url)
        else:
            response = self.session.head('%s/user' % self.url)

        if response.status_code == requests.codes.ok:
            return response.headers['x-oauth-scopes'].split(', ')

    def create_repo(self, name, description=None, homepage=None):
        'Create a new user repository with the specified name.'
        repo_data = {'name': name}
        if description:
            repo_data['description'] = description
        if homepage:
            repo_data['homepage'] = homepage
        # other options we might care about: homepage url, private/public,
        # has_issues, has_wiki, has_downloads, license_template
        response = self.session.post('%s/user/repos' % self.url,
            data=json.dumps(repo_data))
        return response.status_code == requests.codes.created

    def list_repos(self, user):
        '''Get a list of a repositories by user'''
        # could get current user repos at: /user/repos
        # but that includes org repos user has access to
        # could specify type, but default of owner is probably fine for now

        repos = []
        page_url = '%s/users/%s/repos?per_page=3' % (self.url, user)
        response = self.session.get(page_url)
        repos += response.json()


        headers = response.headers
        while 'link' in headers and 'next' in headers['link']:
            links = {}
            linkHeaders = headers["link"].split(", ")
            for linkHeader in linkHeaders:
                (url, rel) = linkHeader.split("; ")
                url = url[1:-1]
                rel = rel[5:-1]
                links[rel] = url
        
            page_url = links.get('next')
            response = self.session.get(page_url)
            repos += response.json()
            headers = response.headers
    
        return repos

    def list_user_repos(self):
        '''Get a list of the current user's repositories'''
        response = self.session.get('%s/user/repos' % self.url)
        if response.status_code == requests.codes.ok:
            repos = response.json()
            # repository list is paged; if there is a rel=next link,
            # there is more content
            while response.links.get('next', None):
                # for now, assuming that if the first response is ok
                # subsequent ones will be too
                response = self.session.get(response.links['next']['url'])
                repos.extend(response.json())
            return repos

    def create_pull_request(self, repo, title, head, base,
                            text=None):
        '''Create a new pull request.
        https://developer.github.com/v3/pulls/#create-a-pull-request

        :param repo: repository where the pull request will be created,
            in owner/repo format
        :param title: title of the pull request
        :param head: name of the branch with the changes to be pulled in
        :param base: name of the branch where changes should will be
            pulled into (e.g., master)
        :param text: optional text body content for the pull request
        '''
        # pull request url is /repos/:owner/:repo/pulls
        data = {'title': title, 'head': head, 'base': base}
        if text is not None:
            data['body'] = text

        response = self.session.post('%s/repos/%s/pulls' % (self.url, repo),
                                     data=json.dumps(data))
        if response.status_code == requests.codes.created:
            return response.json()
        else:
            error_message = 'Error creating pull request'
            try:
                error_message += ': %s' % response.json()['message']
            except Exception:
                pass

            raise GithubApiException(error_message)