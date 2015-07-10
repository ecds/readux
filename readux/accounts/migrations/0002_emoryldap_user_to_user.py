# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations

# fields common to emory ldap user and auth user
common_fields = ['username', 'password', 'first_name', 'last_name',
   'email', 'is_staff', 'is_active', 'is_superuser']

def copy_user_to_user(a, b):
    # copy common fields, groups, and permissions from user a to user b
    for field in common_fields:
        # only set a field if it is empty
        # - should always be the case for users created by the migration,
        # and will avoid overwriting content for existing users
        if not getattr(b, field):
            setattr(b, field, getattr(a, field))
    for g in a.groups.all():
        b.groups.add(g)
    for perm in a.user_permissions.all():
        b.user_permissions.add(perm)


emoryldap_extra_fields = ['phone', 'dept_num', 'full_name', 'title',
    'employee_num', 'subdept_code', 'hr_id']

def migrate_ldap_users(apps, schema_editor):
    # get ldap user and standard auth user models
    ldap_user = apps.get_model('emory_ldap', 'EmoryLDAPUser')
    auth_user = apps.get_model('accounts', 'user')

    # for each ldap user, make sure there is an equivalent auth user
    for ldapuser in ldap_user.objects.all():
        user, created = auth_user.objects.get_or_create(username=ldapuser.username)
        copy_user_to_user(ldapuser, user)
        user.save()
        ldapuser.delete()

def unmigrate_ldap_users(apps, schema_editor):
    # depending on how the database was created, auth_user may not exist
    ldap_user = apps.get_model('emory_ldap', 'EmoryLDAPUser')
    auth_user = apps.get_model('accounts', 'user')

    # if both tables exist, just duplicate user objects
    for user in auth_user.objects.all():
        ldapuser, created = ldap_user.objects.get_or_create(username=user.username)
        copy_user_to_user(user, ldapuser)
        ldapuser.save()


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0001_initial'),
        ('emory_ldap', '0001_initial')
    ]

    operations = [
        migrations.RunPython(migrate_ldap_users,
            reverse_code=unmigrate_ldap_users, atomic=False)
    ]
