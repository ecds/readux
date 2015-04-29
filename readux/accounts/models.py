from django.contrib.auth.models import AbstractUser


## NOTE: This custom local user is a unmodified extension of Django's
# default auth.User model with standard user db table configured.
# It is here ONLY to support migrating out of the eullocal emory_ldap custom
# model user back to the standard django auth.User.  This model is intended
# to ensure the auth_user table exists and to allow for managing the migration
# from emory_ldap accounts to user accounts within the readux application.
# It should be possible to remove readux.accounts in the next release
# after the migration is complete.
class User(AbstractUser):
    class Meta:
        db_table = 'auth_user'
