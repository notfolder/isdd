#!/usr/bin/env bash
set -u

repo_root="$(cd "$(dirname "$0")/.." && pwd)"
mode="${1:-mock}"

# .env ファイルが存在する場合は読み込む（既存の環境変数は上書きしない）
env_file="$repo_root/.env"
if [[ -f "$env_file" ]]; then
    set -o allexport
    # shellcheck source=/dev/null
    source "$env_file"
    set +o allexport
    echo "[env] loaded: $env_file"
fi

usage() {
    echo "usage: $0 [mock|real|local] [skill-name ...]" >&2
    echo "example: $0 real isdd-traceable-coding isdd-design" >&2
    echo "         $0 local isdd-requirements  # LM Studio (http://127.0.0.1:1234) を使用" >&2
    echo "  環境変数: WAZA_LOCAL_LM_STUDIO_URL (デフォルト: http://127.0.0.1:1234/v1)" >&2
    echo "            WAZA_LOCAL_MODEL        (デフォルト: local-model)" >&2
}

if [[ ! -d "$repo_root/skills" ]]; then
  echo "skills directory not found: $repo_root/skills" >&2
  exit 1
fi

case "$mode" in
  mock)
    pattern="evals/*/eval.mock.yaml"
    local_mode=false
    ;;
  real)
    pattern="evals/*/eval.copilot.yaml"
    local_mode=false
    ;;
  local)
    # eval.copilot.yaml を使用し、LM Studio へのカスタムプロバイダー設定を注入する
    pattern="evals/*/eval.copilot.yaml"
    local_mode=true
    ;;
  *)
    usage
    exit 2
    ;;
esac

shift
selected_skills=("$@")

# localモード: LM Studio へ向けるカスタムプロバイダー環境変数を構築する
# COPILOT_BASE_URL はOpenAI互換エンドポイントとして Copilot SDK の BYOK 機能に渡される
lm_studio_url="${WAZA_LOCAL_LM_STUDIO_URL:-http://127.0.0.1:1234/v1}"
local_model="${WAZA_LOCAL_MODEL:-gemma-4-e4b-it-mlx}"

if [[ "$local_mode" == "true" ]]; then
    echo "[local-mode] LM Studio endpoint: $lm_studio_url (model: $local_model)"
    waza_run_env=(env
        COPILOT_PROVIDER_BASE_URL="$lm_studio_url"
        COPILOT_PROVIDER_TYPE=openai
        COPILOT_PROVIDER_WIRE_API=completions
        COPILOT_MODEL="$local_model"
    )
    waza_model_flag=(--model "$local_model")
else
    waza_run_env=()
    waza_model_flag=()
fi

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
  local skill_file="$repo_root/skills/$skill_name/SKILL.md"

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

# Check that task files: entries are complete and exist in context-dir.
# ERROR: skill: field is missing in eval yaml
# ERROR: any file under skills/{skill} or isdd-common is not listed
# ERROR: listed file does not exist in context-dir
check_task_files() {
  local skill_name="$1"
  local eval_dir="$2"
  local context_dir="$3"
  local has_error=0

  echo "[files-check] $skill_name"

  # 1. skill: field must exist in eval yaml
  local eval_yaml
  eval_yaml="$(ls "$eval_dir"/eval.*.yaml 2>/dev/null | head -1)"
  if [[ -z "$eval_yaml" ]] || ! grep -q "^skill:" "$eval_yaml"; then
    echo "  [ERROR] skill: field missing in $(basename "${eval_yaml:-eval.yaml}")" >&2
    has_error=1
  fi

  # Collect path: values only from files: sections.
  # files: entries use 4-space indent ("    - path:").
  # content_patterns entries use 8-space indent and must be excluded.
  local listed_paths
  listed_paths=$(grep -h "^    - path:" "$eval_dir/tasks/"*.yaml 2>/dev/null \
    | sed 's/^    - path:[[:space:]]*//' | sed 's/[[:space:]]*$//' | tr -d '"'"'")

  # 2. All files under skills/{skill} and isdd-common must be listed
  #    __pycache__, .pyc, .DS_Store files are excluded from the check
  for check_subdir in ".agents/skills/$skill_name" ".agents/skills/isdd-common"; do
    local full_dir="$repo_root/$check_subdir"
    [[ -d "$full_dir" ]] || continue
    while IFS= read -r full_path; do
      local rel_path="${full_path#$repo_root/}"
      if ! printf '%s\n' "$listed_paths" | grep -qxF "$rel_path"; then
        echo "  [ERROR] not listed: $rel_path" >&2
        has_error=1
      fi
    done < <(find "$full_dir" -type f -not -path "*/__pycache__/*" -not -name "*.pyc" -not -name ".DS_Store" | sort)
  done

  # 3. All listed files must exist in context-dir
  while IFS= read -r rel_path; do
    [[ -z "$rel_path" ]] && continue
    if [[ ! -f "$context_dir/$rel_path" ]]; then
      echo "  [ERROR] listed but not found in context-dir: $rel_path" >&2
      has_error=1
    fi
  done <<< "$listed_paths"

  [[ $has_error -eq 0 ]] && echo "  [OK]"
  return $has_error
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

    if [[ -d "$repo_root/skills" ]]; then
      mkdir -p "$temp_context_dir/.agents"
      cp -R "$repo_root/skills" "$temp_context_dir/.agents/skills"
    fi

    if ! check_task_files "$skill_name" "$eval_dir" "$temp_context_dir"; then
      echo "==> [files-check] fix files: entries above before running eval" >&2
      rm -rf "$temp_context_dir"
      failures=$((failures + 1))
      ran=$((ran + 1))
      continue
    fi

    "${waza_run_env[@]}" waza run "$eval_file" "${waza_model_flag[@]}" --context-dir "$temp_context_dir" --transcript-dir "$transcript_dir" --keep-workspace -v
    else
    "${waza_run_env[@]}" waza run "$eval_file" "${waza_model_flag[@]}" --transcript-dir "$transcript_dir" --keep-workspace -v
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
