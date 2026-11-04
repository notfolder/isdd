"""非機能要件（表示は 3 秒以内）の E2E: 備品が数百件あっても 3 秒以内に一覧が出る。"""

import sqlite3
import time

from support import register


def test_response_time(start_app, page):
    """備品 500 件の一覧を開いて、表示が 3 秒以内に終わる。"""
    app = start_app()
    base = app.base_url
    register(page, base, "123456", "山田太郎")
    # 初期化済みの DB に 500 件を直接入れる（画面の操作で 500 件作ると時間を測れないため）
    with sqlite3.connect(app.data_dir / "equipment.db") as conn:
        conn.executemany(
            "INSERT INTO equipment (equipment_number, name) VALUES (?, ?)",
            [(f"EQ-{i:04d}", f"備品 {i}") for i in range(500)],
        )

    started = time.perf_counter()
    page.goto(base + "/")
    page.wait_for_selector("tbody tr:nth-child(500)")
    elapsed = time.perf_counter() - started

    assert page.locator("tbody tr").count() == 500
    assert elapsed < 3.0, f"表示に {elapsed:.2f} 秒かかりました"
