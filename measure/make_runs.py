#!/usr/bin/env python3
"""本番の実行コマンドを、乱数で並べ替えて出す（時間帯や負荷が群と重ならないようにする）。

使用方法: python3 measure/make_runs.py --task needfit --counts 6,6,6 --seed 20261123 [--stages 1] > measure/needfit/runs.txt
counts は バイブコーディング, 一文つき, isdd の回数。出したファイルを `bash measure/batch2.sh 4 <ファイル>` に渡す。
"""

import argparse
import random

parser = argparse.ArgumentParser()
parser.add_argument("--task", required=True)
parser.add_argument("--counts", required=True)
parser.add_argument("--seed", type=int, required=True)
parser.add_argument("--stages", default="1")
parser.add_argument("--contract", default=None)
parser.add_argument("--work", default="/Users/Shared/isdd-measure-work")
args = parser.parse_args()
n_control, n_ask, n_isdd = (int(x) for x in args.counts.split(","))
common = (f"--model claude-opus-5-5 --work {args.work} --task {args.task} --stages {args.stages} --responder measure/{args.task}/ledger.md "
          f"--max-rounds 20 --path-prefix /tmp/isdd-measure/bin" + (f" --contract {args.contract}" if args.contract else ""))
runs = [f"python3 measure/run.py --arm control --run {i} {common} --label {args.task}-control-opus-r{i}" for i in range(1, n_control + 1)]
runs += [f"python3 measure/run.py --arm control --ask-first --run {i} {common} --label {args.task}-ask-opus-r{i}" for i in range(1, n_ask + 1)]
runs += [f"python3 measure/run.py --arm isdd --run {i} {common} --label {args.task}-isdd-opus-r{i}" for i in range(1, n_isdd + 1)]
random.Random(args.seed).shuffle(runs)
print("\n".join(runs))
