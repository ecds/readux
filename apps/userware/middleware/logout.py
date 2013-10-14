from django.utils.translation import ugettext_lazy as _
from django.contrib.auth import logout
from django.contrib import messages

from ..models import UserAudit
from .. import constants

class LogoutEnforcementMiddleware(object):

    def process_request(self, request):
        """ Logout user """

        if request.user.is_authenticated():
            try:
                audit = UserAudit.objects.get(audit_key=request.session[constants.USERWARE_AUDIT_KEY])
            except UserAudit.DoesNotExist:
                logout(request) # we shouldn't be here
            else:
                if audit and audit.force_logout:
                    messages.add_message(request, messages.WARNING, 
                            _('Warning!. This session was terminated remotely by the owner of the account.'))
                    logout(request)
        return None



