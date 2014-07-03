import logging
from django.conf import settings

from eulfedora import server


logger = logging.getLogger(__name__)

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

