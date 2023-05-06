#!/usr/bin/env bash

cd /home/buildbot/debian/apt

dpkg-scanpackages --arch amd64 pool/ > dists/develop/main/binary-amd64/Packages
cat dists/develop/main/binary-amd64/Packages | gzip -9 > dists/develop/main/binary-amd64/Packages.gz

