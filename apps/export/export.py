"""Github export module"""
import httpretty
import io
import json
import logging
import os
import re
import shutil
import subprocess
import tempfile
import zipfile
from datetime import datetime
from time import sleep
from urllib.parse import urlparse
from requests import get
# pylint: disable = unused-import, ungrouped-imports
try:
    from yaml import CLoader as Loader, CDumper as Dumper
except ImportError: # pragma: no cover
    from yaml import Loader, Dumper
# pylint: enable = unused-import, ungrouped-imports
# TODO: Can we be more efficient in how we import git?
import git
from git.cmd import Git
from yaml import load, safe_dump
from django.core.mail import send_mail
from django.core.serializers import serialize
from django.template.loader import get_template
from apps.users.models import User
from apps.readux import __version__
import digitaledition_jekylltheme
import config.settings.local as settings
from .github import GithubApi, GithubAccountNotFound


LOGGER = logging.getLogger(__name__)

# zip file of base jekyll site with digital edition templates
JEKYLL_THEME_ZIP = digitaledition_jekylltheme.ZIPFILE_PATH

class ExportException(Exception):
    """Custom exception"""
    pass

class IiifManifestExport:
    """Manifest Export

    :return: Return bytes containing the entire contents of the buffer.
    :rtype: bytes
    """
    @classmethod
    def get_zip(self, manifest, version, owners=[]):
        """Generate zipfile of manifest.

        :param manifest: Manifest to be exported.
        :type manifest: apps.iiif.manifests.models.Manifest
        :param version: IIIF API version to use.
        :type version: str
        :param owners: List of annotation owners, defaults to []
        :type owners: list, optional
        :return: Return bytes containing the entire contents of the buffer.
        :rtype: bytes
        """
        # zip_subdir = manifest.label
        # zip_filename = "iiif_export.zip"

        # Open BytesIO to grab in-memory ZIP contents
        byte_stream = io.BytesIO()

        # The zip compressor
        zip_file = zipfile.ZipFile(byte_stream, "w")

        # First write basic human-readable metadata
        # Annotated edition from {grab site identity/version of Readux} at {grab site URL}
        # volume title
        # volume author
        # volume date
        # volume publisher
        # number of pages
        # annotator username
        # time of export

        # pylint: disable = possibly-unused-variable
        title = manifest.label
        author = manifest.author
        date = manifest.published_date
        publisher = manifest.publisher
        page_count = manifest.canvas_set.count()
        now = datetime.utcnow()
        readux_url = settings.HOSTNAME
        annotators = User.objects.filter(
            userannotation__canvas__manifest__id=manifest.id
        ).distinct()
        annotators_string = ', '.join([i.name for i in annotators])
        # pylint: enable = possibly-unused-variable

        # pylint: disable = line-too-long

        # get the owner_id for each/all annotations
        # dedup the list of owners (although -- how to order?  alphabetical or
        # sby contribution count or ignore order)  .distinct()
        # turn the list of owners into a comma separated string of formal names instead of user ids
        readme = "Annotation export from Readux %(version)s at %(readux_url)s\nedition type: Readux IIIF Exported Edition\nexport date: %(now)s UTC\n\n" % locals()
        volume_data = "volume title: %(title)s\nvolume author: %(author)s\nvolume date: %(date)s\nvolume publisher: %(publisher)s\npages: %(page_count)s \n" % locals()
        annotators_attribution_string = "Annotated by: " + annotators_string +"\n\n"
        boilerplate = "Readux is a platform developed by Emory University’s Center for Digital Scholarship for browsing, annotating, and publishing with digitized books. This zip file includes an International Image Interoperability Framework (IIIF) manifest for the digitized book and an annotation list for each page that includes both the encoded text of the book and annotations created by the user who created this export. This bundle can be used to archive the recognized text and annotations for preservation and future access.\n\n"
        explanation = "Each canvas (\"sc:Canvas\") in the manifest represents a page of the work. Each canvas includes an \"otherContent\" field-set with information identifying that page's annotation lists. This field-set includes an \"@id\" field and the label field (\"@type\") \"sc:AnnotationList\" for each annotation list. The \"@id\" field contains the URL link at which the annotation list was created and originally hosted from the Readux site. In order to host this IIIF manifest and its annotation lists again to browse the book and annotations outside of Readux, these @id fields would need to be updated to the appropriate URLs for the annotation lists on the new host. Exported annotation lists replace nonword characters (where words are made up of alphanumerics and underscores) with underscores in the filename."
        readme = readme + volume_data + annotators_attribution_string + boilerplate + explanation
        zip_file.writestr('README.txt', readme)
        current_user = User.objects.get(id__in=owners)

        # pylint: enable = line-too-long

        # Next write the manifest
        zip_file.writestr(
            'manifest.json',
            json.dumps(
                json.loads(
                    serialize(
                        'manifest',
                        [manifest],
                        version=version,
                        annotators=current_user.name,
                        exportdate=now,
                        current_user=current_user
                    )
                ),
                indent=4
            )
        )

        # Then write the OCR annotations
        for canvas in manifest.canvas_set.all():
            if canvas.annotation_set.count() > 0:
                json_hash = json.loads(
                    serialize(
                        'annotation_list',
                        [canvas],
                        version=version,
                        owners=owners
                    )
                )
                anno_uri = json_hash['@id']

                annotation_file = re.sub(r'\W','_', anno_uri) + ".json"

                zip_file.writestr(
                    annotation_file,
                    json.dumps(
                        json_hash,
                        indent=4
                    )
                )
        # Then write the user annotations
        for canvas in manifest.canvas_set.all():
            user_annotations = current_user.userannotation_set.filter(canvas=canvas)

            if user_annotations.count() > 0:
                # annotations = canvas.userannotation_set.filter(owner__in=owners).all()
                json_hash = json.loads(
                    serialize(
                        'user_annotation_list',
                        [canvas],
                        version=version,
                        is_list=False,
                        owners=[current_user]
                    )
                )
                anno_uri = json_hash['@id']
                annotation_file = re.sub(r'\W', '_', anno_uri) + ".json"

                zip_file.writestr(
                    annotation_file,
                    json.dumps(
                        json_hash,
                        indent=4
                    )
                )

        zip_file.close() # flush zipfile to byte stream

        return byte_stream.getvalue()


