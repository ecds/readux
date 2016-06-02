'''Methods to export an annotated volume as a Jekyll website.'''

from datetime import datetime
from django.conf import settings
import logging
import os
import shutil
import subprocess
import tempfile
from urlparse import urlparse
from zipfile import ZipFile

import git
from git.cmd import Git
import yaml

import digitaledition_jekylltheme
from readux import __version__
from readux.books.github import GithubApi


logger = logging.getLogger(__name__)

# zip file of base jekyll site with digital edition templates
JEKYLL_THEME_ZIP = digitaledition_jekylltheme.ZIPFILE_PATH


class ExportException(Exception):
    pass


def get_jekyll_site_dir(base_dir, noid):
    '''Utility method to generate a jekyll site directory name (to
    ensure consistency between :meth:`website` and :meth:`website_gitrepo`).'''
    return os.path.join(base_dir, '%s_annotated_jekyll_site' % noid)


def website(vol, tei, page_one=None):
    '''Generate a jekyll website for a volume with annotations.
    Creates a jekyll site and imports pages and annotations from the TEI,
    and then returns the directory for further use (e.g., packaging as
    a zipfile for download, or for creating a new GitHub repository).

    :param vol: readux volume object (1.0 or 1.1)
    :param tei: annotated TEI facsimile (e.g.,
        :class:`~readux.books.tei.AnnotatedFacsimile`)
    :param page_one: page where numbering should start from 1 in the export
    :return: directory containing the generated jekyll site
    '''
    logger.debug('Generating jekyll website for %s', vol.pid)
    tmpdir = tempfile.mkdtemp(prefix='tmp-rdx-export')
    logger.debug('Building export for %s in %s', vol.pid, tmpdir)
    teifile = tempfile.NamedTemporaryFile(suffix='.xml', prefix='tei-',
        dir=tmpdir, delete=False)
    logger.debug('Saving TEI as %s', teifile.name)
    # write out tei to temporary file
    tei.serializeDocument(teifile)
    # IMPORTANT: close the filehandle to ensure *all* content is flushed
    # and available before running the ruby script
    teifile.close()
    # unzip jekyll template site
    logger.debug('Extracting jekyll template site')
    with ZipFile(JEKYLL_THEME_ZIP, 'r') as jekyllzip:
        jekyllzip.extractall(tmpdir)
    # run the script to import tei as jekyll site content
    jekyll_site_dir = os.path.join(tmpdir, 'digitaledition-jekylltheme')
    # jekyll_site_dir = os.path.join(tmpdir, 'digitaledition-jekylltheme-master')
    # run the jekyll import script in the jekyll site dir
    logger.debug('Running jekyll import TEI facsimile script')
    import_command = ['jekyllimport_teifacsimile', '-q', teifile.name]

    # if a page number is specified, pass it as a parameter to the script
    if page_one is not None:
        import_command.extend(['--page-one', unicode(page_one)])

    try:
        subprocess.check_call(import_command, cwd=jekyll_site_dir)
    except subprocess.CalledProcessError:
        raise ExportException('Error importing TEI facsimile to jekyll site')

    # NOTE: putting export content in a separate dir to make it easy to create
    # the zip file with the right contents and structure
    export_dir = os.path.join(tmpdir, 'export')
    os.mkdir(export_dir)

    # rename the jekyll dir and move it into the export dir
    shutil.move(jekyll_site_dir,
        os.path.join(export_dir, '%s_annotated_jekyll_site' % vol.noid))

    return export_dir


