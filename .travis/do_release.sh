#!/usr/bin/env bash

echo '------------- Building Python Package -------------'
python setup.py sdist

echo '------------- Building Debian Package -------------'
./scripts/build_deb.sh

echo '------------ Publishing GitHub Release ------------'
./scripts/publish_github_release.sh

echo '------------- Publishing PyPi Release -------------'
./scripts/publish_pypi_release.sh