#!/usr/bin/env bash

echo 'Installing twine... '
pip install twine

echo 'Uploading files to PyPi...'
twine upload \
    --username kcjengr \
    --password $PYPI_PASS \
    --comment "This is a test comment for the QtPyVCP $TRAVIS_TAG release." \
    'dist/qtpyvcp*.tar.gz'
