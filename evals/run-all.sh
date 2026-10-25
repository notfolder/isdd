#!/usr/bin/env bash
set -u

repo_root="$(cd "$(dirname "$0")/.." && pwd)"
# program グレーダー（evals/_graders/isdd_grade.py）がリポジトリの場所を知るために使う
export ISDD_REPO_ROOT="$repo_root"
mode="${1:-mock}"

# .env ファイルが存在する場合は読み込む（既に設定済みの環境変数は上書きしない。
# 例: WAZA_CLAUDE_MODEL=claude-haiku-5-5 bash evals/run-all.sh claude は .env の値より優先される）
env_file="$repo_root/.env"
if [[ -f "$env_file" ]]; then
    while IFS= read -r line || [[ -n "$line" ]]; do
        # 空行・コメント・KEY=VALUE 以外は読み飛ばす
        [[ "$line" =~ ^[[:space:]]*# ]] && continue
        [[ "$line" =~ ^[[:space:]]*$ ]] && continue
        [[ "$line" =~ ^[A-Za-z_][A-Za-z0-9_]*= ]] || continue
        key="${line%%=*}"
        if [[ -z "${!key+x}" ]]; then
            eval "export $line"
        fi
    done < "$env_file"
    echo "[env] loaded: ${env_file} (設定済みの変数は上書きしない)"
fi

usage() {
    echo "usage: $0 [mock|real|local|claude] [skill-name ...]" >&2
    echo "example: $0 real isdd-traceable-coding isdd-design" >&2
    echo "         $0 local isdd-requirements  # LM Studio (http://127.0.0.1:1234) を使用" >&2
    echo "         $0 claude                  # Anthropic API (BYOK)。Haiku で実行し、失敗分だけ同じモデルで 1 回再試行（昇格はしない）" >&2
    echo "  環境変数: WAZA_LOCAL_LM_STUDIO_URL (デフォルト: http://127.0.0.1:1234/v1)" >&2
    echo "            WAZA_LOCAL_MODEL        (デフォルト: gemma-4-e4b-it-mlx)" >&2
    echo "            WAZA_LOCAL_TIMEOUT_SCALE (デフォルト: 10。local モードで timeout_seconds に掛ける倍率)" >&2
    echo "            ANTHROPIC_API_KEY       (claude モードで必須)" >&2
    echo "            WAZA_CLAUDE_MODEL       (デフォルト: claude-haiku-5-5)" >&2
    echo "            WAZA_BIN                (デフォルト: waza。フォーク版を使うときに指定)" >&2
    echo "            COPILOT_CLI_PATH            (claude モード。未指定なら evals/.copilot-cli/ の CLI を自動使用)" >&2
}

if [[ ! -d "$repo_root/skills" ]]; then
  echo "skills directory not found: $repo_root/skills" >&2
  exit 1
fi

# 各スキルの references/ と scripts/ が shared/ の正本と一致しているかを確かめる。
# 一致していないと、公開・install.sh で配る中身と eval で試す中身が食い違うため、止める。
if ! python3 "$repo_root/tools/build_skills.py" --check; then
  echo "==> skills/ の複製が shared/ と一致しません。python3 tools/build_skills.py を実行してから再実行してください" >&2
  exit 1
fi

claude_mode=false
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
  claude)
    # eval.copilot.yaml を使用し、Copilot SDK の BYOK で Anthropic API を呼ぶ
    pattern="evals/*/eval.copilot.yaml"
    local_mode=false
    claude_mode=true
    ;;
  *)
    usage
    exit 2
    ;;
esac

waza_bin="${WAZA_BIN:-waza}"

shift
selected_skills=("$@")

# localモード: LM Studio へ向けるカスタムプロバイダー環境変数を構築する
# COPILOT_BASE_URL はOpenAI互換エンドポイントとして Copilot SDK の BYOK 機能に渡される
lm_studio_url="${WAZA_LOCAL_LM_STUDIO_URL:-http://127.0.0.1:1234/v1}"
local_model="${WAZA_LOCAL_MODEL:-gemma-4-e4b-it-mlx}"
# eval.copilot.yaml の timeout_seconds は Claude の実測の約 3 倍（10〜20 分）に設定してある。
# ローカルモデルは遅いので、local モードではこの倍率を掛けた一時ファイルで実行する
local_timeout_scale="${WAZA_LOCAL_TIMEOUT_SCALE:-10}"

