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
import requests
from piffle.iiif import IIIFImageClient

import digitaledition_jekylltheme
from readux import __version__
from readux.books.github import GithubApi


logger = logging.getLogger(__name__)

# zip file of base jekyll site with digital edition templates
JEKYLL_THEME_ZIP = digitaledition_jekylltheme.ZIPFILE_PATH


class ExportException(Exception):
    pass


class GithubExportException(Exception):
    pass


class VolumeExport(object):
    '''Generate a jekyll website for a volume with annotations.
    Creates a jekyll site and imports pages and annotations from the TEI.
    Can create a zipfile of the directory, push the jekyll site to GitHub
    for use with GitHub Pages, or create a pull request for an existing
    site previously created via Readux export.

    :param vol: readux volume object (1.0 or 1.1)
    :param tei: annotated TEI facsimile (e.g.,
        :class:`~readux.books.tei.AnnotatedFacsimile`)
    :param page_one: page where numbering should start from 1 in the export,
        if custom numbering is desired
    :param update_callback: optional callback for receiving status updates
    :param include_images: if set, page images will be downloaded and
        included in the export
    '''

    def __init__(self, volume, tei, page_one=None, update_callback=None,
                 include_images=False):
        self.volume = volume
        self.tei = tei
        self.page_one = page_one
        self.update_callback = update_callback
        self.include_images = include_images

        # initialize github connection values to None
        self.github = None
        self.github_username = None
        self.github_token = None

    def get_jekyll_site_dir(self, base_dir):
        '''Utility method to generate a jekyll site directory name for the
        volume being exported.'''
        return os.path.join(base_dir,
                            '%s_annotated_jekyll_site' % self.volume.noid)

    def log_status(self, msg):
        logger.debug(msg)
        if self.update_callback is not None:
            self.update_callback(msg)

    def save_tei_file(self, tmpdir):
        teifile = tempfile.NamedTemporaryFile(suffix='.xml', prefix='tei-',
                                              dir=tmpdir, delete=False)
        logger.debug('Saving TEI as %s', teifile.name)
        # write out tei to temporary file
        self.tei.serializeDocument(teifile)
        # IMPORTANT: close the filehandle to ensure *all* content is flushed
        # and available before running the ruby script
        teifile.close()
        return teifile

    def import_tei_jekyll(self, teifile, tmpdir):
        # run the script to get a freash import of tei as jekyll site content
        self.log_status('Running jekyll import TEI facsimile script')
        jekyllimport_tei_script = settings.JEKYLLIMPORT_TEI_SCRIPT
        import_command = [jekyllimport_tei_script, '-q', teifile.name]
        # if a page number is specified, pass it as a parameter to the script
        if self.page_one is not None:
            import_command.extend(['--page-one', unicode(self.page_one)])
        try:
            subprocess.check_call(import_command, cwd=tmpdir)
        except subprocess.CalledProcessError:
            err_msg = 'Error running jekyll import on TEI facsimile'
            if self.update_callback is not None:
                self.update_callback(err_msg, 'error')
            raise ExportException(err_msg)

    def generate_website(self):
        """Generate a jekyll website for a volume with annotations.
        Creates a jekyll site and imports pages and annotations from the TEI,
        and then returns the directory for further use (e.g., packaging as
        a zipfile for download, or for creating a new GitHub repository).
        """
        logger.debug('Generating jekyll website for %s', self.volume.pid)
        tmpdir = tempfile.mkdtemp(prefix='tmp-rdx-export')
        logger.debug('Building export for %s in %s', self.volume.pid, tmpdir)

        # unzip jekyll template site
        self.log_status('Extracting jekyll template site')
        with ZipFile(JEKYLL_THEME_ZIP, 'r') as jekyllzip:
            jekyllzip.extractall(tmpdir)
        jekyll_site_dir = os.path.join(tmpdir, 'digitaledition-jekylltheme')

        # save image files if requested, and update image paths in tei
        # to use local references
        if self.include_images:
            self.save_page_images(jekyll_site_dir)

        teifile = self.save_tei_file(tmpdir)

        # run the script to import tei as jekyll site content
        self.import_tei_jekyll(teifile, jekyll_site_dir)

        # NOTE: putting export content in a separate dir to make it easy to create
        # the zip file with the right contents and structure
        export_dir = os.path.join(tmpdir, 'export')
        os.mkdir(export_dir)

        # rename the jekyll dir and move it into the export dir
        shutil.move(jekyll_site_dir,
                    os.path.join(export_dir, '%s_annotated_jekyll_site' %
                                 self.volume.noid))

        return export_dir

    def save_page_images(self, jekyll_site_dir):
        self.log_status('Downloading page images')
        for teipage in self.tei.page_list:
            for graphic in teipage.graphics:
                # NOTE: could potentially use a channel consumer so
                # that image downloads could happen in parallel, but would
                # require additional error handling

                # graphic url attribute is full, resolvable IIIF url
                imgurl = graphic.url
                # parse image url as IIIF
                iiif_img = IIIFImageClient.init_from_url(imgurl)
                # convert api endpoint to local path
                iiif_img.api_endpoint = 'images'
                # simplify image id: strip out iiif id prefix and pidspace
                # prefix, if possible
                iiif_img.image_id = iiif_img.image_id \
                    .replace(settings.IIIF_ID_PREFIX, '') \
                    .replace('%s:' % settings.FEDORA_PIDSPACE, '')
                # serialize updated iiif image url for use as local image path
                image_path = unicode(iiif_img)

                # update path in the TEI to use local reference
                # in the jekyll site
                graphic.url = image_path

                imgdir = os.path.dirname(image_path)
                # create all needed directories for path
                try:
                    os.makedirs(os.path.join(jekyll_site_dir, imgdir))
                except OSError:
                    # depending on order images are encountered,
                    # could get an error for a directory already existing,
                    # but it's not a real issue
                    pass
                logger.debug('Downloading page image %s', imgurl)
                # NOTE: json info file as downloaded references the configured
                # IIIF image server; this is OK for now, as it allows us
                # to serve deep zoom tiles from the image server
                # Will need to be updated once including deep zoom is
                # an export option.
                save_url_to_file(imgurl,
                                 os.path.join(jekyll_site_dir, image_path))

    def website_zip(self):
        '''Package up a Jekyll site created by :meth:`website` as a zip file
        for easy download.

        :return: :class:`tempfile.NamedTemporaryFile` temporary zip file
        '''
        export_dir = self.generate_website()

        # create a tempfile to hold a zip file of the site
        # (using tempfile for automatic cleanup after use)
        webzipfile = tempfile.NamedTemporaryFile(
            suffix='.zip',
            delete=False, # temporary, testing
            prefix='%s_annotated_site_' % self.volume.noid)
        shutil.make_archive(
            # name of the zipfile to create without .zip
            os.path.splitext(webzipfile.name)[0],
            'zip',  # archive format; could also do tar
            export_dir
        )
        logger.debug('Jekyll site web export zipfile for %s is %s',
                     self.volume.pid, webzipfile.name)
        # clean up temporary files
        shutil.rmtree(export_dir)
        # NOTE: method has to return the tempfile itself, or else it will
        # get cleaned up when the reference is destroyed
        return webzipfile

    def use_github(self, user):
        # connect to github as the user in order to create the repository
        self.github = GithubApi.connect_as_user(user)
        self.github_username = GithubApi.github_username(user)
        self.github_token = GithubApi.github_token(user)

    def github_auth_repo(self, repo_name=None, repo_url=None):
        """Generate a GitHub repo url with an oauth token in order to
        push to GitHub on the user's behalf.  Takes either a repository
        name or repository url.
        """
        if repo_name:
            git_repo_url = 'github.com/%s/%s.git' % (self.github_username, repo_name)
            github_scheme = 'https'
        elif repo_url:
            # parse github url to add oauth token for access
            parsed_repo_url = urlparse(repo_url)
            git_repo_url = '%s%s.git' % (parsed_repo_url.netloc, parsed_repo_url.path)
            # probably https, but may as well pull from parsed url
            github_scheme = parsed_repo_url.scheme

        # use oauth token to push to github
        # 'https://<token>@github.com/username/bar.git'
        # For more information, see
        # https://github.com/blog/1270-easier-builds-and-deployments-using-git-over-https-and-oauth
        return '%s://%s:x-oauth-basic@%s' % (github_scheme, self.github_token,
                                             git_repo_url)

    def website_gitrepo(self, user, repo_name):
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
        self.use_github(user)
        # NOTE: github pages sites now default to https
        github_pages_url = 'https://%s.github.io/%s/' % \
            (self.github_username, repo_name)

        # before even starting to generate the jekyll site,
        # check if requested repo name already exists; if so, bail out with an error
        current_repos = self.github.list_repos(self.github_username)
        current_repo_names = [repo['name'] for repo in current_repos]
        if repo_name in current_repo_names:
            raise GithubExportException('GitHub repo %s already exists.' \
                                        % repo_name)

        export_dir = self.generate_website()

        # jekyll dir is *inside* the export directory;
        # for the jekyll site to display correctly, we need to commit what
        # is in the directory, not the directory itself
        jekyll_dir = self.get_jekyll_site_dir(export_dir)

        # modify the jekyll config for relative url on github.io
        config_file_path = os.path.join(jekyll_dir, '_config.yml')
        with open(config_file_path, 'r') as configfile:
            config_data = yaml.load(configfile)

        # split out github pages url into the site url and path
        parsed_gh_url = urlparse(github_pages_url)
        config_data['url'] = '%s://%s' % (parsed_gh_url.scheme,
                                          parsed_gh_url.netloc)
        config_data['baseurl'] = parsed_gh_url.path.rstrip('/')
        with open(config_file_path, 'w') as configfile:
            yaml.safe_dump(config_data, configfile,
                           default_flow_style=False)
            # using safe_dump to generate only standard yaml output
            # NOTE: pyyaml requires default_flow_style=false to output
            # nested collections in block format

        logger.debug('Creating github repo %s for %s', repo_name,
                     self.github_username)
        if self.update_callback is not None:
            self.update_callback('Creating GitHub repo %s' % repo_name)
        self.github.create_repo(
            repo_name, homepage=github_pages_url,
            description='An annotated digital edition created with Readux')

        # get auth repo url to use to push data
        repo_url = self.github_auth_repo(repo_name=repo_name)

        # add the jekyll site to github; based on these instructions:
        # https://help.github.com/articles/adding-an-existing-project-to-github-using-the-command-line/

        # initialize export dir as a git repo, and commit the contents
        # NOTE: to debug git commands, print the git return to see git output
        gitcmd = Git(jekyll_dir)
        # initialize jekyll site as a git repo
        gitcmd.init()
        # add and commit all contents
        gitcmd.add(['.'])
        gitcmd.commit(
            ['-m', 'Import Jekyll site generated by Readux %s' % __version__,
             '--author="%s <%s>"' % (settings.GIT_AUTHOR_NAME,
                                     settings.GIT_AUTHOR_EMAIL)])
        # push local master to the gh-pages branch of the newly created repo,
        # using the user's oauth token credentials
        self.log_status('Pushing content to GitHub')
        gitcmd.push([repo_url, 'master:gh-pages'])

        # clean up temporary files after push to github
        shutil.rmtree(export_dir)

        # generate public repo url for display to user
        public_repo_url = 'https://github.com/%s/%s' % (self.github_username,
                                                        repo_name)
        return (public_repo_url, github_pages_url)

    def update_gitrepo(self, user, repo_url):
        '''Update an existing GitHub repository previously created by
        Readux export.  Checks out the repository, creates a new branch,
        runs the tei to jekyll import on that branch, pushes it to github,
        and creates a pull request.  Returns the HTML url for the new
        pull request on success.'''

        # connect to github as the user in order to access the repository
        self.use_github(user)
        # get auth repo url to use to create branch
        auth_repo_url = self.github_auth_repo(repo_url=repo_url)

        # create a tmpdir to clone the git repo into
        tmpdir = tempfile.mkdtemp(prefix='tmp-rdx-export-update')
        logger.debug('Cloning %s to %s', repo_url, tmpdir)
        if self.update_callback is not None:
            self.update_callback('Cloning %s' % repo_url)
        repo = git.Repo.clone_from(auth_repo_url, tmpdir, branch='gh-pages')
        # create and switch to a new branch and switch to it; using datetime
        # for uniqueness
        git_branch_name = 'readux-update-%s' % \
            datetime.now().strftime('%Y%m%d-%H%M%S')
        update_branch = repo.create_head(git_branch_name)
        update_branch.checkout()

        logger.debug('Updating export for %s in %s', self.volume.pid, tmpdir)

        # remove all annotations and tag pages so that if an annotation is removed
        # or a tag is no longer used in readux, it will be removed in the export
        # (annotations and tags that are unchanged will be restored by the tei
        # jekyll import, and look unchanged to git if no different)
        try:
            repo.index.remove(['_annotations/*', 'tags/*'])
        except git.GitCommandError:
            # it's possible that an export has no annotations or tags
            # (although unlikely to occur anywhere but development & testing)
            # if there's an error on removal, ignore it
            pass

        # save image files if requested, and update image paths in tei
        # to use local references
        if self.include_images:
            self.save_page_images(tmpdir)

        teifile = self.save_tei_file(tmpdir)

        # run the script to get a fresh import of tei as jekyll site content
        self.import_tei_jekyll(teifile, tmpdir)

        # add any files that could be updated to the git index
        repo.index.add(['_config.yml', '_volume_pages/*', '_annotations/*',
                        'tei.xml', '_data/tags.yml', 'tags/*', 'images/*'])
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
        if self.update_callback is not None:
            self.update_callback('Creating pull request with updates')
        pullrequest = self.github.create_pull_request(
            repo, 'Updated export', git_branch_name, 'gh-pages')

        # clean up local checkout after successful push
        shutil.rmtree(tmpdir)

        # return the html url for the new pull request
        return pullrequest['html_url']


def save_url_to_file(url, filepath):
    resp = requests.get(url, stream=True)
    if resp.status_code == requests.codes.ok:
        with open(filepath, 'wb') as fd:
            for chunk in resp.iter_content(1000):
                fd.write(chunk)
    else:
        logger.warning('Status code %s on %s', resp.status_code, url)
