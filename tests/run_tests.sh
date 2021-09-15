#!/bin/bash

#remove cache data before testing
rm -rf ./cache/*

#build a test suite object which runs the tests in this folder
python -m unittest discover -v -p "test*.py"

VAL=$?

#remove cache data after testing
rm -rf ./cache/*

exit $VAL
