#!/usr/bin/env bash

echo '------------- Building Python Package -------------'
python setup.py sdist

echo '------------- Building Debian Package -------------'
./scripts/build_deb.sh

echo '--------------- Publishing Release ----------------'
./scripts/publish_github_release.sh
