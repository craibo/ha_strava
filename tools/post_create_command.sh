#!/bin/bash

set -e

pip install -r requirements_dev.txt
pip install -r requirements_test.txt

pre-commit install
pre-commit install-hooks
