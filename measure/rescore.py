#!/usr/bin/env python3
"""隠しテストを直した後に、results/<label>/ の各段を採点し直す。段の snapshot があればそれを、無ければ作業ディレクトリの最終状態を使う。

  python3 measure/rescore.py --work <作業の親> [--labels isdd-r1,control-r1,...] [--note <文>]
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--work", required=True)
    parser.add_argument("--labels", default=None)
    parser.add_argument("--note", default="隠しテストを直して採点し直した")
    args = parser.parse_args()
    labels = args.labels.split(",") if args.labels else sorted(p.name for p in (HERE / "results").iterdir() if (p / "summary.json").exists())
    for label in labels:
        results_dir = HERE / "results" / label
        summary_path = results_dir / "summary.json"
        d = json.loads(summary_path.read_text(encoding="utf-8"))
        for st in sorted(d["stages"], key=int):
            snap = results_dir / f"snapshot-stage{st}"
            app = snap if snap.exists() else Path(args.work) / label
            out_json = results_dir / f"stage{st}.json"
            cmd = [sys.executable, str(HERE / "score.py"), "--app", str(app), "--stage", st, "--out", str(out_json)]
            if not snap.exists():
                cmd.append("--skip-setup")
            subprocess.run(cmd, check=False)
            sc = json.loads(out_json.read_text(encoding="utf-8"))
            info = d["stages"][st]
            info.setdefault("original", {"passed": info.get("passed"), "total": info.get("total"), "tests": info.get("tests")})
            info.update({"passed": sc["passed"], "total": sc["total"], "tests": sc["tests"], "overbuild": sc.get("overbuild"),
                         "scored_from": "snapshot" if snap.exists() else "final_state"})
            prev = d["stages"].get(str(int(st) - 1))
            if prev and prev.get("tests"):
                info["regressions"] = sorted(t for t, v in prev["tests"].items() if v == "pass" and sc["tests"].get(t) not in (None, "pass"))
            summary_path.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")
        d["note"] = args.note
        summary_path.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"[{label}] " + ", ".join(f"stage {st}: {d['stages'][st]['passed']}/{d['stages'][st]['total']}" for st in sorted(d['stages'], key=int)), flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
