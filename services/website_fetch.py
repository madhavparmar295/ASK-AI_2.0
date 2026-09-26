import httpx


USER_AGENT = "ASK-AI-Website-Ingestion/1.0"


async def fetch_page(url: str):
    try:
        async with httpx.AsyncClient(
            timeout=20.0,
            follow_redirects=True,
            verify=False,
            headers={
                "User-Agent": USER_AGENT
            },
        ) as client:

            resp = await client.get(url)

            print(
                f"[Website Fetch] "
                f"{resp.status_code} {resp.url}"
            )

            return {
                "url": str(resp.url),
                "status_code": resp.status_code,
                "html": resp.text,
                "content_type": resp.headers.get(
                    "content-type", ""
                ),
            }

    except Exception as e:
        print(f"[Website Fetch] Failed: {url}")
        print(f"[Website Fetch] Error: {e}")
        return None
