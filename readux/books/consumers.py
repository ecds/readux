from os.path import basename
from django.conf import settings
from django.contrib.auth import get_user_model
from django.template.defaultfilters import filesizeformat
from channels import Group
import json
import logging
import os

from eulfedora.server import Repository
from boto.s3.connection import S3Connection
from boto.s3.key import Key

from readux.annotations.models import AnnotationGroup
from readux.books import annotate, export, github
from readux.books.models import Volume
from readux.books.forms import VolumeExport
from readux.books.views import AnnotatedVolumeExport


logger = logging.getLogger(__name__)


def volume_export(message):
    '''Consumer method to handle volume export form submission via
    websockets.  Initializes :class:`readux.books.export.VolumeExport`
    and then calls the appropriate method based on the requested export
    mode.
    '''

    username = message.content['user']
    user = get_user_model().objects.get(username=username)
    pid = message.content['formdata']['pid']
    # NOTE: for some reason, reply channel is not set on this message
    # using a group notification based on username rather than
    # relying on current websocket
    notify = Group(u"notify-%s" % user.username)

    def notify_msg(text, msg_type=None, **data):
        msg_data = {'message': text}
        if msg_type is not None:
            msg_data['type'] = msg_type
        msg_data.update(data)
        notify.send({'text': json.dumps(msg_data)})

    notify_msg('Export started')

    user_has_github = False
    if not user.is_anonymous():
        # check if user has a github account linked
        try:
            github.GithubApi.github_account(user)
            user_has_github = True
        except github.GithubAccountNotFound:
            notify_msg(AnnotatedVolumeExport.github_account_msg, 'warning')

    export_form = VolumeExport(user, user_has_github,
                               message.content['formdata'])

    if not export_form.is_valid():
        notify_msg('Form is not valid; please modify and resubmit',
                   'error', form_errors=export_form.errors)
        logger.debug("Export form is not valid: %s", export_form.errors)
        # bail out
        return

    # if form is valid, then proceed with the export
    cleaned_data = export_form.cleaned_data
    export_mode = cleaned_data['mode']
    image_hosting = cleaned_data['image_hosting']
    include_images = (image_hosting == 'independently_hosted')
    deep_zoom = cleaned_data['deep_zoom']
    include_deep_zoom = (deep_zoom == 'include')
    no_deep_zoom = (deep_zoom == 'exclude')
    # This gets set below if exporting to GitHub.
    github_repo = None
    # deep zoom can't be included without including page images
    # this should be caught by form validation, but in case it isn't,
    # just assume include images is true if we get to this point
    if include_deep_zoom and not include_images:
        include_images = True

    # if github export or update is requested, make sure user
    # has a github account available to use for access
    # and add the repo name to the parameters
    if export_mode in ['github', 'github_update']:
        try:
            github.GithubApi.github_account(user)
            github_repo = cleaned_data['github_repo']
        except github.GithubAccountNotFound:
            notify_msg(AnnotatedVolumeExport.github_account_msg, 'error')
            return

        # check that oauth token has sufficient permission
        # to do needed export steps
        gh = github.GithubApi.connect_as_user(user)
        # note: repo would also work here, but currently asking for public_repo
        if 'public_repo' not in gh.oauth_scopes():
            notify_msg(AnnotatedVolumeExport.github_scope_msg, 'error')
            return

    repo = Repository()
    vol = repo.get_object(pid, type=Volume)

    # determine which annotations should be loaded
    if cleaned_data['annotations'] == 'user':
        # annotations *by* this user
        # (NOT all annotations the user can view)
        annotations = vol.annotations().filter(user=user)
    elif cleaned_data['annotations'].startswith('group:'):
        # all annotations visible to a group this user belongs to
        group_id = cleaned_data['annotations'][len('group:'):]
        # NOTE: object not found error should not occur here,
        # because only valid group ids should be valid choices
        group = AnnotationGroup.objects.get(pk=group_id)
        annotations = vol.annotations().visible_to_group(group)

    notify_msg('Collected %d annotations' % annotations.count(),
               'status')
    # NOTE: could update message to indicate if using IIIF image urls
    notify_msg('Generating volume TEI', 'status')
    tei = vol.generate_volume_tei()
    notify_msg('Finished generating volume TEI', 'status')

    # if user requests images included, the image paths in the tei
    # need to be updated and the images need to be downloaded
    # to the local package (which doesn't exist yet...)
    if include_images:
        notify_msg('Updating image references in TEI', 'status')
        for i in range(len(tei.page_list)):
            teipage = tei.page_list[i]
            page = vol.pages[i]
            # convert from readux image url to
            # IIIF image url, so it can be downloaded and converted to
            # an image path local to the site
            for graphic in teipage.graphics:
                # NOTE: some redundancy here with mode checks
                # and modes in the page image view
                if graphic.rend == 'full':
                    graphic.url = unicode(page.iiif)
                elif graphic.rend == 'page':
                    graphic.url = unicode(page.iiif.page_size())
                elif graphic.rend == 'thumbnail':
                    graphic.url = unicode(page.iiif.thumbnail())
                elif graphic.rend == 'small-thumbnail':
                    graphic.url = unicode(page.iiif.mini_thumbnail())
                elif graphic.rend == 'json':
                    graphic.url = unicode(page.iiif.info())

                # TODO: canonicalize image urls *before* saving/referencing

    # generate annotated tei
    tei = annotate.annotated_tei(tei, annotations)
    notify_msg('Annotated TEI')

    exporter = export.VolumeExport(
        vol, tei, page_one=cleaned_data['page_one'],
        update_callback=notify_msg, include_images=include_images,
        deep_zoom=deep_zoom, github_repo=github_repo)

    # NOTE: passing in notify_msg method so that export methods
    # can also report on progress

    # exporting annotated tei only
    if export_mode == 'tei':
        # reuse volume exporter logic to serialize the file to disk
        teifile = exporter.save_tei_file()
        # upload to temporary S3 bucket and send link to the user
        # - include username to avoid collisions with different users
        # exporting the same valume
        filename = '%s_annotated_tei_%s.xml' % (vol.noid, user.username)
        content_disposition = 'attachment;filename="%s"' % filename

        download_url = s3_upload(teifile.name, filename,
                                 content_disposition=content_disposition)
        notify_msg('TEI file available for download', 'status',
                   download_tei=True, download_url=download_url)

    # check form data to see if github repo is requested
    elif export_mode == 'github':
        # create a new github repository with exported jekyll site
        try:
            repo_url, ghpages_url = exporter.website_gitrepo(
                user, cleaned_data['github_repo'])

            logger.info('Exported %s to GitHub repo %s for user %s',
                        vol.pid, repo_url, user.username)

            # send success with urls to be displayed
            notify_msg('Export to GitHub complete', 'status',
                       github_export=True, repo_url=repo_url,
                       ghpages_url=ghpages_url)

        except export.GithubExportException as err:
            notify_msg('Export failed: %s' % err, 'error')

    elif export_mode == 'github_update':
        # update an existing github repository with new branch and
        # a pull request
        try:
            pr_url = exporter.update_gitrepo(user, cleaned_data['update_repo'])

            notify_msg('GitHub jekyll site update completed', 'status',
                       github_update=True, pullrequest_url=pr_url,
                       repo_url=cleaned_data['update_repo'])

        except export.GithubExportException as err:
            notify_msg('Export failed: %s' % err, 'error')

    elif export_mode == 'download':
        # non github export: download a jekyll site as a zipfile
        try:
            webzipfile = exporter.website_zip()
            logger.info('Exported %s as jekyll zipfile for user %s',
                        vol.pid, user.username)
            notify_msg('Generated Jeyll zip file')

            # upload the generated zipfile to an Amazon S3 bucket configured
            # to auto-expire after 23 hours, so user can download
            notify_msg('Uploading zip file to Amazon S3')
            # include username in downlaod file label to avoid collisions
            label = '%s_annotated_jekyll_site_%s' % (vol.noid, user.username)
            download_url = s3_upload(webzipfile.name, label)

            notify_msg('Zip file available for download', 'status',
                       download=True, download_url=download_url)

        except export.ExportException as err:
            # display error to user
            notify_msg('Export failed: %s' % err, 'error')


