"""
シグマプロット比較アプリ - メインアプリケーション

Streamlit を使用した CSV ファイルから 2 カラムのデータを指定し、
Q-Q プロットとヒストグラムで 2 つの分布を比較するアプリケーション。
"""

import streamlit as st
from services.file_service import FileService
from services.column_service import ColumnService
from services.plot_service import PlotService
from utils.validation import validate_numeric_data, check_file_size
from utils.error_handler import ErrorHandler

# ページ設定
st.set_page_config(page_title="シグマプロット比較アプリ", page_icon="📊", layout="wide")

# カスタム CSS（必要に応じて追加）
st.markdown(
    """
<style>
    .reportview-container {
        background: linear-gradient(to bottom right, #f8f9fa, #e9ecef);
        padding: 20px;
    }
    .stButton > button {
        background-color: #4CAF50;
        color: white;
    }
</style>
""",
    unsafe_allow_html=True,
)


class SigmaPlotApp:
    """シグマプロット比較アプリのメインクラス"""

    def __init__(self):
        """初期化処理"""
        self.file_service = FileService()
        self.column_service = ColumnService()
        self.plot_service = PlotService()
        self.error_handler = ErrorHandler()

    def run(self):
        """アプリケーションのメイン実行フロー"""
        st.title("📊 シグマプロット比較アプリ")

        # セッションステート管理
        if "analysis_session" not in st.session_state:
            st.session_state.analysis_session = {
                "file_path": None,
                "columns_data": {},
                "selected_columns": [],
                "data_1": None,
                "data_2": None,
                "error_message": None,
            }

        # エラー表示（セッション状態から）
        if st.session_state.analysis_session["error_message"]:
            self._show_error()

        # 画面遷移ロジック
        if st.session_state.analysis_session["error_message"] is None:
            self._show_file_selection()
        elif st.session_state.analysis_session["file_path"]:
            self._show_column_list()
        else:
            st.error("エラーが発生しました。ページをリロードしてください。")

    def _show_file_selection(self):
        """ファイル選択画面を表示"""
        st.subheader("1. ファイルを選択してください")

        # ファイルアップロードコンポーネント
        uploaded_file = st.file_uploader(
            "CSV ファイルを選択",
            type=["csv"],
            help="比較したい 2 つの分布を含む CSV ファイル",
        )

        # 保存ボタン
        col1, col2 = st.columns([3, 1])

        with col1:
            if uploaded_file is not None:
                # ファイルサイズチェック
                file_size = len(uploaded_file.read())
                uploaded_file.seek(0)  # ファイルポインタを先頭に戻す

                if file_size > 10 * 1024 * 1024:  # 10MB
                    st.error("ファイルサイズが 10MB を超えています。")
                else:
                    st.success(f"ファイルサイズ：{file_size / 1024:.1f} KB")

        with col2:
            if uploaded_file is not None and file_size <= 10 * 1024 * 1024:
                if st.button("選択", use_container_width=True):
                    # ファイルを保存（セッション状態に保持）
                    import tempfile

                    with tempfile.NamedTemporaryFile(
                        suffix=uploaded_file.name, delete=False
                    ) as tmp_file:
                        tmp_file.write(uploaded_file.read())
                        st.session_state.analysis_session["file_path"] = tmp_file.name

                    # 次へ遷移
                    st.session_state.analysis_session["error_message"] = None
                    st.rerun()

    def _show_column_list(self):
        """カラム一覧画面を表示"""
        st.subheader("2. カラムを選択してください")

        # ファイル情報を表示
        file_name = st.session_state.analysis_session["file_path"].split("/")[-1]
        st.info(f"選択されたファイル：{file_name}")

        # CSV を読み込み
        try:
            columns_data = self.column_service.load_csv(
                st.session_state.analysis_session["file_path"]
            )

            # カラム一覧を表示
            st.subheader("カラム一覧")

            col1, col2 = st.columns(2)

            with col1:
                data_1_col = st.selectbox(
                    "カラム 1",
                    options=columns_data.keys(),
                    label_visibility="collapsed",
                )

            with col2:
                data_2_col = st.selectbox(
                    "カラム 2",
                    options=columns_data.keys(),
                    label_visibility="collapsed",
                )

            # 統計情報を表示
            st.subheader("統計情報")
            col1, col2 = st.columns(2)

            with col1:
                data_1 = columns_data[data_1_col]
                st.metric(
                    "カラム 1",
                    f"平均：{sum(data_1) / len(data_1):.2f}",
                    f"標準偏差：{(__import__('statistics').stdev(data_1) if len(data_1) > 1 else 0):.2f}",
                )

            with col2:
                data_2 = columns_data[data_2_col]
                st.metric(
                    "カラム 2",
                    f"平均：{sum(data_2) / len(data_2):.2f}",
                    f"標準偏差：{(__import__('statistics').stdev(data_2) if len(data_2) > 1 else 0):.2f}",
                )

            # 保存ボタン
            if st.button("Q-Q プロットを表示", use_container_width=True):
                # カラム選択結果を保存
                st.session_state.analysis_session["selected_columns"] = [
                    data_1_col,
                    data_2_col,
                ]
                st.session_state.analysis_session["columns_data"] = columns_data

                # データを抽出
                st.session_state.analysis_session["data_1"] = columns_data[data_1_col]
                st.session_state.analysis_session["data_2"] = columns_data[data_2_col]

                # 検証とエラー処理
                errors = self.error_handler.validate_data(
                    st.session_state.analysis_session["data_1"],
                    st.session_state.analysis_session["data_2"],
                )

                if errors:
                    st.session_state.analysis_session["error_message"] = str(errors)
                    st.rerun()
                else:
                    # 次へ遷移
                    st.session_state.analysis_session["error_message"] = None
                    st.rerun()

        except Exception as e:
            st.session_state.analysis_session["error_message"] = f"エラー：{str(e)}"
            st.rerun()

    def _show_qq_plot(self):
        """Q-Q プロット表示画面を表示"""
        st.subheader("3. Q-Q プロット")

        # データ情報を表示
        col1, col2 = st.columns(2)

        with col1:
            data_1 = st.session_state.analysis_session["data_1"]
            st.metric(
                "カラム 1",
                f"平均：{sum(data_1) / len(data_1):.2f}",
                f"標準偏差：{(__import__('statistics').stdev(data_1) if len(data_1) > 1 else 0):.2f}",
            )

        with col2:
            data_2 = st.session_state.analysis_session["data_2"]
            st.metric(
                "カラム 2",
                f"平均：{sum(data_2) / len(data_2):.2f}",
                f"標準偏差：{(__import__('statistics').stdev(data_2) if len(data_2) > 1 else 0):.2f}",
            )

        # Q-Q プロット描画
        qq_plot_data = self.plot_service.calculate_qq_plot(
            st.session_state.analysis_session["data_1"],
            st.session_state.analysis_session["data_2"],
        )

        # プロット表示エリア
        col1, col2 = st.columns(2)

        with col1:
            fig = self.plot_service.render_qq_plot(qq_plot_data)
            st.pyplot(fig)

        with col2:
            # ヒストグラム表示オプション
            show_histogram = st.checkbox(
                "ヒストグラムを表示",
                value=True,
                help="2 つの分布のヒストグラムを重ねて表示",
            )

            if show_histogram:
                hist_data = self.plot_service.calculate_histogram(
                    st.session_state.analysis_session["data_1"],
                    st.session_state.analysis_session["data_2"],
                )

                fig = self.plot_service.render_qq_plot_with_histograms(
                    qq_plot_data, hist_data
                )
                st.pyplot(fig)

        # 保存ボタン
        col1, col2, col3 = st.columns([3, 1, 1])

        with col1:
            save_path = st.text_input(
                "保存パス", value="sigma_plot.png", label_visibility="collapsed"
            )

        with col2:
            if st.button("保存", use_container_width=True):
                self.plot_service.save_plot(save_path)

        with col3:
            if st.button("再表示", use_container_width=True):
                st.rerun()

    def _show_error(self):
        """エラー表示画面を表示"""
        st.error(f"エラー：{st.session_state.analysis_session['error_message']}")

        # 再試行ボタン
        if st.button("再試行", use_container_width=True):
            # セッション状態をリセット
            st.session_state.analysis_session = {
                "file_path": None,
                "columns_data": {},
                "selected_columns": [],
                "data_1": None,
                "data_2": None,
                "error_message": None,
            }
            st.rerun()


def main():
    """アプリケーションのメインエントリーポイント"""
    app = SigmaPlotApp()
    app.run()


if __name__ == "__main__":
    main()
