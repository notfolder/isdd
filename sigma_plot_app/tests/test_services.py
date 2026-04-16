"""
テストサービス - サービスの単体テスト

- file_service のテスト
- column_service のテスト
- plot_service のテスト
"""

import pytest
from services.file_service import FileService
from services.column_service import ColumnService
from services.plot_service import PlotService


class TestFileService:
    """FileService のテスト"""

    def setup_method(self):
        """各テスト前の準備処理"""
        self.file_service = FileService()

    def test_check_file_exists_true(self, tmp_path):
        """ファイルが存在する場合、True を返す"""
        test_file = tmp_path / "test.csv"
        test_file.write_text("a,b\n1,2\n3,4\n")

        result = self.file_service.check_file_exists(str(test_file))
        assert result is True

    def test_check_file_exists_false(self, tmp_path):
        """ファイルが存在しない場合、False を返す"""
        result = self.file_service.check_file_exists("/nonexistent/path/file.csv")
        assert result is False

    def test_check_file_size_within_limit(self, tmp_path):
        """ファイルサイズが制限内の場合、True を返す"""
        test_file = tmp_path / "test.csv"
        content = "a,b\n" + ",".join(["1"] * 500) + "\n"
        test_file.write_text(content)

        is_within_limit, file_size = self.file_service.check_file_size(str(test_file))
        assert is_within_limit is True
        assert file_size > 0

    def test_check_file_size_exceeds_limit(self, tmp_path):
        """ファイルサイズが制限を超えている場合、False を返す"""
        test_file = tmp_path / "test.csv"
        content = "a,b\n" + ",".join(["1"] * 2000) + "\n"
        test_file.write_text(content)

        is_within_limit, file_size = self.file_service.check_file_size(str(test_file))
        assert is_within_limit is False

    def test_validate_csv_format_valid(self, tmp_path):
        """有効な CSV 形式の場合、True を返す"""
        test_file = tmp_path / "test.csv"
        content = "a,b,c\n1,2,3\n4,5,6\n"
        test_file.write_text(content)

        is_csv, error_msg = self.file_service.validate_csv_format(str(test_file))
        assert is_csv is True
        assert error_msg == ""

    def test_validate_csv_format_not_csv(self, tmp_path):
        """CSV 形式でない場合、False を返す"""
        test_file = tmp_path / "test.txt"
        content = "a b c\n1 2 3\n4 5 6\n"
        test_file.write_text(content)

        is_csv, error_msg = self.file_service.validate_csv_format(str(test_file))
        assert is_csv is False
        assert "CSV 形式" in error_msg

    def test_read_csv(self, tmp_path):
        """CSV の読み込みが正常に機能する"""
        test_file = tmp_path / "test.csv"
        content = "a,b,c\n1,2,3\n4,5,6\n"
        test_file.write_text(content)

        headers, data_rows = self.file_service.read_csv(str(test_file))
        assert headers == ["a", "b", "c"]
        assert data_rows == [["1", "2", "3"], ["4", "5", "6"]]

    def test_load_csv(self, tmp_path):
        """CSV の読み込みが正常に機能する"""
        test_file = tmp_path / "test.csv"
        content = """a,b,c
1.5,2.5,3.0
4.0,5.0,6.0"""
        test_file.write_text(content)

        columns_data = self.file_service.load_csv(str(test_file))
        assert "a" in columns_data
        assert "b" in columns_data
        assert "c" in columns_data
        assert columns_data["a"] == [1.5, 4.0]
        assert columns_data["b"] == [2.5, 5.0]
        assert columns_data["c"] == [3.0, 6.0]


class TestColumnService:
    """ColumnService のテスト"""

    def setup_method(self):
        """各テスト前の準備処理"""
        self.column_service = ColumnService()

    def test_get_columns(self):
        """カラム一覧の取得が正常に機能する"""
        columns_data = {
            "column_a": [1.0, 2.0, 3.0],
            "column_b": [4.0, 5.0, 6.0],
            "column_c": [7.0, 8.0, 9.0],
        }

        columns = self.column_service.get_columns(columns_data)
        assert set(columns) == {"column_a", "column_b", "column_c"}

    def test_select_columns(self):
        """カラム選択が正常に機能する"""
        columns_data = {
            "column_a": [1.0, 2.0, 3.0],
            "column_b": [4.0, 5.0, 6.0],
            "column_c": [7.0, 8.0, 9.0],
        }

        data_1, data_2 = self.column_service.select_columns(
            columns_data, ["column_a", "column_b"]
        )

        assert data_1 == [1.0, 2.0, 3.0]
        assert data_2 == [4.0, 5.0, 6.0]

    def test_select_columns_invalid_count(self):
        """カラム選択数が 2 つでない場合、ValueError をスローする"""
        columns_data = {"column_a": [1.0, 2.0], "column_b": [3.0, 4.0]}

        with pytest.raises(ValueError) as exc_info:
            self.column_service.select_columns(columns_data, ["column_a"])

        assert "2 つのカラムを選択してください" in str(exc_info.value)


class TestPlotService:
    """PlotService のテスト"""

    def setup_method(self):
        """各テスト前の準備処理"""
        self.plot_service = PlotService()

    def test_calculate_percentiles(self):
        """百分位数の計算が正常に機能する"""
        data = [1.0, 2.0, 3.0, 4.0, 5.0]

        theoretical, measured = self.plot_service.calculate_percentiles(data, n=5)

        assert len(theoretical) == 5
        assert len(measured) == 5

    def test_calculate_qq_plot_data(self):
        """Q-Q プロットデータの計算が正常に機能する"""
        data_1 = [1.0, 2.0, 3.0, 4.0, 5.0]
        data_2 = [1.5, 2.5, 3.5, 4.5, 5.5]

        qq_plot_data = self.plot_service.calculate_qq_plot_data(data_1, data_2)

        assert qq_plot_data is not None

    def test_calculate_histogram(self):
        """ヒストグラムの計算が正常に機能する"""
        data_1 = [1.0, 2.0, 3.0, 4.0, 5.0]
        data_2 = [1.5, 2.5, 3.5, 4.5, 5.5]

        hist_data = self.plot_service.calculate_histogram(data_1, data_2)

        assert hist_data is not None

    def test_render_qq_plot(self):
        """Q-Q プロットの描画が正常に機能する"""
        data_1 = [1.0, 2.0, 3.0, 4.0, 5.0]
        data_2 = [1.5, 2.5, 3.5, 4.5, 5.5]

        qq_plot_data = self.plot_service.calculate_qq_plot_data(data_1, data_2)
        rendered_plot = self.plot_service.render_qq_plot(qq_plot_data)

        assert rendered_plot is not None

    def test_save_plot(self, tmp_path):
        """プロットの保存が正常に機能する"""
        data_1 = [1.0, 2.0, 3.0, 4.0, 5.0]
        data_2 = [1.5, 2.5, 3.5, 4.5, 5.5]

        qq_plot_data = self.plot_service.calculate_qq_plot_data(data_1, data_2)
        filepath = str(tmp_path / "test.png")

        result = self.plot_service.save_plot(qq_plot_data, filepath)

        assert result is True
        assert tmp_path.exists("test.png")
