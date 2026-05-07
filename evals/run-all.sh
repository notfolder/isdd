#!/usr/bin/env bash
set -u

repo_root="$(cd "$(dirname "$0")/.." && pwd)"
mode="${1:-mock}"

usage() {
    echo "usage: $0 [mock|real] [skill-name ...]" >&2
    echo "example: $0 real isdd-traceable-coding isdd-design" >&2
}

if ! command -v apm >/dev/null 2>&1; then
  echo "apm command not found" >&2
  exit 1
fi

echo "==> syncing skills with apm install"
if ! (cd "$repo_root" && apm install); then
  echo "apm install failed" >&2
  exit 1
fi

case "$mode" in
  mock)
    pattern="evals/*/eval.mock.yaml"
    ;;
  real)
    pattern="evals/*/eval.copilot.yaml"
    ;;
  *)
    usage
    exit 2
    ;;
esac

shift
selected_skills=("$@")

shopt -s nullglob
files=( $pattern )
shopt -u nullglob

if [[ ${#files[@]} -eq 0 ]]; then
    echo "no eval files found for mode: $mode" >&2
    exit 1
fi

failures=0
ran=0

print_skill_fingerprint() {
  local skill_name="$1"
  local skill_file="$repo_root/.agents/skills/$skill_name/SKILL.md"

  if [[ ! -f "$skill_file" ]]; then
    echo "[skill-fingerprint] skill file not found: $skill_file" >&2
    return 1
  fi

  # macOS: shasum -a 256, Linux: sha256sum
  if command -v shasum >/dev/null 2>&1; then
    local hash
    hash="$(shasum -a 256 "$skill_file" | awk '{print $1}')"
    echo "[skill-fingerprint] $skill_name sha256=$hash file=$skill_file"
    return 0
  fi

  if command -v sha256sum >/dev/null 2>&1; then
    local hash
    hash="$(sha256sum "$skill_file" | awk '{print $1}')"
    echo "[skill-fingerprint] $skill_name sha256=$hash file=$skill_file"
    return 0
  fi

  echo "[skill-fingerprint] sha256 command not found" >&2
  return 1
}

skill_is_selected() {
  local skill_name="$1"

  if [[ ${#selected_skills[@]} -eq 0 ]]; then
    return 0
  fi

  local selected
  for selected in "${selected_skills[@]}"; do
    if [[ "$selected" == "$skill_name" ]]; then
      return 0
    fi
  done

  return 1
}

for eval_file in "${files[@]}"; do
    eval_dir="$(dirname "$eval_file")"
  skill_name="$(basename "$eval_dir")"
    fixtures_dir="$eval_dir/fixtures"
  artifacts_dir="$eval_dir/artifacts"
  transcript_dir="$artifacts_dir/transcripts"
  temp_context_dir=""

  if ! skill_is_selected "$skill_name"; then
    continue
  fi

  mkdir -p "$transcript_dir"

    if ! print_skill_fingerprint "$skill_name"; then
      exit 1
    fi

    echo "==> running: $eval_file"
    if [[ -d "$fixtures_dir" ]]; then
    temp_context_dir="$(mktemp -d "${TMPDIR:-/tmp}/waza-context-${skill_name}-XXXXXX")"
    cp -R "$fixtures_dir"/. "$temp_context_dir"/

    if [[ -d "$repo_root/.agents" ]]; then
      ln -s "$repo_root/.agents" "$temp_context_dir/.agents"
    fi

    waza run "$eval_file" --context-dir "$temp_context_dir" --transcript-dir "$transcript_dir" --keep-workspace -v
    else
    waza run "$eval_file" --transcript-dir "$transcript_dir" --keep-workspace -v
    fi

    exit_code=$?
    if [[ -n "$temp_context_dir" && -d "$temp_context_dir" ]]; then
      rm -rf "$temp_context_dir"
    fi
    ran=$((ran + 1))
    if [[ $exit_code -ne 0 ]]; then
        failures=$((failures + 1))
        echo "failed: $eval_file (exit=$exit_code)" >&2
    fi
    echo
 done

  if [[ $ran -eq 0 ]]; then
    if [[ ${#selected_skills[@]} -gt 0 ]]; then
      echo "no eval files matched selected skills: ${selected_skills[*]}" >&2
    else
      echo "no eval files were executed" >&2
    fi
    exit 1
  fi

if [[ $failures -ne 0 ]]; then
    echo "completed with failures: $failures" >&2
    exit 1
fi

echo "all evaluations passed"
