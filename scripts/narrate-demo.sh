#!/usr/bin/env bash
set -euo pipefail

project_dir=$(CDPATH='' cd -- "$(dirname -- "$0")/.." && pwd)
artifact_dir=${RESCUERELAY_DEMO_OUTPUT_DIR:-"$project_dir/artifacts"}
input_path=${RESCUERELAY_DEMO_INPUT:-"$artifact_dir/rescue-relay-demo.mp4"}
output_path=${RESCUERELAY_NARRATED_OUTPUT:-"$artifact_dir/rescue-relay-demo-narrated.mp4"}
voice=${RESCUERELAY_NARRATION_VOICE:-Samantha}
rate=${RESCUERELAY_NARRATION_RATE:-195}

for command_name in say ffmpeg ffprobe; do
  if ! command -v "$command_name" >/dev/null 2>&1; then
    printf '%s is required to create the narrated demo.\n' "$command_name" >&2
    exit 2
  fi
done

if [[ ! -f "$input_path" ]]; then
  printf 'Caption master not found: %s\nRun ./scripts/record-demo.sh first.\n' "$input_path" >&2
  exit 2
fi

if ! [[ "$rate" =~ ^[0-9]+$ ]] || (( rate < 120 || rate > 240 )); then
  printf 'RESCUERELAY_NARRATION_RATE must be an integer from 120 through 240.\n' >&2
  exit 2
fi

scratch_dir=$(mktemp -d "${TMPDIR:-/tmp}/rescue-relay-narration.XXXXXX")
trap 'rm -rf "$scratch_dir"' EXIT

starts_ms=(700 9000 25000 38000 53500 64500 76500 90500 101500 112500 125500 139000 152000)
texts=(
  "RescueRelay turns expiring food offers into accountable handoffs, while keeping every real-world commitment human-owned."
  "Food rescue coordinators repeatedly interpret donor messages, check pantry need and capacity, match pickup windows, draft outreach, and chase approval. Individually these tasks are small. Together, they consume the time that expiring food does not have."
  "One simulated inbox event starts the real Strands tool loop. RescueRelay claims a durable source identifier before execution, so exact retries cannot duplicate work and conflicting content fails closed."
  "The model orchestrates four tools in order: read offers, load partner constraints, optimize dispatches, then stage messages. Tested code, not model prose, owns quantities, capacity, receiving hours, distance, and partial allocations."
  "Every match links back to donor and pantry evidence. Donor text remains untrusted data, a default-deny hook permits only the safe tool surface, and no send capability exists."
  "The result is a complete operational plan with grounded pickup windows, visible confidence, reversible drafts, and a portable audit record that the recorder parses and validates."
  "Only two Harbor Market decisions interrupt the coordinator. First, approve the proposed split. The pickup still waits. Then approve the real commitment, and only now does its state become scheduled."
  "This boundary is stored in application state, not merely requested in a prompt. Declining either decision atomically declines the dispatch and closes its sibling decision."
  "The button uses fixtures for a stable demo. The same validated action accepts caller-supplied offers and partner constraints, persists them before acknowledgement, and rejects conflicting reuse."
  "Fast A P I and AgentCore share the event contract. A Strands agent chooses the workflow, a deterministic matcher produces the plan, and Sequel Lite records receipts, drafts, decisions, and impact."
  "Live mode swaps the replay adapter for an Amazon Bedrock model without moving correctness into a prompt. The repository includes an I A M-protected AgentCore entry point and an audited minimal deployment package."
  "In this reproducible scenario, four hundred twelve pounds are matched, representing an estimated two hundred eighty-six meals and thirty-eight coordinator minutes saved. Those are transparent demo estimates, not field-validated claims."
  "RescueRelay turns an inbox into an accountable handoff, so coordinators spend time on people instead of repetitive message triage."
)

video_duration=$(ffprobe -v error -show_entries format=duration -of default=nw=1:nk=1 "$input_path")
video_duration_ms=$(awk -v seconds="$video_duration" 'BEGIN { printf "%d", seconds * 1000 }')
ffmpeg_inputs=(-i "$input_path")
filter_parts=("[0:a]aresample=48000[base]")
mix_inputs="[base]"

for index in "${!texts[@]}"; do
  segment_path="$scratch_dir/segment-$(printf '%02d' "$index").aiff"
  say -v "$voice" -r "$rate" -o "$segment_path" "${texts[$index]}"
  segment_duration=$(ffprobe -v error -show_entries format=duration -of default=nw=1:nk=1 "$segment_path")
  segment_duration_ms=$(awk -v seconds="$segment_duration" 'BEGIN { printf "%d", seconds * 1000 }')
  if (( index + 1 < ${#starts_ms[@]} )); then
    next_start_ms=${starts_ms[$((index + 1))]}
  else
    next_start_ms=$video_duration_ms
  fi
  available_ms=$((next_start_ms - starts_ms[index] - 250))
  if (( segment_duration_ms > available_ms )); then
    printf 'Narration segment %d is %d ms but only %d ms are available. Increase RESCUERELAY_NARRATION_RATE.\n' \
      "$((index + 1))" "$segment_duration_ms" "$available_ms" >&2
    exit 3
  fi
  input_index=$((index + 1))
  label="voice$index"
  ffmpeg_inputs+=(-i "$segment_path")
  filter_parts+=("[$input_index:a]aresample=48000,adelay=${starts_ms[$index]}:all=1[$label]")
  mix_inputs+="[$label]"
done

filter=$(IFS=';'; printf '%s' "${filter_parts[*]}")
filter+=";${mix_inputs}amix=inputs=$((${#texts[@]} + 1)):normalize=0:dropout_transition=0,loudnorm=I=-16:LRA=7:TP=-1.5[mix]"

ffmpeg -y -loglevel error \
  "${ffmpeg_inputs[@]}" \
  -filter_complex "$filter" \
  -map 0:v:0 -map '[mix]' \
  -c:v copy -c:a aac -b:a 160k -ar 48000 -shortest -movflags +faststart \
  "$output_path"

narrated_duration=$(ffprobe -v error -show_entries format=duration -of default=nw=1:nk=1 "$output_path")
printf 'Narrated demo: %s (%0.1f seconds, voice=%s, rate=%s)\n' \
  "$output_path" "$narrated_duration" "$voice" "$rate"
