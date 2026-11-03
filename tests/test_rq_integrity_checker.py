"""rq_integrity_checker.py の単体テスト"""

import unittest

from helpers import TempDirMixin, run_script, write

GOOD = """
| RQ-BZ-ID | 業務名 |
|---|---|
| `RQ-BZ-HELLO-CHECK` | 動作確認 |

| RQ-BK-ID | 業務課題 | 対象業務 |
|---|---|---|
| `RQ-BK-SHARED-CHECK-SCRIPT` | 共通の確認手段を用意する | `RQ-BZ-HELLO-CHECK` |

| RQ-ID | 機能名 | 対応業務課題ID |
|---|---|---|
| `RQ-FT-PRINT-HELLO` | 出力 | `RQ-BK-SHARED-CHECK-SCRIPT` |
| `RQ-EF-SOFT-SAVING-CHECK` | 工数削減 | `RQ-BK-SHARED-CHECK-SCRIPT` |

## 7. テスト用利用シナリオ

| RQ-ID | テスト目的 | 前提条件 | テスト手順 | 期待される結果 | 検証する要件ID | 対応業務課題ID（RQ-BK-*） |
|---|---|---|---|---|---|---|
| `RQ-TS-VERIFY-HELLO` | 出力の確認 | 無し | 実行する | Hello が出る | `RQ-FT-PRINT-HELLO` | `RQ-BK-SHARED-CHECK-SCRIPT` |
"""


