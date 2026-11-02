#!/bin/sh
# Netlify runs this on every deploy: stamps today's date (Alberta time) into the "Last updated" spots.
set -e
TODAY=$(TZ=America/Edmonton date '+%B %-d, %Y')
sed -i -E "s#(<span class=\"updated\">)[^<]*#\1${TODAY}#g" index.html
echo "Stamped last updated: ${TODAY}"
