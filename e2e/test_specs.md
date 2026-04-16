# E2Eテストスイートの構成
# Playwrightを使用したエンドツーエンドテストコードを格納する。
# テストは以下のシナリオを網羅する必要がある：
# 1. 基本フロー (Basic Flow): CSVアップロード -> カラム選択 -> 解析実行 (成功ケース)
# 2. エラーハンドリング (Error Handling): 非数値データを含むカラムのアップロード/選択
# 3. 比較対象変更 (Comparison Change): データセットが複数ある場合の動作検証（今回は単一ファイルを想定し、ログ確認にフォーカス）

@page("basic_flow.spec.py")
async function testBasicFlow() { ... }

@page("error_handling.spec.py")
async function testErrorHandling() { ... }