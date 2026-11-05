"""E2E tests in a browser. Each test function is linked to one DS-TS-* in docs/trace_map.md."""

import re

from playwright.sync_api import expect


def test_browse_and_vote_e2e(page, base_url):
    # Sample poll 1 "Favorite season?" starts with Autumn = 2 votes.
    page.get_by_role("link", name="Vote").first.click()
    expect(page).to_have_url(re.compile(r"/polls/1$"))
    page.get_by_label("Autumn").check()
    page.get_by_role("button", name="Submit vote").click()
    expect(page).to_have_url(re.compile(r"/polls/1/results$"))
    expect(page.get_by_text("Autumn: 3 votes")).to_be_visible()


def test_vote_without_selection_e2e(page, base_url):
    page.goto(base_url + "/polls/1")
    page.get_by_role("button", name="Submit vote").click()
    expect(page.get_by_text("Please select an option.")).to_be_visible()
    page.goto(base_url + "/polls/1/results")
    expect(page.get_by_text("Total votes: 11")).to_be_visible()


def test_one_vote_per_browser_e2e(page, base_url):
    page.goto(base_url + "/polls/1")
    page.get_by_label("Summer").check()
    page.get_by_role("button", name="Submit vote").click()
    expect(page).to_have_url(re.compile(r"/polls/1/results$"))
    page.goto(base_url + "/polls/1")
    page.get_by_label("Spring").check()
    page.get_by_role("button", name="Submit vote").click()
    expect(page.get_by_text("You have already voted in this poll.")).to_be_visible()
    page.goto(base_url + "/polls/1/results")
    expect(page.get_by_text("Summer: 6 votes")).to_be_visible()
    expect(page.get_by_text("Spring: 3 votes")).to_be_visible()


def test_results_list_e2e(page, base_url):
    page.get_by_role("navigation", name="Main navigation").get_by_role("link", name="Results").click()
    expect(page).to_have_url(re.compile(r"/results$"))
    page.get_by_role("link", name="View results").first.click()
    expect(page).to_have_url(re.compile(r"/polls/1/results$"))
    expect(page.get_by_role("heading", name="Favorite season?")).to_be_visible()


def test_unknown_poll_e2e(page, base_url):
    page.goto(base_url + "/polls/99999")
    expect(page.get_by_text("Poll not found.")).to_be_visible()
    expect(page.get_by_role("navigation", name="Main navigation").get_by_role("link", name="Polls")).to_be_visible()


def test_visual_style_e2e(page, base_url):
    page.goto(base_url + "/polls")
    expect(page.locator("html")).to_have_attribute("lang", "en")
    body_bg = page.evaluate("getComputedStyle(document.body).backgroundColor")
    header_bg = page.evaluate("getComputedStyle(document.querySelector('header.site')).backgroundColor")
    button_bg = page.evaluate("getComputedStyle(document.querySelector('a.button')).backgroundColor")
    assert body_bg == "rgb(255, 255, 255)"
    assert header_bg == "rgb(0, 0, 128)"
    assert button_bg == "rgb(0, 0, 128)"


def test_empty_poll_results_e2e(page, base_url):
    # Sample poll 2 "Best programming language for beginners?" has no votes.
    page.goto(base_url + "/polls/2/results")
    expect(page.get_by_text("No votes yet.")).to_be_visible()
    expect(page.get_by_text("Python: 0 votes (0.0%)")).to_be_visible()
