from background_task import background
from django.core.mail import send_mail
from django.core.serializers import serialize
from django.template.loader import get_template

from .models import Manifest

from apps.iiif.annotations.models import Annotation
from apps.iiif.canvases.models import Canvas
from apps.iiif.manifests import github
from apps.iiif.manifests.github import GithubApi
from apps.users.models import User
from apps.readux.models import UserAnnotation
from datetime import datetime
from urllib.parse import urlparse

import git
from git.cmd import Git
import config.settings.local as settings
import digitaledition_jekylltheme
import io
import json
import logging
import os
import re
import shutil
import subprocess
import tempfile
import yaml
import zipfile

__version__="2.0.0"


logger = logging.getLogger(__name__)

# zip file of base jekyll site with digital edition templates
JEKYLL_THEME_ZIP = digitaledition_jekylltheme.ZIPFILE_PATH
class ExportException(Exception):
    pass


class IiifManifestExport:
    @classmethod
    def get_zip(self, manifest, version, owners=[]):
        zip_subdir = manifest.label
        zip_filename = "iiif_export.zip"

        # Open BytesIO to grab in-memory ZIP contents
        byte_stream = io.BytesIO()

        # The zip compressor
        zf = zipfile.ZipFile(byte_stream, "w")

        # First write basic human-readable metadata
        ''' Annotated edition from {grab site identity/version of Readux} at {grab site URL}
        volume title
        volume author
        volume date
        volume publisher
        number of pages
        annotator username
        time of export
        '''
        title = manifest.label
        author = manifest.author
        date = manifest.published_date
        publisher = manifest.publisher
        page_count = manifest.canvas_set.count()
        now = datetime.utcnow()
        readux_url = settings.HOSTNAME
        annotators = User.objects.filter(userannotation__canvas__manifest__id=manifest.id).distinct()
        annotators_string = ', '.join([i.fullname() for i in annotators])
        # get the owner_id for each/all annotations
        # dedup the list of owners (although -- how to order?  alphabetical or by contribution count or ignore order)  .distinct()
        # turn the list of owners into a comma separated string of formal names instead of user ids
        readme = "Annotation export from Readux %(version)s at %(readux_url)s\nedition type: Readux IIIF Exported Edition\nexport date: %(now)s UTC\n\n" % locals()
        volume_data = "volume title: %(title)s\nvolume author: %(author)s\nvolume date: %(date)s\nvolume publisher: %(publisher)s\npages: %(page_count)s \n" % locals()
        annotators_attribution_string = "Annotated by: " + annotators_string +"\n\n"
        boilerplate = "Readux is a platform developed by Emory University’s Center for Digital Scholarship for browsing, annotating, and publishing with digitized books. This zip file includes an International Image Interoperability Framework (IIIF) manifest for the digitized book and an annotation list for each page that includes both the encoded text of the book and annotations created by the user who created this export. This bundle can be used to archive the recognized text and annotations for preservation and future access.\n\n"
        explanation = "Each canvas (\"sc:Canvas\") in the manifest represents a page of the work. Each canvas includes an \"otherContent\" field-set with information identifying that page's annotation lists. This field-set includes an \"@id\" field and the label field (\"@type\") \"sc:AnnotationList\" for each annotation list. The \"@id\" field contains the URL link at which the annotation list was created and originally hosted from the Readux site. In order to host this IIIF manifest and its annotation lists again to browse the book and annotations outside of Readux, these @id fields would need to be updated to the appropriate URLs for the annotation lists on the new host. Exported annotation lists replace nonword characters (where words are made up of alphanumerics and underscores) with underscores in the filename."
        readme = readme + volume_data + annotators_attribution_string + boilerplate + explanation
        zf.writestr('README.txt', readme)

        # Next write the manifest
        zf.writestr('manifest.json',
            json.dumps(
                json.loads(
                    serialize(
                        'manifest',
                        [manifest],
                        version=version,
                        annotators=User.objects.get(id__in=owners).name,
                        exportdate=now
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

                annotation_file = re.sub('\W','_', anno_uri) + ".json"

                zf.writestr(
                    annotation_file,
                    json.dumps(
                      json_hash,
                      indent=4
                    )
                )
        # Then write the user annotations
        for canvas in manifest.canvas_set.all():
            if canvas.userannotation_set.count() > 0:
                annotations = canvas.userannotation_set.filter(owner__in=owners).all()
                json_hash = json.loads(
                    serialize(
                        'user_annotation_list',
                        [canvas],
                        version=version,
                        is_list=False,
                        owners=[User.objects.get(id__in=owners)]
                    )
                )
                anno_uri = json_hash['@id']
                annotation_file = re.sub('\W','_', anno_uri) + ".json"

                zf.writestr(
                    annotation_file,
                    json.dumps(
                      json_hash,
                      indent=4
                    )
                )

        zf.close() # flush zipfile to byte stream

        return byte_stream.getvalue()


class GithubExportException(Exception):
    pass

class JekyllSiteExport(object):
    def __init__(self, manifest, version, page_one=None,
                 include_images=False, deep_zoom='hosted', github_repo=None, owners=None, user=None):
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
        self.github_repo=github_repo


    def log_status(self, msg):
        logger.info(msg)

    def notify_msg(self, msg):
        log_status(msg)


    def get_zip(self):
        return self.website_zip()

    def get_zip_path(filename):
        return os.path.join(tempfile.gettempdir(), filename)

    def get_zip_file(self, filename):
        f=open(JekyllSiteExport.get_zip_path(filename),"rb")
        data=f.read()
        f.close()
        return data

    def iiif_dir(self):
        return os.path.join(self.jekyll_site_dir, 'iiif_export')

    def import_iiif_jekyll(self, manifest, tmpdir):
        # run the script to get a fresh import of IIIF as jekyll site content
        self.log_status('Running jekyll import IIIF manifest script')
        jekyllimport_manifest_script = settings.JEKYLLIMPORT_MANIFEST_SCRIPT
        import_command = [jekyllimport_manifest_script, '--local-directory', '-q', self.iiif_dir(), tmpdir]
        # TODO
        # # if a page number is specified, pass it as a parameter to the script
        # if self.page_one is not None:
        #     import_command.extend(['--page-one', unicode(self.page_one)])
        # # if no deep zoom is requested, pass through so the jekyll
        # #  config can be updated appropriately
        if self.no_deep_zoom:
            import_command.append('--no-deep-zoom')

        try:
            logger.debug('Jekyll import command: %s', ' '.join(import_command))
            output = subprocess.check_output(' '.join(import_command), shell=True, stderr=subprocess.STDOUT)
            logger.debug('Jekyll import output:')
            logger.debug(output.decode('utf-8'))
        except subprocess.CalledProcessError as e:
            logger.debug('Jekyll import error:')
            logger.debug(e.output)
            err_msg = "Error running jekyll import on IIIF manifest!\n" + ' '.join(import_command) + "\n" + e.output.decode('utf-8')
            logger.error(err_msg)
            raise ExportException(err_msg)



    def generate_website(self):
        """Generate a jekyll website for a volume with annotations.
        Creates a jekyll site and imports pages and annotations from the IIIF,
        and then returns the directory for further use (e.g., packaging as
        a zipfile for download, or for creating a new GitHub repository).
        """
        logger.debug('Generating jekyll website for %s', self.manifest.id)
        tmpdir = tempfile.mkdtemp(prefix='tmp-rdx-export')
        logger.debug('Building export for %s in %s', self.manifest.id, tmpdir)

        # unzip jekyll template site
        self.log_status('Extracting jekyll template site')
        with zipfile.ZipFile(JEKYLL_THEME_ZIP, 'r') as jekyllzip:
            jekyllzip.extractall(tmpdir)
        self.jekyll_site_dir = os.path.join(tmpdir, 'digitaledition-jekylltheme')
        logger.debug('Jekyll site dir:')
        logger.debug(self.jekyll_site_dir)

        logger.debug('Exporting IIIF bundle')
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


    def edition_dir(self,export_dir):
        return os.path.join(export_dir, '%s_annotated_jekyll_site' %
                     self.manifest.id)


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
            prefix='%s_annotated_site_' % self.manifest.id,
            delete=False)
        shutil.make_archive(
            # name of the zipfile to create without .zip
            os.path.splitext(webzipfile.name)[0],
            'zip',  # archive format; could also do tar
            export_dir
        )
        logger.debug('Jekyll site web export zipfile for %s is %s',
                     self.manifest.id, webzipfile.name)
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

    def gitrepo_exists(self):
        current_repos = self.github.list_repos(self.github_username)
        current_repo_names = [repo['name'] for repo in current_repos]
        logger.debug("Checking to see if "+self.github_repo+" in: "+ " ".join(current_repo_names))
        return self.github_repo in current_repo_names



    def website_gitrepo(self):
        '''Create a new GitHub repository and populate it with content from
        a newly generated jekyll website export created via :meth:`website`.
        :return: on success, returns a tuple of public repository url and
            github pages url for the newly created repo and site
        '''

        # NOTE: github pages sites now default to https
        github_pages_url = 'https://%s.github.io/%s/' % \
            (self.github_username, self.github_repo)

        # before even starting to generate the jekyll site,
        # check if requested repo name already exists; if so, bail out with an error
        logger.debug('Checking github repo %s for %s', self.github_repo,
                     self.github_username)

        if self.gitrepo_exists():
            raise GithubExportException('GitHub repo %s already exists.' \
                                        % self.github_repo)

        export_dir = self.generate_website()

        # jekyll dir is *inside* the export directory;
        # for the jekyll site to display correctly, we need to commit what
        # is in the directory, not the directory itself
        jekyll_dir = self.edition_dir(export_dir) 

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

        logger.debug('Creating github repo %s for %s', self.github_repo,
                     self.github_username)
        self.github.create_repo(
            self.github_repo, homepage=github_pages_url,
            description='An annotated digital edition created with Readux')

        # get auth repo url to use to push data
        repo_url = self.github_auth_repo(repo_name=self.github_repo)

        # add the jekyll site to github; based on these instructions:
        # https://help.github.com/articles/adding-an-existing-project-to-github-using-the-command-line/

        # initialize export dir as a git repo, and commit the contents
        # NOTE: to debug git commands, print the git return to see git output

        gitcmd = Git(jekyll_dir)
        # initialize jekyll site as a git repo
        gitcmd.init()
        # add and commit all contents
        gitcmd.config("user.email",self.user.email);
        gitcmd.config("user.name",self.user.fullname());

        gitcmd.add(['.'])
        gitcmd.commit(
            ['-m', 'Import Jekyll site generated by Readux %s' % __version__,
             '--author="%s <%s>"' % (self.user.fullname(),
                                     self.user.email)])
        # push local master to the gh-pages branch of the newly created repo,
        # using the user's oauth token credentials
        self.log_status('Pushing new content to GitHub')
        gitcmd.push([repo_url, 'master:gh-pages'])

        # clean up temporary files after push to github
        shutil.rmtree(export_dir)

        # generate public repo url for display to user
        public_repo_url = 'https://github.com/%s/%s' % (self.github_username,
                                                        self.github_repo)
        return (public_repo_url, github_pages_url)

    def update_gitrepo(self):
        '''Update an existing GitHub repository previously created by
        Readux export.  Checks out the repository, creates a new branch,
        runs the iiif_to_jekyll import on that branch, pushes it to github,
        and creates a pull request.  Returns the HTML url for the new
        pull request on success.'''

        repo_url = 'github.com/%s/%s.git' % (self.github_username, self.github_repo)

        # get auth repo url to use to create branch
        auth_repo_url = self.github_auth_repo(repo_name=self.github_repo)

        # create a tmpdir to clone the git repo into
        tmpdir = tempfile.mkdtemp(prefix='tmp-rdx-export-update')
        logger.debug('Cloning %s to %s', repo_url, tmpdir)
        repo = git.Repo.clone_from(auth_repo_url, tmpdir, branch='gh-pages')
        repo.remote().pull()
        # create and switch to a new branch and switch to it; using datetime
        # for uniqueness
        git_branch_name = 'readux-update-%s' % \
            datetime.now().strftime('%Y%m%d-%H%M%S')
        update_branch = repo.create_head(git_branch_name)
        update_branch.checkout()

        logger.debug('Updating export for %s in %s', self.manifest.pid, tmpdir)

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

        logger.debug('Exporting IIIF bundle')
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

        # add any files that could be updated to the git index
        repo.index.add(['_config.yml', '_volume_pages/*', '_annotations/*',
                        '_data/tags.yml', 'tags/*', 'iiif_export/*'])
        # TODO if deep zoom is added, we must add that directory as well

        git_author = git.Actor(self.user.fullname(),
                               self.user.email)
        # commit all changes
        repo.index.commit('Updated Jekyll site by Readux %s' % __version__,
                          author=git_author)

        # push the update to a new branch on github
        repo.remotes.origin.push('%(branch)s:%(branch)s' %
                                 {'branch': git_branch_name})
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
        logger.debug('Background export started.')
        user_has_github = False
        if not self.user == None:
            # check if user has a github account linked
            try:
                github.GithubApi.github_account(self.user)
            except github.GithubAccountNotFound:
                logger.info('User attempted github export with no github account.')


        # connect to github as the user in order to create the repository
        self.use_github(self.user)

        # check that oauth token has sufficient permission
        # to do needed export steps
        if 'repo' not in self.github.oauth_scopes():
            logger.error('TOOO bad scope message')
            return

        repo_url = None
        ghpages_url = None
        pr_url = None
        if not self.gitrepo_exists():
            # create a new github repository with exported jekyll site
            try:
                repo_url, ghpages_url = self.website_gitrepo()

                logger.info('Exported %s to GitHub repo %s for user %s',
                            self.manifest.pid, repo_url, self.user.username)

            except GithubExportException as err:
                logger.info('Export failed: %s' % err)
        else:
            # update an existing github repository with new branch and
            # a pull request
            try:
                pr_url = self.update_gitrepo()

                logger.info('GitHub jekyll site update completed')
                repo_url = 'https://github.com/%s/%s' % (self.github_username, self.github_repo)
                ghpages_url = 'https://%s.github.io/%s/' % (self.github_username, self.github_repo)
            except GithubExportException as err:
                notify_msg('Export failed: %s' % err, 'error')

        context = {}
        context['repo_url'] = repo_url
        context['ghpages_url'] = ghpages_url
        context['pr_url'] = pr_url

        email_contents = get_template('jekyll_export_email.html').render(context)
        text_contents = get_template('jekyll_export_email.txt').render(context)
        send_mail(
            'Your Readux site export is ready!',
            text_contents,
            settings.READUX_EMAIL_SENDER,
            [user_email],
            fail_silently=False,
            html_message=email_contents
        )


        return [repo_url, ghpages_url, pr_url]


    def download_export(self, user_email, volume):
        logger.debug('Background download export started.  Sending email to ' + user_email)
 
        zipfile=self.website_zip()
        context = {}
        context["filename"]=os.path.basename(zipfile.name)
        context["volume"]=volume
        context["hostname"]=settings.HOSTNAME

        email_contents = get_template('download_export_email.html').render(context)
        text_contents = get_template('download_export_email.txt').render(context)

        send_mail(
            'Your Readux site export is ready!',
            text_contents,
            settings.READUX_EMAIL_SENDER,
            [user_email],
            fail_silently=False,
            html_message=email_contents
        )

        return zipfile.name