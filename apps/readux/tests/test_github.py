from django.test import TestCase
from apps.iiif.manifests.github import GithubApi, GithubApiException, GithubAccountNotFound
from apps.users.tests.factories import UserFactory, SocialAccountFactory, SocialAppFactory, SocialTokenFactory
import httpretty

class TestGithubApi(TestCase):
    def setUp(self):
        self.user = UserFactory.create()
        self.sa_app = SocialAppFactory.create(
            provider = 'github',
            name = 'GitHub'
        )
        self.sa_acct = SocialAccountFactory.create(
            provider='github',
            user_id=self.user.pk,
            extra_data={'login': self.user.username}
        )
        self.sa_token = SocialTokenFactory.create(
            app_id = self.sa_app.pk,
            account_id = self.sa_acct.pk
        )
        self.gh = GithubApi(self.sa_token)
        self.gh_account = self.gh.github_account(self.user)

    def test_github_api_init(self):
        assert self.gh.session.headers['Authorization'] == "token {t}".format(t=self.sa_token)

    def test_github_account(self):
        assert self.gh_account == self.sa_acct

    def test_github_account_not_found(self):
        gh = GithubApi(123456789)
        user = UserFactory.create()
        with self.assertRaisesMessage(GithubAccountNotFound, ''):
            gh.github_account(user)

    def test_github_token(self):
        assert self.gh.github_token(self.user) == self.sa_token.token

    def test_github_username(self):
        assert self.gh.github_username(self.user) == self.user.username

    def test_connect_as_user(self):
        gh = GithubApi.connect_as_user(self.user)
        assert isinstance(gh, GithubApi)

    @httpretty.activate
    def test_get_oauth_scopes(self):
        httpretty.register_uri(
            httpretty.GET,
            'https://api.github.com/user',
            adding_headers={"X-OAuth-Scopes": "repo, user"},
            body='hallo'
        )
        scopes = self.gh.oauth_scopes(test=True)
        assert scopes == ['repo', 'user']

    @httpretty.activate
    def test_create_repo(self):
        httpretty.register_uri(httpretty.POST, 'https://api.github.com/user/repos', body='hello', status=201)
        assert self.gh.create_repo(name='name', description='desc', homepage='page')

    @httpretty.activate
    def test_list_repos(self):
        resp_body = '[{},{},{}]'
        httpretty.register_uri(
            httpretty.GET,
            'https://api.github.com/users/karl/repos?per_page=3',
            body=resp_body,
            content_type="text/json",
            adding_headers={"Link": '<https://api.github.com/users/repos?page=2>; rel="next"'},
        )
        httpretty.register_uri(
            httpretty.GET,
            'https://api.github.com/users/repos?page=2',
            body=resp_body,
            content_type="text/json"
        )

        repos = self.gh.list_repos('karl')
        assert len(repos) == 6
        
    @httpretty.activate
    def test_list_user_repos(self):
        resp_body = '[{},{},{}]'
        httpretty.register_uri(
            httpretty.GET,
            'https://api.github.com/user/repos',
            body=resp_body,
            content_type="text/json",
            adding_headers={"Link": '<https://api.github.com/users/repos?page=2>; rel="next"'},
        )
        httpretty.register_uri(
            httpretty.GET,
            'https://api.github.com/users/repos?page=2',
            body=resp_body,
            content_type="text/json"
        )

        repos = self.gh.list_user_repos()
        assert len(repos) == 6

    @httpretty.activate
    def test_create_pr(self):
        httpretty.register_uri(
            httpretty.POST,
            'https://api.github.com/repos/joseph/pulls',
            body='{}',
            status=201
        )
        pr = self.gh.create_pull_request('joseph', 'pitty', 'barco', 'larentowicz')
        assert pr == {}

    @httpretty.activate
    def test_create_pr_error(self):
        httpretty.register_uri(
            httpretty.POST,
            'https://api.github.com/repos/joseph/pulls',
            body='{"message": "NO NO NO!"}',
            status=401
        )
        with self.assertRaisesMessage(GithubApiException, ''):
            self.gh.create_pull_request('joseph', 'pitty', 'barco', 'larentowicz')
