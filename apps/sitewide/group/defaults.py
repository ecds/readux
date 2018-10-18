##
# @license
# Copyright Neekware Inc. All Rights Reserved.
#
# Use of this source code is governed by an MIT-style license that can be
# found in the LICENSE file at http://neekware.com/license/MIT.html
###

# admin is like super user but with a bit less permissions
ADMIN_PERMISSIONS = {

    'sitewide': {       # app name
        'sitewide': (   # model name
            'admin',    # access to full admin menu
        )
    },

    'profiles': {    # app name
        'profile': (    # model name
            'add',      # add new user profile
            'change',   # change any data on user profile
            'delete',   # delete any non-superuser profile
            'read',     # read access to all user data
            'switch',   # switch to other users (similar to su command on *nix)
        )
    },

}

# is_staff is not used, so staff will get these perms.
STAFF_PERMISSIONS = {

    'sitewide': {       # app name
        'sitewide': (   # model name
            'staff',    # access to limited admin menu
        )
    },

    'profiles': {    # app name
        'profile': (    # model name
            'add',      # add new user profile
            'read',     # read full user data
            'update',   # update to public user data
        )
    },

}

AVAILABLE_GROUPS = {
    'admin': ADMIN_PERMISSIONS,
    'staff': STAFF_PERMISSIONS,
}
