from django.contrib.auth.models import User
import json
import requests


from readux import __version__



class GithubApi(object):
    # partial GitHub API access
    # does NOT implement the full API, only those portions we need
    # for readux export functionality

    url = 'https://api.github.com'

    def __init__(self, token):
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': 'token %s' % token,
            'Accept': 'application/vnd.github.v3+json',
            'User-Agent': 'Readux %s / python-requests %s' % \
                (__version__, requests.__version__),
        })

    @staticmethod
    def github_token(user):
        # TODO: handle no github account, check for appropriate scope
        github_account = user.social_auth.filter(provider='github').first()
        return github_account.tokens

    @staticmethod
    def github_username(user):
        # TODO: handle no github account
        github_account = user.social_auth.filter(provider='github').first()
        return github_account.extra_data['login']

    @classmethod
    def connect_as_user(cls, user):
        '''Initialize a new GithubApi connection for the specified user.
        '''
        return cls(cls.github_token(user))

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
        # could get current user repos at: /user/repos
        # but that includes org repos user has access to
        # could specify type, but default of owner is probably fine for now
        response = self.session.get('%s/users/%s/repos' % (self.url, user))
        if response.status_code == requests.codes.ok:
            return response.json()
