from django.utils.translation import ugettext_lazy as _
from django.contrib.auth import logout
from django.contrib import messages

from ..models import UserAudit
from ..utils import get_audit_object_for_session
from .. import constants

class LogoutEnforcementMiddleware(object):

    def process_request(self, request):
        """ Logout user """

        if request.user.is_authenticated():
            audit = get_audit_object_for_session(request)
            if audit and audit.force_logout:
                messages.add_message(request, messages.WARNING, 
                    _('Warning!. This session was terminated remotely by the owner of the account.'))
                logout(request)
        return None