waza_run_env=()
waza_model_flag=()

if [[ "$local_mode" == "true" ]]; then
    echo "[local-mode] LM Studio endpoint: $lm_studio_url (model: $local_model)"
    waza_run_env=(env
        COPILOT_PROVIDER_BASE_URL="$lm_studio_url"
        COPILOT_PROVIDER_TYPE=openai
        COPILOT_PROVIDER_WIRE_API=completions
        COPILOT_MODEL="$local_model"
    )
    waza_model_flag=(--model "$local_model")
fi

# claudeモード: Anthropic API を BYOK で使う。Haiku で 1 回目 → 失敗なら同じモデルで 1 回だけ再試行。
# 強いモデルへの昇格はしない。Haiku で落ちたらスキルの質の問題として SKILL.md を直す（2026-10-17 の運用方針）。
# 旧変数名 WAZA_CLAUDE_MODEL_PRIMARY も読む（.env の互換のため）。
claude_model="${WAZA_CLAUDE_MODEL:-${WAZA_CLAUDE_MODEL_PRIMARY:-claude-haiku-5-5}}"
if [[ "$claude_mode" == "true" ]]; then
    if [[ -z "${ANTHROPIC_API_KEY:-}" ]]; then
        echo "claude モードには ANTHROPIC_API_KEY が必要です（.env に置くか環境変数で渡す）" >&2
        exit 2
    fi
    # waza 同梱の Copilot ランタイム（1.0.85）は Haiku 5.5 に旧式の思考設定を送って 400 になるため、
    # evals/install-copilot-cli.sh で入れた新しい CLI があればそれを使う（COPILOT_CLI_PATH の明示指定が優先）
    if [[ -z "${COPILOT_CLI_PATH:-}" ]]; then
        local_cli="$(ls -d "$repo_root"/evals/.copilot-cli/node_modules/@github/copilot-*/copilot 2>/dev/null | head -1)"
        if [[ -n "$local_cli" && -x "$local_cli" ]]; then
            export COPILOT_CLI_PATH="$local_cli"
        else
            echo "[claude-mode] 注意: 新しい Copilot CLI が未導入です。Haiku 5.5 は waza 同梱ランタイムでは動きません。bash evals/install-copilot-cli.sh を実行してください" >&2
        fi
    fi
    echo "[claude-mode] model: ${claude_model} (1 回目と再試行とも。昇格なし) / copilot cli: ${COPILOT_CLI_PATH:-(waza 同梱)}"
fi

# claude モード用: 指定モデルで waza を 1 回実行する環境変数を組み立てる
claude_env_for() {
    local model="$1"
    printf '%s\n' env \
        COPILOT_PROVIDER_TYPE=anthropic \
        COPILOT_BASE_URL=https://api.anthropic.com \
        COPILOT_API_KEY="$ANTHROPIC_API_KEY" \
        COPILOT_MODEL="$model"
}

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
# ERROR: any file of a skill whose SKILL.md is listed is not listed (skills/{skill}/evals is excluded)
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

  # 2. For every skill whose SKILL.md is listed, all files under skills/{skill} must be listed
  #    (evals/, __pycache__, .pyc, .DS_Store are excluded from the check)
  local listed_skills
  listed_skills=$(printf '%s\n' "$listed_paths" | sed -n 's#^\.agents/skills/\([^/]*\)/SKILL\.md$#\1#p' | sort -u)
  if ! printf '%s\n' "$listed_skills" | grep -qxF "$skill_name"; then
    echo "  [ERROR] not listed: .agents/skills/$skill_name/SKILL.md" >&2
    has_error=1
  fi
  local listed_skill
  while IFS= read -r listed_skill; do
    [[ -z "$listed_skill" ]] && continue
    local full_dir="$repo_root/skills/$listed_skill"
    if [[ ! -d "$full_dir" ]]; then
      echo "  [ERROR] skill not found: skills/$listed_skill" >&2
      has_error=1
      continue
    fi
    while IFS= read -r full_path; do
      local rel_path=".agents/skills/$listed_skill/${full_path#$full_dir/}"
      if ! printf '%s\n' "$listed_paths" | grep -qxF "$rel_path"; then
        echo "  [ERROR] not listed: $rel_path" >&2
        has_error=1
      fi
    done < <(find "$full_dir" -type f -not -path "$full_dir/evals/*" -not -path "*/__pycache__/*" -not -name "*.pyc" -not -name ".DS_Store" | sort)
  done <<< "$listed_skills"

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

