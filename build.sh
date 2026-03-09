#!/usr/bin/env bash
# exit on error
set -o errexit

# Install dependencies (cleaned UTF-8 version)
pip install -r requirements.txt

# Run Django commands
python manage.py collectstatic --no-input

# No standard migrations for MongoDB, but run anyway for system checks
# python manage.py migrate
