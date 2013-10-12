import os
import sys
import random
import logging
import resource
import progressbar
from optparse import make_option
from random import randint, choice
from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils.translation import ugettext as _
from django.core.management import call_command
from django.contrib.auth import get_user_model; User = get_user_model()

from uuslug import slugify
from ... import defaults
from profileware import listeners # need to load this so signals are intercepted in this commands context

logger = logging.getLogger("testware.cmd.createusers")

class Command(BaseCommand):
    cmd_name = "Createusers"
    help = "usage: %prog [--overwrite] \n\tThis command creats test users in debug mode"

    option_list = BaseCommand.option_list + (
        make_option('-o', '--overwrite', action='store_true', default=False,
            help='Overwrite any locally modified data with the new dowloaded data.'
        ),
        make_option('-p', '--purge', action='store_true', default=False,
            help='Remove all users from db.'
        ),
    )


    def handle(self, *args, **options):
        self.options = options
        # if not getattr(settings, "DEBUG", True):
        #     return

        class MemoryUsageWidget(progressbar.ProgressBarWidget):
            def update(self, pbar):
                return '{0} kB'.format(str(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss).rjust(8))

        self.widgets = [
            '{0}|RAM usage:'.format("|Running:  {0}".format((self.cmd_name[:10] + (self.cmd_name[10:] and '..')).rjust(12))),
            MemoryUsageWidget(),
            '|',
            progressbar.ETA(),
            '|Done:',
            progressbar.Percentage(),
            progressbar.Bar(),
        ]

        if self.options['purge']:
            self.purge_users()
        else:
            if not self.is_geo_loaded():
                return
            return self.create_users()


    def create_users(self):
        progress = progressbar.ProgressBar(maxval=len(defaults.TESTWARE_USER_NAME_OPTIONS), widgets=self.widgets)
        count = 0
        # import pdb; pdb.set_trace()
        for name in defaults.TESTWARE_USER_NAME_OPTIONS:
            count += 1; progress.update(count)
            first_name, last_name = name
            username = slugify(first_name)
            email = '{0}@{1}'.format(username, defaults.TESTWARE_EMAIL_DOMAIN_NAME)
            u, created = User.objects.get_or_create(username=username)
            if not created and not self.options['overwrite']:
                continue
            u.email = email
            u.first_name = first_name
            u.last_name = last_name
            u.set_password(defaults.TESTWARE_TEMP_PASS)
            u.save()
            p = u.profile
            p.first_name, p.last_name = name # this is automatic for users created through a request
            p.personal_about = '{0} {1} {2}'.format(p.first_name, defaults.TESTWARE_LOREM_IPSUM, p.last_name)
            p.save()
            logger.debug(_('Created User {0} {1}').format(p.first_name, p.last_name))

    def purge_users(self):
        """ Remove all non superuser `test` Users """

        User.objects.filter(is_superuser=False).delete()
        SocialNetworkProfile.objects.filter(user__is_superuser=False).delete()





