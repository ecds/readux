import logging
from django.conf import settings
from django.core.urlresolvers import reverse
import httplib
import urllib

from eulfedora import models, server
from eulxml.xmlmap.dc import DublinCore
from pidservices.clients import parse_ark
from pidservices.djangowrapper.shortcuts import DjangoPidmanRestClient

from readux.utils import absolutize_url

logger = logging.getLogger(__name__)


# try to configure a pidman client to get pids.
try:
    pidman = DjangoPidmanRestClient()
except:
    # if we're in dev mode then we can fall back on the fedora default
    # pid allocator. in non-dev, though, we really need pidman
    if getattr(settings, 'DEV_ENV', False):
        logger.warn('Failed to configure PID manager client; default pid logic will be used')
        pidman = None
    else:
        raise


class ManagementRepository(server.Repository):
    '''Convenience class to initialize an instance of :class:`eulfedora.server.Repository`
    with Fedora management/maintenance account credentials defined in Django settings.

    .. Note::

        This :class:`~eulfedora.server.Repository` variant should only
        be used for maintainance tasks (e.g., scripts that ingest,
        modify, or otherwise manage content).  It should **not** be
        used for general website views or access; those views should
        use the standard :class:`~eulfedora.server.Repository` which
        will pick up the default, non-privileged credentials intended
        for read and display access but not for modifying content in
        the repository.

    '''
    default_pidspace = getattr(settings, 'FEDORA_PIDSPACE', None)
    # default pidspace is not automatically pulled from django conf
    # when user/password are specified, so explicitly set it here

    def __init__(self):
        # explicitly disabling other init args, so that anyone who tries to use
        # this as a regular repo will get errors rather than confusing behavior
        super(ManagementRepository, self).__init__(username=settings.FEDORA_MANAGEMENT_USER,
                                                   password=settings.FEDORA_MANAGEMENT_PASSWORD)


class DigitalObject(models.DigitalObject):
    """Extend the default fedora DigitalObject class with logic for setting
    pids based on PID manager ids."""


    #: :class:`~eulfedora.models.XmlDatastream` for the required Fedora
    #: **DC** datastream; datastream content loaded as an instance
    #: of :class:`eulxml.xmlmap.dc.DublinCore`; overriding default
    #: declaration in eulfedora to configure as Managed instead of Inline XML
    dc = models.XmlDatastream("DC", "Dublin Core", DublinCore, defaults={
        'control_group': 'M',
        'format': 'http://www.openarchives.org/OAI/2.0/oai_dc/',
        'versionable': True
    })
    # NOTE: we don't really need DC versioned, but there is a Fedora bug
    # that requires Managed DC be versioned

    #: :class:`~eulfedora.models.RdfDatastream` for the standard Fedora
    #: **RELS-EXT** datastream; overriding to configure as Managed instead
    #: of Inline XML
    rels_ext = models.RdfDatastream("RELS-EXT", "External Relations", defaults={
            'control_group': 'M',
            'format': 'info:fedora/fedora-system:FedoraRELSExt-1.0',
        })

    def __init__(self, *args, **kwargs):
        default_pidspace = getattr(settings, 'FEDORA_PIDSPACE', None)
        kwargs['default_pidspace'] = default_pidspace
        super(DigitalObject, self).__init__(*args, **kwargs)
        self._default_target_data = None

    @property
    def noid(self):
        pidspace, noid = self.pid.split(':')
        return noid

    @property
    def ark_uri(self):
        for dcid in self.dc.content.identifier_list:
            print dcid
            if 'ark:/' in dcid:
                return dcid

    #: special pid token that tells pid manager to put the newly minted
    # pid into the url
    PID_TOKEN = '{%PID%}'

    def get_default_pid(self):
        '''Default pid logic for DigitalObjects in :mod:`readux`.  Mint a
        new ARK via the PID manager, store the ARK in the MODS
        metadata (if available) or Dublin Core, and use the noid
        portion of the ARK for a Fedora pid in the site-configured
        Fedora pidspace.'''
        global pidman

        if pidman is not None:
            # pidman wants a target for the new pid
            # generate a pidman-ready target for a named view

            # first just reverse the view name.
            pid = '%s:%s' % (self.default_pidspace, self.PID_TOKEN)
            target = reverse(self.NEW_OBJECT_VIEW, kwargs={'pid': pid})

            # reverse() encodes the PID_TOKEN and the :, so just unquote the url
            # (shouldn't contain anything else that needs escaping)
            target = urllib.unquote(target)

            # reverse() returns a full path - absolutize so we get scheme & server also
            target = absolutize_url(target)
            # pid name is not required, but helpful for managing pids
            pid_name = self.label
            # ask pidman for a new ark in the configured pidman domain
            try:
                ark = pidman.create_ark(settings.PIDMAN_DOMAIN, target, name=pid_name)
            except httplib.BadStatusLine:
                logger.warn('Error creating ARK; re-initializing pidman client and trying again')
                pidman = DjangoPidmanRestClient()
                ark = pidman.create_ark(settings.PIDMAN_DOMAIN, target, name=pid_name)
            # pidman returns the full, resolvable ark
            # parse into dictionary with nma, naan, and noid
            parsed_ark = parse_ark(ark)
            noid = parsed_ark['noid']  # nice opaque identifier

            # Add full uri ARK to dc:identifier
            self.dc.content.identifier_list.append(ark)

            # use the noid to construct a pid in the configured pidspace
            return '%s:%s' % (self.default_pidspace, noid)
        else:
            # if pidmanager is not available, fall back to default pid behavior
            return super(DigitalObject, self).get_default_pid()

    def index_data_descriptive(self):
        '''Extend the default :meth:`eulfedora.models.DigitalObject.index_data`
        to do common clean up for all Readux indexing:

        - If there are multiple titles, choose the longest one.
        '''

        data = super(DigitalObject, self).index_data_descriptive()

        # a few books have multiple titles;
        # if title is a list, choose the longest one
        if 'title' in data and isinstance(data['title'], list):
            title = ''
            for d in data['title']:
                if len(d) > len(title):
                    title = d
            data['title'] = title

        return data