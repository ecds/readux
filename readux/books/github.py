from django.contrib.auth.models import User
import json
import requests


from readux import __version__


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
            'User-Agent': 'Readux %s / python-requests %s' % \
                (__version__, requests.__version__),
        })

    @staticmethod
    def github_account(user):
        '''Static method to find a user's GitHub account (current or
        linked account via python-social-auth); raises
        :class:`GithubAccountNotFound` if none is found.'''
        account = user.social_auth.filter(provider='github').first()
        if account is None:
            raise GithubAccountNotFound
        return account

    @staticmethod
    def github_token(user):
        '''Retrieve a GitHub user account's token'''
        # TODO: handle no github account, check for appropriate scope
        return GithubApi.github_account(user).tokens

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

    def oauth_scopes(self):
        'Get a list of scopes available for the current oauth token'
        response = self.session.head('%s/user' % self.url)
        if response.status_code == requests.codes.ok:
            return response.headers['x-oauth-scopes'].split(',')

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
        'Get a list of a repositories by user'
        # could get current user repos at: /user/repos
        # but that includes org repos user has access to
        # could specify type, but default of owner is probably fine for now
        response = self.session.get('%s/users/%s/repos' % (self.url, user))
        if response.status_code == requests.codes.ok:
            return response.json()
