#!/usr/bin/env bash
set -euo pipefail

project_dir=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
artifact_dir=${RESCUERELAY_DEMO_OUTPUT_DIR:-"$project_dir/artifacts"}
webm_path="$artifact_dir/rescue-relay-demo.webm"
mp4_path="$artifact_dir/rescue-relay-demo.mp4"

if ! command -v ffmpeg >/dev/null 2>&1 || ! command -v ffprobe >/dev/null 2>&1; then
  printf 'ffmpeg and ffprobe are required to create and validate the final MP4.\n' >&2
  exit 2
fi

mkdir -p "$artifact_dir"
(
  cd "$project_dir/frontend"
  RESCUERELAY_DEMO_VIDEO="$webm_path" npm run record:demo
)

ffmpeg -y -loglevel warning \
  -i "$webm_path" \
  -f lavfi -i anullsrc=channel_layout=stereo:sample_rate=48000 \
  -c:v libx264 -preset medium -crf 20 -pix_fmt yuv420p \
  -c:a aac -b:a 128k -shortest -movflags +faststart \
  "$mp4_path"

duration=$(ffprobe -v error -show_entries format=duration -of default=nw=1:nk=1 "$mp4_path")
printf 'Recorded caption-led demo: %s (%0.1f seconds)\n' "$mp4_path" "$duration"
