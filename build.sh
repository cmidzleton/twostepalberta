#!/bin/sh
# Netlify runs this on every deploy: stamps today's date (Alberta time) into the "Last updated" spots.
set -e
TODAY=$(TZ=America/Edmonton date '+%B %-d, %Y')
sed -i -E "s#(<span class=\"updated\">)[^<]*#\1${TODAY}#g" index.html calgary/index.html
echo "Stamped last updated: ${TODAY}"
# Keep the sitemap's lastmod in step with the deploy date so Google sees fresh listings.
ISO=$(TZ=America/Edmonton date '+%Y-%m-%d')
sed -i -E "s#<lastmod>[^<]*</lastmod>#<lastmod>${ISO}</lastmod>#" sitemap.xml
echo "Stamped sitemap lastmod: ${ISO}"
# Rebuild the calendar feeds (dances.ics, calgary/dances.ics) from the confirmed listings. The committed copy is used if Python isn't there.
if command -v python3 >/dev/null 2>&1; then python3 make_ics.py; else echo "python3 not found, keeping committed dances.ics"; fi