def website_zip(vol, tei, page_one=None):
    '''Package up a Jekyll site created by :meth:`website` as a zip file
    for easy download.

    :return: :class:`tempfile.NamedTemporaryFile` temporary zip file
    '''
    export_dir = website(vol, tei, page_one=page_one)

    # create a tempfile to hold a zip file of the site
    # (using tempfile for automatic cleanup after use)
    webzipfile = tempfile.NamedTemporaryFile(suffix='.zip',
        prefix='%s_annotated_site_' % vol.noid)
    shutil.make_archive(os.path.splitext(webzipfile.name)[0],  # name of the zipfile to create without .zip
         'zip',  # archive format; could also do tar
         export_dir
        )
    logger.debug('Jekyll site web export zipfile for %s is %s',
        vol.pid, webzipfile.name)
    # clean up temporary files
    shutil.rmtree(export_dir)
    # NOTE: method has to return the tempfile itself, or else it will get cleaned up when
    # the reference is destroyed
    return webzipfile


class GithubExportException(Exception):
    pass


def website_gitrepo(user, repo_name, vol, tei, page_one=None):
    '''Create a new GitHub repository and populate it with content from
    a newly generated jekyll website export created via :meth:`website`.

    :param user: user
    :param repo_name: name of the GitHub repository to be created;
        raises :class:`GithubExportException` if the repository already
        exists
    :param vol: :class:`~readux.books.models.Volume` to be exported
        (1.0 or 1.1)
    :param tei: annotated TEI facsimile (e.g.,
        :class:`~readux.books.tei.AnnotatedFacsimile`)
    :param page_one: page where numbering should start from 1 in the export
    :return: on success, returns a tuple of public repository url and
        github pages url for the newly created repo and site
    '''
    # connect to github as the user in order to create the repository
    github = GithubApi.connect_as_user(user)
    github_username = GithubApi.github_username(user)
    github_pages_url = 'http://%s.github.io/%s/' % (github_username, repo_name)

    # before even starting to generate the jekyll site,
    # check if requested repo name already exists; if so, bail out with an error
    current_repos = github.list_repos(github_username)
    current_repo_names = [repo['name'] for repo in current_repos]
    if repo_name in current_repo_names:
        raise GithubExportException('GitHub repo %s already exists.' % repo_name)

    export_dir = website(vol, tei, page_one=page_one)

    # jekyll dir is *inside* the export directory;
    # for the jekyll site to display correctly, we need to commit what
    # is in the directory, not the directory itself
    jekyll_dir = get_jekyll_site_dir(export_dir, vol.noid)

    # modify the jekyll config for relative url on github.io
    config_file_path = os.path.join(jekyll_dir, '_config.yml')
    with open(config_file_path, 'r') as configfile:
        config_data = yaml.load(configfile)
    config_data['url'] = github_pages_url
    config_data['baseurl'] = '/%s' % repo_name
    with open(config_file_path, 'w') as configfile:
        yaml.safe_dump(config_data, configfile,
            default_flow_style=False)
        # using safe_dump to generate only standard yaml output
        # NOTE: pyyaml requires default_flow_style=false to output
        # nested collections in block format

    logger.debug('Creating github repo %s for %s' % (repo_name, github_username))
    github.create_repo(repo_name,
        description='An annotated digital edition created with Readux',
        homepage=github_pages_url)
    # use oauth token to push to github
    # 'https://<token>@github.com/username/bar.git'
    # For more information, see
    # https://github.com/blog/1270-easier-builds-and-deployments-using-git-over-https-and-oauth
    repo_url = 'https://%s:x-oauth-basic@github.com/%s/%s.git' % \
        (GithubApi.github_token(user), github_username, repo_name)

    # add the jekyll site to github; based on these instructions:
    # https://help.github.com/articles/adding-an-existing-project-to-github-using-the-command-line/

    # initialize export dir as a git repo, and commit the contents
    # NOTE: to debug git commands, print the git return to see git output
    git = Git(jekyll_dir)
    # initialize jekyll site as a git repo
    git.init()
    # add and commit all contents
    git.add(['.'])
    git.commit(['-m', 'Import Jekyll site generated by Readux %s' % __version__,
        '--author="%s <%s>"' % (settings.GIT_AUTHOR_NAME, settings.GIT_AUTHOR_EMAIL)])
    # push local master to the gh-pages branch of the newly created repo,
    # using the user's oauth token credentials
    logger.debug('Pushing content to github')
    git.push([repo_url, 'master:gh-pages'])

    # clean up temporary files after push to github
    shutil.rmtree(export_dir)

    # generate public repo url for display to user
    public_repo_url = 'https://github.com/%s/%s' % (github_username, repo_name)
    return (public_repo_url, github_pages_url)


