from django.utils.translation import ugettext_lazy as _
from django.contrib import messages

from ..models import UserAudit
from ..utils import get_audit_object_for_session
from .. import constants

class UserAuditMiddleware(object):

    def process_request(self, request):
        """ User Activity Audit """

        if not request.is_ajax() and request.user.is_authenticated():
            audit = get_audit_object_for_session(request)
            if audit and audit.last_page != request.path:
                audit.last_page = request.path
                audit.pages_viwed += 1
                audit.save()
        return None

