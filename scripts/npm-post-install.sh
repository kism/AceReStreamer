#!/usr/bin/env sh

set -e

cp node_modules/hls.js/dist/hls.min.js acerestreamer/static/hls.min.js
cp node_modules/hls.js/dist/hls.min.js.map acerestreamer/static/hls.min.js.map
cp node_modules/xml-formatter/dist/browser/xml-formatter.js acerestreamer/static/xml-formatter.js