def s3_upload(filename, label=None, content_disposition=None):
    '''Upload a file to the Amazon S3 bucket configured in local settings.
    (Should be configured to auto-expire after 24 hours.)

    :param filename: full path to file to be uploaded
    :param label: optional file name to use for the download; if not
        specified, will be generated from filename basename
    :param content_disposition: optional content-disposition header value,
        e.g. to prompt download of a type that could be displayed
        in the browser (e.g. xml)
    '''
    s3_conn = S3Connection(settings.AWS_ACCESS_KEY_ID,
                           settings.AWS_SECRET_ACCESS_KEY)
    s3_bucket = s3_conn.get_bucket(settings.AWS_S3_BUCKET)
    key = Key(s3_bucket)
    # use base filename as label, if no label is specified
    if label is None:
        label = basename(filename)
    key.key = label
    if content_disposition is not None:
        key.set_metadata('Content-Disposition', content_disposition)
    # NOTE: if zip file exports get very large (e.g. when including
    # images or deep zoom), this will need to be converted to a
    # multi-part upload
    # for now, log file size so we can check on errors
    filesize = os.stat(filename).st_size
    logger.info('File %s to upload to S3 is %s (%sb)',
                filename, filesizeformat(filesize), filesize)
    key.set_contents_from_filename(filename)
    # make the file publicly readable
    key.set_acl('public-read')

    return 'https://s3.amazonaws.com/%s/%s' % \
        (settings.AWS_S3_BUCKET, label)