# 結果表（claude モード用）。bash 3.2 に合わせて連想配列は使わない
summary_skills=()
summary_first=()
summary_retry=()

# 1 回分の waza 実行。引数: eval_file skill_name fixtures_dir transcript_dir [model]
run_one() {
  local eval_file="$1" skill_name="$2" fixtures_dir="$3" transcript_dir="$4" model="${5:-}"
  local temp_context_dir="" exit_code=0
  local run_env=() model_flag=()

  if [[ "$claude_mode" == "true" ]]; then
    # bash 3.2 では mapfile が無いため while read で配列化する
    while IFS= read -r line; do run_env+=("$line"); done < <(claude_env_for "$model")
    model_flag=(--model "$model")
  else
    run_env=(${waza_run_env[@]+"${waza_run_env[@]}"})
    model_flag=(${waza_model_flag[@]+"${waza_model_flag[@]}"})
  fi

  mkdir -p "$transcript_dir"

  # local モードでは timeout_seconds を倍率で伸ばした一時 eval ファイルを同じディレクトリに作る
  # （inputs.context.fixture は eval ファイルのディレクトリからの相対パスなので、同じディレクトリに置く）。
  # タスク側の timeout_seconds は eval ファイルの値より優先されるため、tasks/*.yaml も倍率を掛けた
  # 一時コピーを作り、一時 eval ファイルの tasks: をそちらへ向ける
  local eval_to_run="$eval_file" tmp_eval="" tmp_tasks=""
  if [[ "$local_mode" == "true" ]]; then
    local eval_dir_of_file tmp_tasks_name scale_awk task_file
    eval_dir_of_file="$(dirname "$eval_file")"
    tmp_eval="$eval_dir_of_file/.eval.local.$$.yaml"
    tmp_tasks_name=".tasks.local.$$"
    tmp_tasks="$eval_dir_of_file/$tmp_tasks_name"
    scale_awk='/^[[:space:]]*timeout_seconds:[[:space:]]*[0-9]+/ { sub(/[0-9]+/, int($2 * s)) } { print }'
    mkdir -p "$tmp_tasks"
    for task_file in "$eval_dir_of_file"/tasks/*.yaml; do
      [[ -f "$task_file" ]] || continue
      awk -v s="$local_timeout_scale" "$scale_awk" "$task_file" > "$tmp_tasks/$(basename "$task_file")"
    done
    awk -v s="$local_timeout_scale" -v d="$tmp_tasks_name/" '
      /^[[:space:]]*-[[:space:]]*tasks\// { sub(/tasks\//, d) }
      '"$scale_awk" "$eval_file" > "$tmp_eval"
    eval_to_run="$tmp_eval"
    echo "[local-mode] timeout_seconds を ${local_timeout_scale} 倍にした一時ファイルで実行: ${tmp_eval}（タスク: ${tmp_tasks}）"
  fi

  if [[ -d "$fixtures_dir" ]]; then
    temp_context_dir="$(mktemp -d "${TMPDIR:-/tmp}/waza-context-${skill_name}-XXXXXX")"
    cp -R "$fixtures_dir"/. "$temp_context_dir"/

    if [[ -d "$repo_root/skills" ]]; then
      mkdir -p "$temp_context_dir/.agents"
      cp -R "$repo_root/skills" "$temp_context_dir/.agents/skills"
    fi

    if ! check_task_files "$skill_name" "$(dirname "$eval_file")" "$temp_context_dir"; then
      echo "==> [files-check] fix files: entries above before running eval" >&2
      rm -rf "$temp_context_dir"
      [[ -n "$tmp_eval" ]] && rm -f "$tmp_eval"
      [[ -n "$tmp_tasks" ]] && rm -rf "$tmp_tasks"
      return 3
    fi

    ${run_env[@]+"${run_env[@]}"} "$waza_bin" run "$eval_to_run" ${model_flag[@]+"${model_flag[@]}"} --context-dir "$temp_context_dir" --transcript-dir "$transcript_dir" --keep-workspace -v
    exit_code=$?
    rm -rf "$temp_context_dir"
  else
    ${run_env[@]+"${run_env[@]}"} "$waza_bin" run "$eval_to_run" ${model_flag[@]+"${model_flag[@]}"} --transcript-dir "$transcript_dir" --keep-workspace -v
    exit_code=$?
  fi
  [[ -n "$tmp_eval" ]] && rm -f "$tmp_eval"
  [[ -n "$tmp_tasks" ]] && rm -rf "$tmp_tasks"
  return $exit_code
}

for eval_file in "${files[@]}"; do
  eval_dir="$(dirname "$eval_file")"
  skill_name="$(basename "$eval_dir")"
  fixtures_dir="$eval_dir/fixtures"
  artifacts_dir="$eval_dir/artifacts"
  transcript_dir="$artifacts_dir/transcripts"

  if ! skill_is_selected "$skill_name"; then
    continue
  fi

  if ! print_skill_fingerprint "$skill_name"; then
    exit 1
  fi

  echo "==> running: $eval_file"
  ran=$((ran + 1))

  if [[ "$claude_mode" != "true" ]]; then
    run_one "$eval_file" "$skill_name" "$fixtures_dir" "$transcript_dir"
    exit_code=$?
    if [[ $exit_code -ne 0 ]]; then
      failures=$((failures + 1))
      echo "failed: $eval_file (exit=$exit_code)" >&2
    fi
    echo
    continue
  fi

  # claude モード: 1 回目 → 失敗なら同じモデルで 1 回だけ再試行。昇格はしない
  first="FAIL"; retry="-"
  echo "==> [claude-mode] attempt 1: $claude_model"
  run_one "$eval_file" "$skill_name" "$fixtures_dir" "$transcript_dir/$claude_model/attempt-1" "$claude_model"
  exit_code=$?
  if [[ $exit_code -eq 0 ]]; then
    first="PASS"
  elif [[ $exit_code -eq 3 ]]; then
    first="FILES-ERROR"
  else
    echo "==> [claude-mode] attempt 2 (retry): $claude_model"
    run_one "$eval_file" "$skill_name" "$fixtures_dir" "$transcript_dir/$claude_model/attempt-2" "$claude_model"
    exit_code=$?
    if [[ $exit_code -eq 0 ]]; then retry="PASS"; else retry="FAIL"; fi
  fi

  summary_skills+=("$skill_name")
  summary_first+=("$first")
  summary_retry+=("$retry")

  if [[ $exit_code -ne 0 ]]; then
    failures=$((failures + 1))
    echo "failed: $eval_file (exit=$exit_code)" >&2
  fi
  echo
done

if [[ "$claude_mode" == "true" && ${#summary_skills[@]} -gt 0 ]]; then
  echo "==> [claude-mode] 結果表（モデル: ${claude_model}）"
  printf '| %-36s | %-11s | %-6s |\n' "skill" "1回目" "再試行"
  printf '|%s|%s|%s|\n' "--------------------------------------" "-------------" "--------"
  for i in "${!summary_skills[@]}"; do
    printf '| %-36s | %-11s | %-6s |\n' "${summary_skills[$i]}" "${summary_first[$i]}" "${summary_retry[$i]}"
  done
  echo "  1回目が FAIL のスキルは、再試行で通ってもスキルの質の問題として SKILL.md を直す（昇格による救済はしない）"
  echo
fi

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
