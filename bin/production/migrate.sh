#!/bin/bash
. "`dirname $0`"/common.sh

# Running as root
##############################################
if [ -z "$*" ]; then
    echo "Missing username"
    echo "Example: command <username>"
    echo ""
    exit 0
fi
ADMIN_USER=$1

export -f secrets_update
export -f project_migrate
export -f server_restart

echo -e "\nPlease enter the password for the admin user ($ADMIN_USER)."

su $ADMIN_USER -c '
echo -e "**** Updating secrets for neekware.io ****\n"
bash -c secrets_update
echo -e "**** Migrate project for neekware.io ****\n"
bash -c project_migrate
echo -e "**** Restart web server for neekware.io ****\n"
bash -c server_restart
echo -e "Done!\n"
'
