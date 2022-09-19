#!/bin/bash

set -e

python -m virtualenv env
source env/bin/activate

pip install -r requirements_dev.txt
pip install -r requirements_test.txt

tools/post_create_command.sh
