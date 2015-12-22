from django.contrib.auth.models import User
import json
import requests


from readux import __version__



class GithubApi(object):

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

    def create_repo(self, name, description=None):
        repo_data = {'name': name}
        if description:
            repo_data['description'] = description
        # other options we might care about: homepage url, private/public,
        # has_issues, has_wiki, has_downloads, license_template
        response = self.session.post('%s/user/repos' % self.url,
            data=json.dumps(repo_data))
        return response.status_code == requests.codes.created
