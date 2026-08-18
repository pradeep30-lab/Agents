from playwright.async_api import async_playwright, Page, expect
import pytest

@pytest.mark.asyncio
async def test_verify_airbnb_search():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        mypage = await browser.new_page()
        await mypage.goto("https://www.airbnb.com/")
        await expect(mypage).to_have_url("https://www.airbnb.com/")
        await mypage.get_by_test_id("structured-search-input-field-query").fill("Fremont")


""" page.goto("https://www.airbnb.com/")
 expect(page).to_have_url("https://www.airbnb.com/")
 page.get_by_test_id("structured-search-input-field-query").fill("Eastvale")"""
