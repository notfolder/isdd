#!/usr/bin/env bash
# 使い方: bash measure/batch.sh <並列数> <コマンドを 1 行ずつ書いたファイル>
# 各行を順に、最大 <並列数> 本まで同時に実行する。ログは measure/results/batch-<n>.log
set -u
PAR="$1"; LIST="$2"
mkdir -p "$(dirname "$0")/results"
n=0
while IFS= read -r cmd; do
  [ -z "$cmd" ] && continue
  n=$((n+1))
  while [ "$(jobs -rp | wc -l)" -ge "$PAR" ]; do sleep 20; done
  echo "[$(date +%H:%M:%S)] start $n: $cmd"
  python3 -c 'import os,sys; os.setsid(); os.execvp("bash", ["bash","-c",sys.argv[1]])' "$cmd" > "$(dirname "$0")/results/batch-$n.log" 2>&1 &
done < "$LIST"
wait
echo "[$(date +%H:%M:%S)] all done"
