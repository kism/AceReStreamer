#!/usr/bin/env bash


cd tests/test_sites || exit 1



PORT=8999
HOST="http://localhost:$PORT"

echo "Paths for test sites:"

find . -type f | sort | sed "s|^\.|$HOST|"

echo
echo "Starting web server on port $PORT"

python3 -m http.server $PORT
