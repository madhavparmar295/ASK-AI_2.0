import httpx

MIN_STATIC_CONTENT_CHARS = 200
USER_AGENT = "ASK-AI-Bot/1.0 (IITJ student project)"


async def fetch_page(url: str) -> dict:
    """Returns {"html": ..., "status": ..., "method": ...}"""
    async with httpx.AsyncClient(follow_redirects=True, timeout=10) as client:
        resp = await client.get(url, headers={"User-Agent": USER_AGENT})
        if _looks_rendered(resp):
            return {"html": resp.text, "status": resp.status_code, "method": "httpx"}
        # Fallback: headless render for JS-heavy pages
        html = await _playwright_render(url)
        return {"html": html, "status": 200, "method": "playwright"}


def _looks_rendered(resp) -> bool:
    if resp.status_code >= 400:
        return False
    if "text/html" not in resp.headers.get("content-type", ""):
        return False
    # crude but effective: a real page has a meaningful body length
    return len(resp.text.strip()) > MIN_STATIC_CONTENT_CHARS


async def _playwright_render(url: str) -> str:
    from playwright.async_api import async_playwright

    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        await page.goto(url, wait_until="networkidle", timeout=15000)
        html = await page.content()
        await browser.close()
        return html


# Note: reuse the existing rate limiter here once you wire this into a real task --
# call acquire_token(bucket="website_crawl") from services/rate_limiter.py before
# every fetch, the same way the Gmail backfill worker already does before every
# API call.
