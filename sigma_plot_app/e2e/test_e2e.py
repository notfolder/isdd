"""
E2E テスト - アプリケーションの統合テスト

Playwright を使用したブラウザ自動化テスト
"""

import pytest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


@pytest.fixture(scope="module")
def driver():
    """WebDriver のセットアップ"""
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")  # ヘッドレスモード

    driver = webdriver.Chrome(options=options)
    yield driver
    driver.quit()


class TestE2EFileSelection:
    """ファイル選択機能の E2E テスト"""

    def test_file_upload_dialog(self, driver):
        """ファイル選択ダイアログが表示される"""
        # アプリにアクセス
        driver.get("http://localhost:8501")

        # ファイルアップロードコンポーネントが存在するか確認
        file_uploader = driver.find_element(By.CSS_SELECTOR, "input[type='file']")
        assert file_uploader is not None

    def test_file_size_display(self, driver):
        """ファイルサイズが表示される"""
        # アプリにアクセス
        driver.get("http://localhost:8501")

        # ファイルアップロード
        file_path = "/path/to/test.csv"
        driver.find_element(By.CSS_SELECTOR, "input[type='file']").send_keys(file_path)

        # ファイルサイズ表示を確認（待機）
        WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".stMetric"))
        )


class TestE2EColumnSelection:
    """カラム選択機能の E2E テスト"""

    def test_column_list_display(self, driver):
        """カラム一覧が表示される"""
        # アプリにアクセス
        driver.get("http://localhost:8501")

        # ファイルアップロード
        file_path = "/path/to/test.csv"
        driver.find_element(By.CSS_SELECTOR, "input[type='file']").send_keys(file_path)

        # 選択ボタンをクリック
        select_button = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
        select_button.click()

        # カラム選択コンポーネントが存在するか確認
        column_select_1 = driver.find_element(By.CSS_SELECTOR, "select.stSelectbox")
        assert column_select_1 is not None


class TestE2EQQPlotDisplay:
    """Q-Q プロット表示機能の E2E テスト"""

    def test_qq_plot_display(self, driver):
        """Q-Q プロットが表示される"""
        # アプリにアクセス
        driver.get("http://localhost:8501")

        # ファイルアップロード
        file_path = "/path/to/test.csv"
        driver.find_element(By.CSS_SELECTOR, "input[type='file']").send_keys(file_path)

        # 選択ボタンをクリック
        select_button = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
        select_button.click()

        # Q-Q プロット表示ボタンをクリック
        qq_plot_button = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
        qq_plot_button.click()

        # Q-Q プロットが存在するか確認（待機）
        WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div.stPlot"))
        )


class TestE2ESavePlot:
    """プロット保存機能の E2E テスト"""

    def test_save_plot(self, driver):
        """プロットが保存される"""
        # アプリにアクセス
        driver.get("http://localhost:8501")

        # ファイルアップロード
        file_path = "/path/to/test.csv"
        driver.find_element(By.CSS_SELECTOR, "input[type='file']").send_keys(file_path)

        # 選択ボタンをクリック
        select_button = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
        select_button.click()

        # Q-Q プロット表示ボタンをクリック
        qq_plot_button = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
        qq_plot_button.click()

        # 保存ボタンをクリック
        save_button = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
        save_button.click()


class TestE2EErrorHandling:
    """エラー処理機能の E2E テスト"""

    def test_invalid_file_type(self, driver):
        """無効なファイルタイプでエラーが表示される"""
        # アプリにアクセス
        driver.get("http://localhost:8501")

        # 無効なファイルアップロード（テキストファイル）
        file_path = "/path/to/test.txt"
        driver.find_element(By.CSS_SELECTOR, "input[type='file']").send_keys(file_path)

        # 選択ボタンをクリック
        select_button = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
        select_button.click()

        # エラーメッセージが表示されるか確認（待機）
        WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div.stError"))
        )


if __name__ == "__main__":
    pytest.main(["-v", "--html-report=./e2e_report.html"])
