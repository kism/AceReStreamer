#!/usr/bin/env bash

cd test_site || exit 1

python3 -m http.server 8999 &
