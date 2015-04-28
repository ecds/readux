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
    auth_user = apps.get_model('auth', 'user')

    # depending on how the database was created, auth_user may not exist
    if 'auth_user' not in schema_editor.connection.introspection.table_names():
        print 'Moving emoryldap_user table to auth_user.'
        print 'emory_ldap should be removed from installed apps.'

        # if auth_user doesn't exist, rename the emory_ldap table to
        # auth_user and drop the unnecessary fields
        ldap_fields = ['id', 'password']
        # remove fields in ldap user not in auth user
        for field in ldap_user._meta.fields:
            ldap_fields.append(field.name)
            if field.name in emoryldap_extra_fields:
                schema_editor.remove_field(ldap_user, field)

        # rename the table
        schema_editor.alter_db_table(auth_user, ldap_user._meta.db_table,
            auth_user._meta.db_table)

        # add fields in auth user not in emory ldap
        for field in auth_user._meta.fields:
            if field.name == 'id':
                continue
            if field not in ldap_fields:
                schema_editor.add_field(auth_user, field)

    else:
    # if both tables exist, copy user information over

        # for each ldap user, make sure there is an equivalent auth user
        for ldapuser in ldap_user.objects.all():
            user, created = auth_user.objects.get_or_create(username=ldapuser.username)
            copy_user_to_user(ldapuser, user)
            user.save()
            ldapuser.delete()

def unmigrate_ldap_users(apps, schema_editor):
    # depending on how the database was created, auth_user may not exist
    ldap_user = apps.get_model('emory_ldap', 'EmoryLDAPUser')
    auth_user = apps.get_model('auth', 'user')

    # if we migrated by moving the table, then it won't exist, so undo the same way
    if 'emory_ldap_emoryldapuser' not in schema_editor.connection.introspection.table_names():

        schema_editor.alter_db_table(ldap_user, auth_user._meta.db_table,
            ldap_user._meta.db_table)

        # add extra fields ldap_user expects
        for field in ldap_user._meta.fields:
            if field.name in emoryldap_extra_fields:
                schema_editor.add_field(ldap_user, field)

        # don't worry about removing fields in auth but not in ldap
    else:
        # if both tables exist, just duplicate user objects
        for user in auth_user.objects.all():
            ldapuser, created = ldap_user.objects.get_or_create(username=user.username)
            copy_user_to_user(user, ldapuser)
            ldapuser.save()


class Migration(migrations.Migration):

    dependencies = [
        ('collection', '0002_load_image_defaults'),
        ('auth', '0001_initial'),
        ('contenttypes', '0001_initial'),
        ('emory_ldap', '0001_initial')
    ]

    operations = [
        migrations.RunPython(migrate_ldap_users,
            reverse_code=unmigrate_ldap_users, atomic=False)
    ]
