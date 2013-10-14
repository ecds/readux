from django.utils.translation import ugettext_lazy as _
from django.contrib.auth import logout
from django.contrib import messages

from ..models import UserAudit
from .. import constants

class UserAuditMiddleware(object):

    def process_request(self, request):
        """ User Activity Audit """

        if not request.is_ajax() and request.user.is_authenticated():
            try:
                audit = UserAudit.objects.get(audit_key=request.session[constants.USERWARE_AUDIT_KEY])
            except UserAudit.DoesNotExist:
                logout(request) # we shouldn't be here
            else:
                if audit and audit.last_page != request.path:
                    audit.last_page = request.path
                    audit.pages_viwed += 1
                    audit.save()
        return None

