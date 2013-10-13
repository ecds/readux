from django.utils.translation import ugettext_lazy as _
from django.contrib.auth import logout
from django.contrib import messages

from ..models import UserActivityAudit
from .. import constants

class UserActivityAuitMiddleware(object):

    def process_request(self, request):
        """ Monitor User's Activity """

        if not request.is_ajax() and request.user.is_authenticated():
            try:
                uaa = UserActivityAudit.objects.get(audit_key=request.session[constants.ACTIVITYWARE_AUDIT_KEY])
            except:
                logout(request) # we shouldn't be here
            else:
                if uaa and uaa.last_page != request.path:
                    uaa.last_page = request.path
                    uaa.pages_viwed += 1
                    uaa.save()
        return None



