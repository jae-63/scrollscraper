#!/bin/bash
# Recover the bible.ort.org Exodus 40 RealAudio files that the Wayback Machine captured (see issue #7)
# and convert them to the same format as local_ort_mp3s (16 kHz, stereo, 48 kbps MP3).
# The .ra files contain a "dnet" (AC3) stream; ffmpeg decodes it. A "corrupt packet" warning on the
# final packet is expected and harmless.
set -e
OUT=${1:-$(dirname "$0")/../../misc_mp3s/t2/40/from_wayback}
TMP=$(mktemp -d); mkdir -p "$OUT"
curl -s "https://web.archive.org/cdx/search/cdx?url=bible.ort.org/webmedia/t2/40*&output=json&filter=statuscode:200&collapse=urlkey&fl=timestamp,original,mimetype" |
  python3 -c "import json,sys; [print(r[0],r[1]) for r in json.load(sys.stdin)[1:] if 'audio' in r[2]]" |
  while read ts url; do
    f=$(basename "$url")
    curl -sL -o "$TMP/$f" "https://web.archive.org/web/${ts}id_/$url"
    ffmpeg -hide_banner -loglevel error -y -i "$TMP/$f" -ar 16000 -ac 2 -b:a 48k "$OUT/${f%.ra}.mp3" || true
    echo "$f -> $OUT/${f%.ra}.mp3"
  done
rm -rf "$TMP"
