"""GitHub Module"""
import json
import requests
from django.contrib.auth.models import User

#from readux import __version__

__version__ = "2.0.0"

class GithubApiException(Exception):
    """custom exception"""
    pass

class GithubAccountNotFound(GithubApiException):
    """custom exception"""
    pass


class GithubApi(object):
    """
    Partial GitHub API access.
    Does **NOT** implement the full API, only those portions currently
    needed for readux export functionality.
    """

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
        social_account = GithubApi.github_account(user)
        return social_account.socialtoken_set.first().token

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
        """Get a list of scopes available for the current oauth token

        :param test: Flag for if code is being executed for testing, defaults to False
        :type test: bool, optional
        :return: List of OAuth headers
        :rtype: list
        """
        # TODO: httpretty does not like the HEAD method, so this is a quick
        # workaround for testing. It might be fine to just use GET.
        if test:
            response = self.session.get('%s/user' % self.url)
        else:
            response = self.session.head('%s/user' % self.url) # pragma: no cover

        if response.status_code == requests.codes.ok:
            return response.headers['x-oauth-scopes'].split(', ')
        return None

    def create_repo(self, name, user, description=None, homepage=None):
        """Create a new user repository with the specified name.

        :param name: Repo name
        :type name: str
        :param description: Repo description, defaults to None
        :type description: str, optional
        :param homepage: URL for site, defaults to None
        :type homepage: str, optional
        :return: True if the POST succeeds.
        :rtype: bool
        """
        self.session.headers['Authorization'] = f'token {self.github_token(user)}'
        repo_data = {'name': name}
        if description:
            repo_data['description'] = description
        if homepage:
            repo_data['homepage'] = homepage
        # other options we might care about: homepage url, private/public,
        # has_issues, has_wiki, has_downloads, license_template
        response = self.session.post(
            '{u}/user/repos'.format(u=self.url),
            data=json.dumps(repo_data)
        )
        return response.status_code == requests.codes.created

    def list_repos(self, user):
        """Get a list of a repositories by person

        :param user: GitHub username
        :type user: str
        :return: List of person's repositories.
        :rtype: list
        """
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
            link_headers = headers["link"].split(", ")
            for link_header in link_headers:
                (url, rel) = link_header.split("; ")
                url = url[1:-1]
                rel = rel[5:-1]
                links[rel] = url

            page_url = links.get('next')
            response = self.session.get(page_url)
            repos += response.json()
            headers = response.headers

        return repos

    def list_user_repos(self):
        """Get a list of the current person's repositories

        :return: List of person's repositories
        :rtype: list
        """
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
        return None

    def create_pull_request(self, repo, title, head, base, text=None):
        """Create a new pull request.
        https://developer.github.com/v3/pulls/#create-a-pull-request

        :param repo: repository where the pull request will be created,
            in owner/repo format
        :param title: title of the pull request
        :param head: name of the branch with the changes to be pulled in
        :param base: name of the branch where changes should will be
            pulled into (e.g., master)
        :param text: optional text body content for the pull request
        """
        # pull request url is /repos/:owner/:repo/pulls
        data = {'title': title, 'head': head, 'base': base}
        if text is not None:
            data['body'] = text

        response = self.session.post('%s/repos/%s/pulls' % (self.url, repo),
                                     data=json.dumps(data))
        if response.status_code == requests.codes.created:
            return response.json()
        error_message = 'Error creating pull request'
        try:
            error_message += ': %s' % response.json()['message']
        except Exception:
            pass

        raise GithubApiException(error_message)
