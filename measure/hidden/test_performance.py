"""段 2: 性能。50 のブラウザ環境から同時に開き、操作の応答が 3 秒以内かを測る。前提データ（備品 500、アカウント 50、貸出 200）は画面操作で入れる。"""

import asyncio
import sys
import threading
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor

import pytest

from support.config import BTN_MAKE_STAFF, BTN_UNMAKE_STAFF, EMP_FORMAT_MSG, LAST_STAFF, OLD_ROLE, ROLE, STAFF_ONLY, emp
from playwright.async_api import async_playwright

LIMIT_SECONDS = 3.0


def bulk_data() -> dict:
    accounts = [{"number": emp("1"), "name": "担当太郎", "staff": True}]
    accounts += [{"number": emp(str(i)), "name": f"社員{i}"} for i in range(2, 51)]
    equipment = [{"number": f"PC-{i:03d}", "name": f"備品{i}"} for i in range(1, 501)]
    lendings = [
        {"equipment": f"PC-{i:03d}", "borrower": emp(str((i % 49) + 2)), "lent_on": "2026-10-01"}
        for i in range(1, 201)
    ]
    return {"accounts": accounts, "equipment": equipment, "lendings": lendings}


def _get_status(base_url: str) -> float:
    start = time.perf_counter()
    urllib.request.urlopen(f"{base_url}/").read()
    return time.perf_counter() - start


async def _display_seconds(page) -> float:
    """ブラウザが記録した、直前の画面の要求の開始から表示の完了までの秒数を返す。

    送信からリダイレクト先の画面の表示までを含む。テスト側の操作の指示の待ちは含まない。
    """
    await page.wait_for_load_state("load")
    duration = await page.evaluate("performance.getEntriesByType('navigation')[0].duration")
    return duration / 1000


async def _measure(base_url: str) -> dict:
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch()
        contexts = [await browser.new_context() for _ in range(50)]
        pages = [await context.new_page() for context in contexts]

        async def open_status(page) -> float:
            await page.goto(f"{base_url}/")
            return await _display_seconds(page)

        # 1 回目はブラウザ側の描画プロセスの立ち上げを含み、50 画面が同じコンテナの CPU を
        # 取り合うので測らない（利用者はそれぞれ自分のブラウザで開くため）。2 回目を測る。
        await asyncio.gather(*(open_status(page) for page in pages))
        open_times = await asyncio.gather(*(open_status(page) for page in pages))

        staff = pages[0]
        await staff.goto(f"{base_url}/login/")
        await staff.fill("#id_employee_number", emp("1"))
        await staff.fill("#id_password", "password1")
        await staff.get_by_role("button", name="ログイン").click()
        await staff.wait_for_url(f"{base_url}/")
        await staff.locator('tr[data-equipment-number="PC-300"]').get_by_role("button", name="貸出").click()
        await staff.select_option("#id_borrower", index=1)
        # ほかの 49 人分の閲覧は、ブラウザの描画を混ぜずにサーバーへの同時の要求としてかける
        pool = ThreadPoolExecutor(49)
        others = asyncio.gather(
            *(asyncio.wrap_future(pool.submit(_get_status, base_url)) for _ in range(49))
        )
        async with staff.expect_navigation(url=f"{base_url}/"):
            await staff.get_by_role("button", name="登録").click()
        lend_time = await _display_seconds(staff)
        staff.once("dialog", lambda dialog: asyncio.ensure_future(dialog.accept()))
        async with staff.expect_navigation(url=f"{base_url}/"):
            await staff.locator('tr[data-equipment-number="PC-300"]').get_by_role("button", name="返却").click()
        return_time = await _display_seconds(staff)
        reload_times = await others
        pool.shutdown()
        await browser.close()
        return {"open": open_times, "lend": lend_time, "return": return_time, "reload": reload_times}


@pytest.mark.stage2
def test_response_time(app):
    app.seed(bulk_data())
    result: dict = {}
    # pytest-playwright の同期 API と混ざらないよう、非同期 API は別のスレッドで動かす
    thread = threading.Thread(target=lambda: result.update(asyncio.run(_measure(app.base_url))))
    thread.start()
    thread.join()
    print(
        f"open max={max(result['open']):.2f}s lend={result['lend']:.2f}s "
        f"return={result['return']:.2f}s reload max={max(result['reload']):.2f}s",
        file=sys.stderr, flush=True,
    )
    assert max(result["open"]) < LIMIT_SECONDS
    assert max(result["reload"]) < LIMIT_SECONDS
    assert result["lend"] < LIMIT_SECONDS
    assert result["return"] < LIMIT_SECONDS
