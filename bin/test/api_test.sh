#!/usr/bin/env bash

##
# @license
# Copyright Neekware Inc. All Rights Reserved.
#
# Use of this source code is governed by an MIT-style license that can be
# found in the LICENSE file at http://neekware.com/license/MIT.html
###

DEFAULT_TESTS="
api_v1.tests.test_generics
api_v1.tests.test_profiles
api_v1.tests.test_throttles
"

# Clean up tests in the DEFAULT_TESTS to give more options
####################################################################
TEST_ARRAY=()
function tests_cleanup(){
    for test in $DEFAULT_TESTS; do
        tokens=$(echo $test|awk -F. '{for (i=1;i<=NF;i++)print $i}')
        module=''
        for token in $tokens; do
            if [[ -z "$module" ]]; then
                module=$token
            else
                module=$module.$token
            fi
            if grep -qv ' '$module' ' <<< ${TEST_ARRAY[*]}; then
                TEST_ARRAY+=($module)
            fi
        done
    done
}


# Show available tests
####################################################################
function tests_show(){
    tests_cleanup
    echo -e "\nAvailable Tests\n===================================="
    for test in ${TEST_ARRAY[*]}; do
        echo $test
    done
    echo -e "\n"
}


# Run a single given test
####################################################################
function tests_run_single_test(){
    echo -e "==================================================="
    echo -e "Testing: ( $1 )"
    echo -e "==================================================="
    'bin/test/manage.py' test $1 || exit 1
    echo -e "\n"
}


# Run one or more tests
####################################################################
multiple_tests=''
function tests_run_multiple(){
    tests_cleanup
    if [ -z "$multiple_tests" ]; then
        echo -e "\nError: No test to run.\n"
        test_show_usage
        exit 1
    fi
    VALID_TESTS=()
    for test in $multiple_tests; do
        if grep -q $test <<< ${TEST_ARRAY[*]}; then
            if grep -qv $test <<< ${VALID_TESTS[*]}; then
                VALID_TESTS+=($test)
            fi
        else
            echo -e "\nError: Invalid test: ( $test )\n"
            exit 1
        fi
    done

    for test in ${VALID_TESTS[*]}; do
        tests_run_single_test $test || exit 1
    done
}


# Run all tests found in DEFAULT_TESTS
####################################################################
function tests_run_all(){
    for test in $DEFAULT_TESTS; do
        echo -e "==================================================="
        echo -e "Testing: ( $test )"
        echo -e "==================================================="

        'bin/test/manage.py' test ${test} || exit 1

        echo -e "\n"
    done
}

function test_show_usage(){
cat << EOF
Usage: $0 options

This script runs single, multiple or all test(s) in the current project.

OPTIONS:
   -h Show this message
   -s Show all available tests
   -a Run all available tests
   -t <test1> <test2> Run specific test(s)
EOF
}

while getopts "hsat" OPTION; do
    case "$OPTION" in
    h)
        test_show_usage
        exit 0
        ;;
    s)
        tests_show
        exit 0
        ;;
    a)
        tests_run_all
        exit $?
        ;;
    t)
        shift $((OPTIND-1))
        multiple_tests=$@
        tests_run_multiple
        exit $?
        ;;
  esac
done

test_show_usage