def update_gitrepo(user, repo_url, vol, tei, page_one=None):
    '''Update an existing GitHub repository previously created by
    Readux export.  Checks out the repository, creates a new branch,
    runs the tei to jekyll import on that branch, pushes it to github,
    and creates a pull request.  Returns the HTML url for the new
    pull request on success.'''

    # NOTE: some overlap in functionality with website export and
    # website_gitrepo methods, but not obvious how to share the functionality

    # connect to github as the user in order to access the repository
    github = GithubApi.connect_as_user(user)

    # parse github url to add oauth token for access (as in website_gitrepo)
    parsed_repo_url = urlparse(repo_url)
    auth_repo_url = '%s://%s:x-oauth-basic@%s%s.git' % \
        (parsed_repo_url.scheme, GithubApi.github_token(user),
         parsed_repo_url.netloc, parsed_repo_url.path)

    # create a tmpdir to clone the git repo into
    tmpdir = tempfile.mkdtemp(prefix='tmp-rdx-export-update')
    logger.debug('Cloning %s to %s', repo_url, tmpdir)
    repo = git.Repo.clone_from(auth_repo_url, tmpdir, branch='gh-pages')
    # create and switch to a new branch and switch to it; using datetime
    # for uniqueness
    git_branch_name = 'readux-update-%s' % \
        datetime.now().strftime('%Y%m%d-%H%M%S')
    update_branch = repo.create_head(git_branch_name)
    update_branch.checkout()

    logger.debug('Updating export for %s in %s', vol.pid, tmpdir)
    teifile = tempfile.NamedTemporaryFile(suffix='.xml', prefix='tei-',
                                          dir=tmpdir, delete=False)
    logger.debug('Saving TEI as %s', teifile.name)

    # write out tei to temporary file for use with import script
    tei.serializeDocument(teifile)
    # IMPORTANT: close the filehandle to ensure *all* content is flushed
    # and available before running the ruby script
    teifile.close()

    # run the script to get a freash import of tei as jekyll site content
    logger.debug('Running jekyll import TEI facsimile script')
    import_command = ['jekyllimport_teifacsimile', '-q', teifile.name]
    # if a page number is specified, pass it as a parameter to the script
    if page_one is not None:
        import_command.extend(['--page-one', unicode(page_one)])
    try:
        subprocess.check_call(import_command, cwd=tmpdir)
    except subprocess.CalledProcessError:
        raise ExportException('Error running jekyll import on TEI facsimile')

    # add any files that could be updated to the git index
    repo.index.add(['_config.yml', '_volume_pages/*', '_annotations/*',
                    'tei.xml', '_data/tags.yml', 'tags/*'])
    git_author = git.Actor(settings.GIT_AUTHOR_NAME,
                           settings.GIT_AUTHOR_EMAIL)
    # commit all changes
    repo.index.commit('Updated Jekyll site by Readux %s' % __version__,
                      author=git_author)

    # push the update to a new branch on github
    repo.remotes.origin.push('%(branch)s:%(branch)s' %
                             {'branch': git_branch_name})
    # convert repo url to form needed to generate pull request
    repo = repo_url.replace('https://github.com/', '')
    pullrequest = github.create_pull_request(
        repo, 'Updated export', git_branch_name, 'gh-pages')

    # clean up local checkout after successful push
    shutil.rmtree(tmpdir)

    # return the html url for the new pull request
    return pullrequest['html_url']