class RqIntegrityCheckerTest(TempDirMixin, unittest.TestCase):
    def test_valid_document_passes(self):
        path = write(self.tmp, "req.md", GOOD)
        code, out = run_script("rq_integrity_checker.py", [str(path)])
        self.assertEqual(code, 0, out)
        self.assertIn("全てのチェックに合格しました", out)

    def test_requirement_without_bk_fails(self):
        path = write(self.tmp, "req.md", GOOD + "\n| `RQ-NF-RESPONSE-1S` | 応答 1 秒 | |\n")
        code, out = run_script("rq_integrity_checker.py", [str(path)])
        self.assertEqual(code, 1, out)
        self.assertIn("RQ-NF-RESPONSE-1S", out)

    def test_orphan_bk_fails(self):
        path = write(self.tmp, "req.md", GOOD + "\n| `RQ-BK-UNUSED-THEME` | 使われない課題 | `RQ-BZ-HELLO-CHECK` |\n")
        code, out = run_script("rq_integrity_checker.py", [str(path)])
        self.assertEqual(code, 1, out)
        self.assertIn("RQ-BK-UNUSED-THEME", out)

    def test_invalid_category_fails(self):
        path = write(self.tmp, "req.md", GOOD + "\n| `RQ-XX-UNKNOWN` | 不明 | `RQ-BK-SHARED-CHECK-SCRIPT` |\n")
        code, out = run_script("rq_integrity_checker.py", [str(path)])
        self.assertEqual(code, 1, out)
        self.assertIn("RQ-XX-UNKNOWN", out)

    def test_missing_bz_fails_for_full_document(self):
        text = GOOD.replace("`RQ-BZ-HELLO-CHECK`", "業務")
        path = write(self.tmp, "req.md", text)
        code, out = run_script("rq_integrity_checker.py", [str(path)])
        self.assertEqual(code, 1, out)
        self.assertIn("RQ-BZ", out)

    def test_change_document_does_not_require_bz(self):
        text = """
        | RQ-ID | 区分 | 内容 | 対応業務課題ID |
        |---|---|---|---|
        | `RQ-BK-ADD-TIMESTAMP` | [追加] | 時刻を付ける | |
        | `RQ-FT-PRINT-TIMESTAMP` | [追加] | 時刻付き出力 | `RQ-BK-ADD-TIMESTAMP` |

        ## 7. テスト用利用シナリオ

        | RQ-ID | 区分 | テスト目的 | 検証する要件ID | 対応業務課題ID |
        |---|---|---|---|---|
        | `RQ-TS-VERIFY-TIMESTAMP` | [追加] | 時刻の確認 | `RQ-FT-PRINT-TIMESTAMP` | `RQ-BK-ADD-TIMESTAMP` |
        """
        path = write(self.tmp, "change.md", text)
        code, out = run_script("rq_integrity_checker.py", [str(path)])
        self.assertEqual(code, 0, out)

    def test_header_labels_are_not_ids(self):
        path = write(self.tmp, "req.md", GOOD)
        code, out = run_script("rq_integrity_checker.py", [str(path)])
        self.assertNotIn("RQ-BK-ID", out.split("結果")[-1])

    def test_missing_file_reports_reason(self):
        code, out = run_script("rq_integrity_checker.py", [str(self.tmp / "none.md")])
        self.assertEqual(code, 1)
        self.assertIn("見つかりません", out)

    # requirements-chapters.md 第 7 章: RQ-FT・RQ-UI・RQ-EX は 1 本以上の RQ-TS の「検証する要件ID」に現れる
    def test_feature_without_scenario_fails(self):
        text = GOOD.replace("| `RQ-EF-SOFT-SAVING-CHECK` | 工数削減 | `RQ-BK-SHARED-CHECK-SCRIPT` |",
                            "| `RQ-EF-SOFT-SAVING-CHECK` | 工数削減 | `RQ-BK-SHARED-CHECK-SCRIPT` |\n| `RQ-UI-HELLO-SCREEN` | 画面 | `RQ-BK-SHARED-CHECK-SCRIPT` |")
        path = write(self.tmp, "req.md", text)
        code, out = run_script("rq_integrity_checker.py", [str(path)])
        self.assertEqual(code, 1, out)
        self.assertIn("受け入れテスト欠落", out)
        self.assertIn("RQ-UI-HELLO-SCREEN", out)
        self.assertNotIn("RQ-FT-PRINT-HELLO\n", out)

    # 第 7 章の表に列が無い文書は、欠落と一緒に列の不足を案内する
    def test_missing_verify_column_is_reported(self):
        text = GOOD.split("## 7.")[0]
        path = write(self.tmp, "req.md", text)
        code, out = run_script("rq_integrity_checker.py", [str(path)])
        self.assertEqual(code, 1, out)
        self.assertIn("「検証する要件ID」列が見つかりません", out)

    # RQ-NF・RQ-DT・RQ-OP には受け入れテストを求めない
    def test_non_feature_categories_do_not_need_scenario(self):
        text = GOOD.replace("| `RQ-EF-SOFT-SAVING-CHECK` | 工数削減 | `RQ-BK-SHARED-CHECK-SCRIPT` |",
                            "| `RQ-EF-SOFT-SAVING-CHECK` | 工数削減 | `RQ-BK-SHARED-CHECK-SCRIPT` |\n"
                            "| `RQ-NF-RESPONSE-1S` | 応答 | `RQ-BK-SHARED-CHECK-SCRIPT` |\n"
                            "| `RQ-DT-NO-STORAGE` | 保持しない | `RQ-BK-SHARED-CHECK-SCRIPT` |\n"
                            "| `RQ-OP-NO-LOG` | ログ不要 | `RQ-BK-SHARED-CHECK-SCRIPT` |")
        path = write(self.tmp, "req.md", text)
        code, out = run_script("rq_integrity_checker.py", [str(path)])
        self.assertEqual(code, 0, out)

    # 「検証する要件ID」列の ID は RQ-BK との対応に数えない。正本でこの列にだけ現れる ID は未定義の参照
    def test_verify_column_does_not_count_as_bk_mapping(self):
        text = GOOD.replace("| `RQ-TS-VERIFY-HELLO` | 出力の確認 | 無し | 実行する | Hello が出る | `RQ-FT-PRINT-HELLO` | `RQ-BK-SHARED-CHECK-SCRIPT` |",
                            "| `RQ-TS-VERIFY-HELLO` | 出力の確認 | 無し | 実行する | Hello が出る | `RQ-FT-PRINT-HELLO`, `RQ-FT-ONLY-IN-SCENARIO` | `RQ-BK-SHARED-CHECK-SCRIPT` |")
        path = write(self.tmp, "req.md", text)
        code, out = run_script("rq_integrity_checker.py", [str(path)])
        self.assertEqual(code, 1, out)
        self.assertIn("未定義参照", out)
        self.assertIn("RQ-FT-ONLY-IN-SCENARIO", out)
        self.assertNotIn("BKマッピング欠落", out)

    # 変更要件定義書: [追加] の RQ-FT にだけ RQ-TS を求める。既存の要件への参照には求めない。[削除] のシナリオは数えない
    def test_change_document_requires_scenario_for_added_features_only(self):
        base = """
        | RQ-ID | 区分 | 内容 | 対応業務課題ID |
        |---|---|---|---|
        | `RQ-BK-ADD-TIMESTAMP` | [追加] | 時刻を付ける | |
        | `RQ-FT-PRINT-TIMESTAMP` | [追加] | 時刻付き出力 | `RQ-BK-ADD-TIMESTAMP` |

        ## 7. テスト用利用シナリオ

        | RQ-ID | 区分 | テスト目的 | 検証する要件ID | 対応業務課題ID |
        |---|---|---|---|---|
        """
        # 7 章が無い → [追加] の要件が欠落
        path = write(self.tmp, "creq.md", base)
        code, out = run_script("rq_integrity_checker.py", [str(path)])
        self.assertEqual(code, 1, out)
        self.assertIn("RQ-FT-PRINT-TIMESTAMP", out)
        # [削除] の行だけでは数えない
        path = write(self.tmp, "creq.md", base + "| `RQ-TS-VERIFY-OUTPUT` | [削除] | 出力の確認 | `RQ-FT-PRINT-TIMESTAMP` | `RQ-BK-ADD-TIMESTAMP` |\n")
        code, out = run_script("rq_integrity_checker.py", [str(path)])
        self.assertEqual(code, 1, out)
        # [削除]・[追加] の 2 行で列を差し替えれば合格。既存要件 RQ-FT-PRINT-HELLO への参照には RQ-TS を求めない
        path = write(self.tmp, "creq.md", base
                     + "| `RQ-TS-VERIFY-OUTPUT` | [削除] | 出力の確認 | `RQ-FT-PRINT-HELLO` | `RQ-BK-ADD-TIMESTAMP` |\n"
                     + "| `RQ-TS-VERIFY-OUTPUT` | [追加] | 出力の確認 | `RQ-FT-PRINT-HELLO`, `RQ-FT-PRINT-TIMESTAMP` | `RQ-BK-ADD-TIMESTAMP` |\n")
        code, out = run_script("rq_integrity_checker.py", [str(path)])
        self.assertEqual(code, 0, out)


if __name__ == "__main__":
    unittest.main()
