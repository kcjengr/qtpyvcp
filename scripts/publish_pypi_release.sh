#!/usr/bin/env bash

echo 'Installing twine... '
pip install twine

echo 'Uploading files to PyPi...'
twine upload \
    --username kcjengr \
    --password $PYPI_PASS \
    'dist/qtpyvcp*.tar.gz'
