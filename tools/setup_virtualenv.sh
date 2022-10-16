#!/bin/bash

set -e

python -m virtualenv env
source env/bin/activate

tools/post_create_command.sh
