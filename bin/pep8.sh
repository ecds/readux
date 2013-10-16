#!/usr/bin/env bash
# It is a good idea to conform to pep8 standards so your code is clean and proper.
# Run this script often and corrent any errors that may find.
# You are after all as good as the code your write.
###################################################################################

echo -e "\nRunning: (pep8 --show-source --show-pep8 --select=errors --testsuite=.)\n\n"
pep8 --show-source --show-pep8 --select=errors --testsuite=./
echo -e "\n\n"

