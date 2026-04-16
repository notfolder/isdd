import streamlit as st
import pandas as pd
from typing import List

# ローカルで定義したモジュールをインポート（実際には相対パスや適切なインポート処理が必要だが、今回は簡略化）
from src.data_processor import DataProcessor
from src.analysis_engine import AnalysisEngine
from src.logger_manager import logger

# 初期セットアップ：ログマネージャーのインスタンスを取得
logger_manager = logger()
data_processor = DataProcessor()
analysis_engine = AnalysisEngine(logger_manager)


def main():
    """メインアプリケーションのエントリポイント。データフロー全体を制御する。"""
    st.title("📈 検査データ分布比較システム (MVP)")
    st.markdown("---")

    # 1. データアップロードフェーズ
    uploaded_file = st.file_uploader(
        "CSVファイルをアップロードしてください", type=["csv"]
    )
    data_df: pd.DataFrame = None
    metadata: dict = {}

    if uploaded_file is not None:
        try:
            # T-Logger: UPLOAD_START
            logger_manager.log_event(
                "UPLOAD_START",
                f"ファイル '{uploaded_file.name}' の読み込みを開始。",
                "データアップロード処理を開始します。",
            )

            # DataProcessorによるロードとバリデーション（T-DataProcessorの実行）
            data_df = data_processor.load_data(uploaded_file)
            metadata["filename"] = uploaded_file.name

        except Exception as e:
            st.error(f"🚨 データ読み込み中にエラーが発生しました: {e}")
            return

    # 2. カラム選択とバリデーションフェーズ
    if data_df is not None and data_df.shape[1] > 0:
        st.subheader("🔍 分析対象カラムの選択")

        all_columns = list(data_df.columns)

        # 利用可能な全てのカラムを表示し、ユーザーに選択させる
        selected_cols_raw = st.multiselect(
            "統計解析を行う数値カラムを選択してください:",
            options=all_columns,
            default=[],  # 初期値は空にするか、適切なデフォルト値を設定する
        )

        if selected_cols_raw:
            try:
                # DataProcessorによるバリデーション実行（T-DataProcessorの再利用）
                df_validated, error_cols = data_processor.validate_columns(
                    data_df, selected_cols_raw
                )
                metadata["validated_columns"] = df_validated.columns.tolist()

                st.success("✅ カラムが正常に検証されました。解析を実行できます。")

            except ValueError as e:
                st.error(f"❌ データバリデーションエラー: {e}")
                return

    # 3. 解析実行フェーズ (T-Analyzerの実行)
    if "validated_columns" in metadata and metadata["validated_columns"]:
        st.subheader("📊 統計解析の実行")

        run_analysis = st.button("解析を実行し、分布比較を行う", disabled=False)

        if run_analysis:
            # T-Logger: ANALYZE_START
            logger_manager.log_event(
                "ANALYZE_START",
                f"選択されたカラム {metadata['validated_columns']} の解析を開始。",
                "統計解析エンジンが動作中です...",
            )

            results = {}
            col_names = metadata["validated_columns"]

            for col in col_names:
                try:
                    # 記述統計量の計算 (T-Analyzerの実行)
                    stats = analysis_engine.calculate_descriptive_stats(data_df, col)
                    results[col] = stats

                    st.metric(label=f"{col} の平均値", value=f"{stats['mean']:.2f}")

                except Exception as e:
                    st.warning(f"⚠️ カラム '{col}' の解析中にエラーが発生しました: {e}")

            # 全カラムのデータを使ってQ-Qプロットを生成（今回は最初の有効なカラムで代表）
            main_col = col_names[0]
            data_for_qqplot = data_df[main_col].dropna().values.astype(np.float64)

            if len(data_for_qqplot) > 1:
                try:
                    # Q-Qプロットの生成 (T-Analyzerの実行)
                    fig = analysis_engine.calculate_qqplot(data_for_qqplot)
                    st.pyplot(fig)  # Streamlitで描画する
                except Exception as e:
                    st.warning(f"⚠️ Q-Qプロットの生成に失敗しました: {e}")

            # T-Logger: ANALYZE_SUCCESS
            logger_manager.log_event(
                "ANALYZE_SUCCESS",
                f"全ての解析が完了し、{len(col_names)}カラムの結果を統合しました。",
                "データ分析プロセスが正常に完了しました。",
            )

    st.sidebar.header("システムログ履歴")
    history = logger_manager.get_history()
    if history:
        # サイドバーでログの主要な情報のみ表示
        for log in history[-5:]:  # 最新5件を表示する例
            st.caption(f"[{log['event_type']}]: {log['message']}")


if __name__ == "__main__":
    # 環境変数やシミュレーション実行のためのダミーデータの生成処理をここに入れることも可能
    main()
