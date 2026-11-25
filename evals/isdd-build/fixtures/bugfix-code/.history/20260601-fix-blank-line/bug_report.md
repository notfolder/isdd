# 不具合の記録

| 現象 | 再現の手順 | 期待する動き | 満たされていない既存の要件ID | 対応業務課題ID（RQ-BK-*） | 原因のある場所 | 原因 |
|---|---|---|---|---|---|---|
| "Hello, World!" のあとに空行が 1 行余分に出る | `python3 src/hello.py` を引数なしで実行する | "Hello, World!" を 1 行だけ表示する | `RQ-UI-HELLO-STDOUT-OUTPUT` | `RQ-BK-SHARED-VERIFICATION-SCRIPT` | コード | 設計書 4-1 は標準出力に "Hello, World!" を 1 行と定めているが、`src/hello.py` の `print_hello_world` が文字列の末尾に改行を足してから表示している |

## 再現するテスト

| 確かめる要件ID | 結ぶ DS-TS（既存） | テストの手順 | 期待される結果 |
|---|---|---|---|
| `RQ-UI-HELLO-STDOUT-OUTPUT` | `DS-TS-HELLO-OUTPUT-E2E-TS-VERIFY-HELLO-WORLD-OUTPUT` | `python3 src/hello.py` を引数なしで実行し、標準出力をそのまま（前後の空白を除かずに）受け取る | 標準出力が "Hello, World!" と改行 1 つだけである |
