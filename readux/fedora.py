import logging
from django.conf import settings
from django.core.urlresolvers import reverse
from django.utils.encoding import iri_to_uri

from eulfedora import models, server
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

    def __init__(self, *args, **kwargs):
        default_pidspace = getattr(settings, 'FEDORA_PIDSPACE', None)
        kwargs['default_pidspace'] = default_pidspace
        super(DigitalObject, self).__init__(*args, **kwargs)
        self._default_target_data = None

    @property
    def noid(self):
        pidspace, noid = self.pid.split(':')
        return noid

    PID_TOKEN = '{%PID%}'
    ENCODED_PID_TOKEN = iri_to_uri(PID_TOKEN)
    def get_default_pid(self):
        '''Default pid logic for DigitalObjects in the Readux.  Mint a
        new ARK via the PID manager, store the ARK in the MODS
        metadata (if available) or Dublin Core, and use the noid
        portion of the ARK for a Fedora pid in the site-configured
        Fedora pidspace.'''

        if pidman is not None:
            # pidman wants a target for the new pid
            '''Get a pidman-ready target for a named view.'''

            # first just reverse the view name.
            pid = '%s:%s' % (self.default_pidspace, self.PID_TOKEN)
            target = reverse(self.NEW_OBJECT_VIEW, kwargs={'pid': pid})
            # reverse() encodes the PID_TOKEN, so unencode just that part
            target = target.replace(self.ENCODED_PID_TOKEN, self.PID_TOKEN)
            # reverse() returns a full path - absolutize so we get scheme & server also
            target = absolutize_url(target)
            # pid name is not required, but helpful for managing pids
            pid_name = self.label
            # ask pidman for a new ark in the configured pidman domain
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
