from uuid import uuid4
from django.db import models
from django.db.models import signals
from django.utils.translation import gettext as _
from django.contrib.auth import get_user_model; User = get_user_model()

class UserActivityAudit(models.Model):

    created_at = models.DateTimeField(auto_now_add = True)
    updated_at = models.DateTimeField(auto_now = True)

    user = models.ForeignKey(User, related_name="%(class)s")
    audit_key = models.CharField(max_length=254, db_index=True, unique=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    referrer = models.CharField(max_length=254)
    user_agent = models.TextField(blank=True)
    last_page = models.CharField(max_length=255)
    pages_viwed = models.PositiveIntegerField(default=0)
    force_logout = models.BooleanField(default=False)


    class Meta:
        unique_together = (("user", "audit_key"),)

    def __unicode__(self):
        return u"%s (%s)" % (self.user.username, self.ip_address)