class GithubExportException(Exception):
    """Custom exception."""
    pass

class JekyllSiteExport(object):
    """Export Jekyllsite

    :param object: [description]
    :type object: [type]
    :raises ExportException: [description]
    :raises GithubExportException: [description]
    :return: [description]
    :rtype: [type]
    """
    def __init__(self, manifest, version, page_one=None,
                 include_images=False, deep_zoom='hosted',
                 github_repo=None, owners=None, user=None):
        """Init JekyllSiteExport

        :param manifest: Manifest to be exported
        :type manifest: apps.iiif.manifests.models.Manifest
        :param version: IIIF API version eg 'v2'
        :type version: str
        :param page_one: First page for export, defaults to None
        :type page_one: apps.iiif.canvases.models.Canvas, optional
        :param include_images: Wether or not to include image files in export, defaults to False
        :type include_images: bool, optional
        :param deep_zoom: Where to look for DeepZoom, defaults to 'hosted'
        :type deep_zoom: str, optional
        :param github_repo: Name of GitHub repo for export, defaults to None
        :type github_repo: str, optional
        :param owners: List of annotation owners, defaults to None
        :type owners: list, optional
        :param user: Person doing the export. defaults to None
        :type user: apps.users.models.User, optional
        """
        # self.volume = volume
        self.manifest = manifest
        self.version = version
        # self.page_one = page_one
        # self.include_images = include_images
        #self.deep_zoom = deep_zoom
        self.include_deep_zoom = (deep_zoom == 'include')
        self.no_deep_zoom = (deep_zoom == 'exclude')
        # self.github_repo = github_repo

        # # initialize github connection values to None
        self.github = None
        self.github_username = None
        self.github_token = None
        self.jekyll_site_dir = None
        self.owners = owners
        self.user = user
        self.github_repo = github_repo
        # TODO: Why?
        self.is_testing = False


    def log_status(self, msg):
        """Shortcut function to log status of export.

        :param msg: Message to log.
        :type msg: str
        """
        LOGGER.info(msg)

    # TODO: is this ever called?
    # Why not just call `log_status` directly?
    def notify_msg(self, msg):
        """Log the notification.

        :param msg: Notification message
        :type msg: str
        """
        self.log_status(msg)

    # TODO: is this needed?
    # Why not just call `website_zip` directly?
    def get_zip(self):
        """Get the zip file of the export.

        :return: Exported site in zip file
        :rtype: bytes
        """
        return self.website_zip()

    def get_zip_path(filename):
        """Convenience function to get the path for the export zip file."""
        return os.path.join(tempfile.gettempdir(), filename)

    def get_zip_file(self, filename):
        """Generate zip file"""
        file = open(JekyllSiteExport.get_zip_path(filename),"rb")
        data = file.read()
        file.close()
        return data

    def iiif_dir(self):
        """Convenience function to produce the system path for export file.

        :return: System path for export file.
        :rtype: str
        """
        return os.path.join(self.jekyll_site_dir, 'iiif_export')

    def import_iiif_jekyll(self, manifest, tmpdir):
        """Get a fresh import of IIIF as jekyll site content

        :param manifest: Manifest to be exported.
        :type manifest: apps.iiif.manifests.models.Manifest
        :param tmpdir: System path for tmp directory.
        :type tmpdir: str
        :raises ExportException: [description]
        """
        # run the script to get a fresh import of IIIF as jekyll site content
        self.log_status('Running jekyll import IIIF manifest script')
        jekyllimport_manifest_script = settings.JEKYLLIMPORT_MANIFEST_SCRIPT
        import_command = [
            jekyllimport_manifest_script,
            '--local-directory',
            '-q',
            self.iiif_dir(),
            tmpdir
        ]
        # TODO
        # # if a page number is specified, pass it as a parameter to the script
        # if self.page_one is not None:
        #     import_command.extend(['--page-one', unicode(self.page_one)])
        # # if no deep zoom is requested, pass through so the jekyll
        # #  config can be updated appropriately
        if self.no_deep_zoom:
            import_command.append('--no-deep-zoom')

        try:
            LOGGER.debug('Jekyll import command: %s', ' '.join(import_command))
            output = subprocess.check_output(
                ' '.join(import_command),
                shell=True,
                stderr=subprocess.STDOUT
            )
            LOGGER.debug('Jekyll import output:')
            LOGGER.debug(output.decode('utf-8'))
        except subprocess.CalledProcessError as error:
            LOGGER.debug('Jekyll import error:')
            LOGGER.debug(error.output)
            err_msg = "Error running jekyll import on IIIF manifest!\n{cmd}\n{err}".format(
                cmd=' '.join(import_command),
                err=error.output.decode('utf-8')
            )
            LOGGER.error(err_msg)
            raise ExportException(err_msg)

    def generate_website(self):
        """Generate a jekyll website for a volume with annotations.
        Creates a jekyll site and imports pages and annotations from the IIIF,
        and then returns the directory for further use (e.g., packaging as
        a zipfile for download, or for creating a new GitHub repository).

        :return: System path for export directory.
        :rtype: str
        """
        LOGGER.debug('Generating jekyll website for %s', self.manifest.id)
        tmpdir = tempfile.mkdtemp(prefix='tmp-rdx-export')
        LOGGER.debug('Building export for %s in %s', self.manifest.id, tmpdir)

        # unzip jekyll template site
        self.log_status('Extracting jekyll template site')
        with zipfile.ZipFile(JEKYLL_THEME_ZIP, 'r') as jekyllzip:
            jekyllzip.extractall(tmpdir)
        self.jekyll_site_dir = os.path.join(tmpdir, 'digitaledition-jekylltheme')
        LOGGER.debug('Jekyll site dir:')
        LOGGER.debug(self.jekyll_site_dir)

        LOGGER.debug('Exporting IIIF bundle')
        iiif_zip_stream = IiifManifestExport.get_zip(self.manifest, 'v2', owners=self.owners)
        iiif_zip = zipfile.ZipFile(io.BytesIO(iiif_zip_stream), "r")

        iiif_zip.extractall(self.iiif_dir())

        # TODO
        # # save image files if requested, and update image paths
        # # to use local references
        # if self.include_images:
        #     self.save_page_images(jekyll_site_dir)
        # if self.include_deep_zoom:
        #     self.generate_deep_zoom(jekyll_site_dir)


        # run the script to import IIIF as jekyll site content
        self.import_iiif_jekyll(self.manifest, self.jekyll_site_dir)

        # NOTE: putting export content in a separate dir to make it easy to create
        # the zip file with the right contents and structure
        export_dir = os.path.join(tmpdir, 'export')
        os.mkdir(export_dir)

        # rename the jekyll dir and move it into the export dir
        shutil.move(self.jekyll_site_dir,
                    self.edition_dir(export_dir))

        return export_dir


    def edition_dir(self, export_dir):
        """Convenience function for system path to the edition directory

        :param export_dir: System path for export directory.
        :type export_dir: str
        :return: System path for edition directory
        :rtype: str
        """
        return os.path.join(
            export_dir,
            '{m}_annotated_jekyll_site'.format(m=self.manifest.id)
        )

    def website_zip(self):
        """Package up a Jekyll site created by :meth:`website` as a zip file
        for easy download.

        :return: Temporary zip file.
        :rtype: tempfile.NamedTemporaryFile
        """
        export_dir = self.generate_website()

        # create a tempfile to hold a zip file of the site
        # (using tempfile for automatic cleanup after use)
        webzipfile = tempfile.NamedTemporaryFile(
            suffix='.zip',
            prefix='%s_annotated_site_' % self.manifest.id,
            delete=False)
        shutil.make_archive(
            # name of the zipfile to create without .zip
            os.path.splitext(webzipfile.name)[0],
            'zip',  # archive format; could also do tar
            export_dir
        )
        LOGGER.debug('Jekyll site web export zipfile for %s is %s',
                     self.manifest.id, webzipfile.name)
        # clean up temporary files
        shutil.rmtree(export_dir)
        # NOTE: method has to return the tempfile itself, or else it will
        # get cleaned up when the reference is destroyed
        return webzipfile

    def use_github(self, user):
        """Set variables for GitHub export.

        :param user: Person exporting
        :type user: apps.users.models.User
        """
        # connect to github as the user in order to create the repository
        self.github = GithubApi.connect_as_user(user)
        self.github_username = GithubApi.github_username(user)
        self.github_token = GithubApi.github_token(user)
        self.github.session.headers['Authorization'] = f'token {self.github_token}'

    def github_auth_repo(self, repo_name=None, repo_url=None):
        """Generate a GitHub repo url with an oauth token in order to
        push to GitHub on the user's behalf.  Takes either a repository
        name or repository url. The expected result should be formatted
        as follows:

        https://<github username>:<github token>@github.com/<github username>/<github repo>.git

        :return: GitHub authentication header.
        :rtype: str
        """
        if repo_url:
            parsed_repo_url = urlparse(repo_url)
            return f'https://{self.github_username}:{GithubApi.github_token(self.user)}@github.com/{parsed_repo_url.path[1:]}.git'

        return f'https://{self.github_username}:{GithubApi.github_token(self.user)}@github.com/{self.github_username}/{repo_name}.git'

    def gitrepo_exists(self):
        """Check to see if GitHub repo already exists.

        :return: True if repo exists. False if it does not.
        :rtype: bool
        """
        current_repos = self.github.list_repos(self.github_username)
        current_repo_names = [repo['name'] for repo in current_repos]
        LOGGER.debug(
            'Checking to see if {gr} in {rns}'.format(
                gr=self.github_repo,
                rns=" ".join(current_repo_names)
            )
        )
        return self.github_repo in current_repo_names



    def website_gitrepo(self):
        """Create a new GitHub repository and populate it with content from
        a newly generated jekyll website export created via :meth:`website`.

        :return: On success, returns a tuple of public repository URL and
            GitHub Pages URL for the newly created repo and site
        :rtype: tuple
        """

        # NOTE: github pages sites now default to https
        github_pages_url = 'https://{un}.github.io/{gr}/'.format(
            un=self.github_username,
            gr=self.github_repo
        )

        # before even starting to generate the jekyll site,
        # check if requested repo name already exists; if so, bail out with an error
        LOGGER.debug(
            'Checking github repo {gr} for {un}'.format(
                gr=self.github_repo,
                un=self.github_username
            )
        )

        if self.gitrepo_exists():
            raise GithubExportException(
                'GitHub repo {gr} already exists.'.format(
                    gr=self.github_repo
                )
            )

        export_dir = self.generate_website()

        # jekyll dir is *inside* the export directory;
        # for the jekyll site to display correctly, we need to commit what
        # is in the directory, not the directory itself
        jekyll_dir = self.edition_dir(export_dir)

        # modify the jekyll config for relative url on github.io
        config_file_path = os.path.join(jekyll_dir, '_config.yml')
        with open(config_file_path, 'r') as configfile:
            config_data = load(configfile, Loader=Loader)

        # split out github pages url into the site url and path
        parsed_gh_url = urlparse(github_pages_url)
        config_data['url'] = '{s}://{n}'.format(
            s=parsed_gh_url.scheme,
            n=parsed_gh_url.netloc
        )
        config_data['baseurl'] = parsed_gh_url.path.rstrip('/')
        with open(config_file_path, 'w') as configfile:
            safe_dump(config_data, configfile,
                           default_flow_style=False)
            # using safe_dump to generate only standard yaml output
            # NOTE: pyyaml requires default_flow_style=false to output
            # nested collections in block format

        LOGGER.debug(
            'Creating github repo {gr} for {un}'.format(
                gr=self.github_repo,
                un=self.github_username
            )
        )

        self.github.create_repo(
            self.github_repo, homepage=github_pages_url, user=self.user,
            description='An annotated digital edition created with Readux'
        )

        # get auth repo url to use to push data
        repo_url = self.github_auth_repo(repo_name=self.github_repo)

        # add the jekyll site to github; based on these instructions:
        # https://help.github.com/articles/adding-an-existing-project-to-github-using-the-command-line/

        # initialize export dir as a git repo, and commit the contents
        # NOTE: to debug git commands, print the git return to see git output

        git_author = None

        if self.user.name is None or not self.user.name:
            git_author = GithubApi.github_username(self.user)
        else:
            git_author = self.user.name

        gitcmd = Git(jekyll_dir)
        # initialize jekyll site as a git repo
        gitcmd.init()
        # add and commit all contents
        gitcmd.config("user.email", self.user.email)
        gitcmd.config("user.name", git_author)
        # Use the token to authenticate the Git commands.
        # Required to do this as of June 9, 2020
        # https://developer.github.com/changes/2020-02-14-deprecating-oauth-app-endpoint/
        gitcmd.config("user.password", GithubApi.github_token(self.user))

        gitcmd.add(['.'])
        gitcmd.commit([
            '-m',
            'Import Jekyll site generated by Readux {v}'.format(
                v=__version__
            ),
            '--author="{fn} <{ue}>"'.format(
                fn=git_author,
                ue=self.user.email
            )
        ])
        # push local master to the gh-pages branch of the newly created repo,
        # using the user's oauth token credentials
        self.log_status('Pushing new content to GitHub')
        if os.environ['DJANGO_ENV'] != 'test': # pragma: no cover
            gitcmd.push([repo_url, 'master:gh-pages']) # pragma: no cover

        # clean up temporary files after push to github
        shutil.rmtree(export_dir)

        # generate public repo url for display to user
        public_repo_url = 'https://github.com/{un}/{gr}'.format(
            un=self.github_username,
            gr=self.github_repo
        )
        return (public_repo_url, github_pages_url)

    def update_gitrepo(self):
        '''Update an existing GitHub repository previously created by
        Readux export.  Checks out the repository, creates a new branch,
        runs the iiif_to_jekyll import on that branch, pushes it to github,
        and creates a pull request.  Returns the HTML url for the new
        pull request on success.'''

        repo_url = 'github.com/{un}/{gr}.git'.format(
            un=self.github_username,
            gr=self.github_repo
        )

        # get auth repo url to use to create branch
        auth_repo_url = self.github_auth_repo(repo_name=self.github_repo)

        # create a tmpdir to clone the git repo into
        tmpdir = tempfile.mkdtemp(prefix='tmp-rdx-export-update')
        LOGGER.debug(
            'Cloning {r} to {t}'.format(
                r=repo_url,
                t=tmpdir
            )
        )
        repo = None
        if os.environ['DJANGO_ENV'] == 'test':
            repo = git.Repo.init(tmpdir)
            yml_config_path = os.path.join(tmpdir, '_config.yml')
            open(yml_config_path, 'a').close()
            repo.index.commit('initial commit')
            repo.git.checkout('HEAD', b='gh-pages')
        else:
            repo = git.Repo.clone_from(auth_repo_url, tmpdir, branch='gh-pages')
            repo.remote().pull()  # pragma: no cover
        # create and switch to a new branch and switch to it; using datetime
        # for uniqueness
        git_branch_name = 'readux-update-%s' % \
            datetime.now().strftime('%Y%m%d-%H%M%S')
        update_branch = repo.create_head(git_branch_name)
        update_branch.checkout()

        LOGGER.debug(
            'Updating export for {m} in {t}'.format(
                m=self.manifest.pid,
                t=tmpdir
            )
        )

        # remove all annotations and tag pages so that if an annotation is removed
        # or a tag is no longer used in readux, it will be removed in the export
        # (annotations and tags that are unchanged will be restored by the IIIF
        # jekyll import, and look unchanged to git if no different)
        try:
            repo.index.remove(['_annotations/*', 'tags/*', 'iiif_export/*'])
        except git.GitCommandError:
            # it's possible that an export has no annotations or tags
            # (although unlikely to occur anywhere but development & testing)
            # if there's an error on removal, ignore it
            pass

        # save image files if requested, and update image paths
        # to use local references
        # TODO
        # if self.include_images:
        #     self.save_page_images(tmpdir)

        self.jekyll_site_dir = tmpdir

        LOGGER.debug('Exporting IIIF bundle')
        iiif_zip_stream = IiifManifestExport.get_zip(self.manifest, 'v2', owners=self.owners)
        iiif_zip = zipfile.ZipFile(io.BytesIO(iiif_zip_stream), "r")

        iiif_zip.extractall(self.iiif_dir())



        # TODO
        # # save image files if requested, and update image paths
        # # to use local references
        # if self.include_images:
        #     self.save_page_images(jekyll_site_dir)
        # if self.include_deep_zoom:
        #     self.generate_deep_zoom(jekyll_site_dir)

        if os.environ['DJANGO_ENV'] != 'test':
            # run the script to import IIIF as jekyll site content
            self.import_iiif_jekyll(self.manifest, self.jekyll_site_dir) # pragma: no cover

            # add any files that could be updated to the git index
            repo.index.add([ # pragma: no cover
                '_config.yml', '_volume_pages/*', '_annotations/*',
                '_data/tags.yml', 'tags/*', 'iiif_export/*'
            ])
            # TODO: if deep zoom is added, we must add that directory as well

        git_author = git.Actor(
            self.user.name,
            self.user.email
        )
        # commit all changes
        repo.index.commit(
            'Updated Jekyll site by Readux {v}'.format(
                v=__version__
            ),
            author=git_author
        )

        if os.environ['DJANGO_ENV'] != 'test':
            # push the update to a new branch on github
            repo.remotes.origin.push( # pragma: no cover
                '{b}s:{b}s'.format(b=git_branch_name)
            )
        # convert repo url to form needed to generate pull request
        repo = repo_url.replace('github.com/', '').replace('.git', '')
        pullrequest = self.github.create_pull_request(
            repo, 'Updated export', git_branch_name, 'gh-pages')

        # clean up local checkout after successful push
        shutil.rmtree(tmpdir)

        # return the html url for the new pull request
        return pullrequest['html_url']

    # from readux/books/consumers.py in Readux 1.

    def github_export(self, user_email):
        """
        Export manifest to GitHub.

        :param user_email: Email of exporter.
        :type user_email: str
        :return: List of export URLs
        :rtype: list
        """
        LOGGER.debug('Background export started.')
        # user_has_github = False
        if self.user:
            # check if user has a github account linked
            try:
                GithubApi.github_account(self.user)
            except GithubAccountNotFound:
                LOGGER.info('User attempted github export with no github account.')

        # connect to github as the user in order to create the repository
        self.use_github(self.user)

        # check that oauth token has sufficient permission
        # to do needed export steps
        # TODO: httpretty seems to include the HEAD method, but it errors when
        # making the request because the Head method is not implemented.
        if os.environ['DJANGO_ENV'] != 'test' and 'repo' not in self.github.oauth_scopes():
            LOGGER.error('TODO: bad scope message')
            return None # pragma: no cover

        repo_url = None
        ghpages_url = None
        pr_url = None
        if not self.gitrepo_exists():
            # create a new github repository with exported jekyll site
            try:
                repo_url, ghpages_url = self.website_gitrepo()

                LOGGER.info('Exported %s to GitHub repo %s for user %s',
                            self.manifest.pid, repo_url, self.user.username)

            except GithubExportException as err:
                LOGGER.info('Export failed: {e}'.format(e=err))
        else:
            # update an existing github repository with new branch and
            # a pull request
            try:
                # TODO: How to highjack the request to
                # https://58816:x-oauth-basic@github.com/zaphod/marx.git/ when testing.
                if os.environ['DJANGO_ENV'] != 'test':
                    pr_url = self.update_gitrepo() # pragma: no cover
                else:
                    pr_url = 'https://github.com/{u}/{r}/pull/2'.format(
                        u=self.github_username,
                        r=self.github_repo
                    )

                LOGGER.info('GitHub jekyll site update completed')
                repo_url = 'https://github.com/%s/%s' % (self.github_username, self.github_repo)
                ghpages_url = 'https://%s.github.io/%s/' % (self.github_username, self.github_repo)
            except GithubExportException as err:
                self.notify_msg('Export failed: {e}'.format(e=err))

        context = {}
        context['repo_url'] = repo_url
        context['ghpages_url'] = ghpages_url
        context['pr_url'] = pr_url

        # It takes GitHub a few to build the site. This holds the email till the site
        # is available. If it takes longer than 10 minutes, and email is sent saying
        # that is is taking longer than expected.
        tries = 0
        sleep_for = 15 if os.environ['DJANGO_ENV'] != 'test' else 0.1
        while not self.__check_site(ghpages_url, tries):
            for _ in range(0,10):
                print(tries)
            tries += 1
            sleep(sleep_for)

        if tries < 45:
            email_subject = 'Your Readux site export is ready!'
            email_contents = get_template('jekyll_export_email.html').render(context)
            text_contents = get_template('jekyll_export_email.txt').render(context)
        else:
            email_subject = 'Your Readux site export is taking longer than expected'
            email_contents = get_template('jekyll_export_email_error.html').render(context)
            text_contents = get_template('jekyll_export_email_error.txt').render(context)

        send_mail(
            email_subject,
            text_contents,
            settings.READUX_EMAIL_SENDER,
            [user_email],
            fail_silently=False,
            html_message=email_contents
        )

        return [repo_url, ghpages_url, pr_url]

    def download_export(self, user_email, volume):
        """Download exported manifest.

        :param user_email: Exporter's email address.
        :type user_email: str
        :param volume: Manifest being exported.
        :type volume: apps.iiif.manifests.models.Manifest
        :return: Filename for the exported zip.
        :rtype: str
        """

        LOGGER.debug(
            'Background download export started.  Sending email to {ue}'.format(
                ue=user_email
            )
        )

        zip_file = self.website_zip()
        context = {}
        context["filename"] = os.path.basename(zip_file.name)
        context["volume"] = volume
        context["hostname"] = settings.HOSTNAME

        email_contents = get_template('download_export_email.html').render(context)
        text_contents = get_template('download_export_email.txt').render(context)

        # TODO: Maybe break this out so we can test it?
        send_mail(
            'Your Readux site export is ready!',
            text_contents,
            settings.READUX_EMAIL_SENDER,
            [user_email],
            fail_silently=False,
            html_message=email_contents
        )

        return zip_file.name

    def __check_site(self, url, tries):
        # if os.environ['DJANGO_ENV'] == 'test':
        #     httpretty.enable(verbose=True, allow_net_connect=False)  # enable HTTPretty so that it will monkey patch the socket module
        #     httpretty.register_uri(httpretty.GET, url, status=404)
        if tries > 45:
            return True
        # raise NameError(url)
        req = get(url, verify=False, timeout=1)
        if req.status_code == 200:
            return True
        return False
