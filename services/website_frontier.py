import httpx
from xml.etree import ElementTree
from urllib.parse import urlparse, urlunparse, parse_qs, urlencode
from urllib.robotparser import RobotFileParser

TRACKING_PARAMS = {"utm_source", "utm_medium", "utm_campaign", "gclid", "fbclid"}


def get_sitemap_urls(domain: str) -> list[str]:
    """Try the domain's sitemap.xml first -- fast and authoritative."""
    try:
        resp = httpx.get(f"{domain}/sitemap.xml", timeout=10)
        root = ElementTree.fromstring(resp.content)
        ns = "{http://www.sitemaps.org/schemas/sitemap/0.9}"
        return [el.text for el in root.iter(f"{ns}loc")]
    except Exception:
        return []


def bfs_crawl(domain: str, max_depth: int = 3, max_pages: int = 500) -> list[str]:
    """Fallback: breadth-first crawl from the homepage if no sitemap."""
    import httpx
    from bs4 import BeautifulSoup

    seen = {domain}
    queue = [(domain, 0)]
    found = []
    while queue and len(found) < max_pages:
        url, depth = queue.pop(0)
        if depth > max_depth:
            continue
        try:
            resp = httpx.get(url, timeout=10)
            found.append(url)
            soup = BeautifulSoup(resp.text, "html.parser")
            for a in soup.find_all("a", href=True):
                link = httpx.URL(url).join(a["href"])
                link_str = str(link)
                if domain in link_str and link_str not in seen:
                    seen.add(link_str)
                    queue.append((link_str, depth + 1))
        except Exception:
            continue
    return found


def normalize_url(url: str) -> str:
    """Strip tracking params, lowercase host, drop fragment."""
    parsed = urlparse(url)
    query = parse_qs(parsed.query)
    clean_query = {k: v for k, v in query.items() if k not in TRACKING_PARAMS}
    return urlunparse(parsed._replace(
        query=urlencode(clean_query, doseq=True), fragment="",
        netloc=parsed.netloc.lower(),
    ))


def is_allowed_by_robots(url: str, user_agent: str = "ASK-AI-Bot") -> bool:
    parsed = urlparse(url)
    robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
    rp = RobotFileParser()
    rp.set_url(robots_url)
    try:
        rp.read()
        return rp.can_fetch(user_agent, url)
    except Exception:
        return True  # if robots.txt is unreachable, default to allowed


def build_frontier(domain: str) -> list[str]:
    """Single entry point: sitemap first, BFS fallback, normalized + robots-checked."""
    urls = get_sitemap_urls(domain) or bfs_crawl(domain)
    seen = set()
    result = []
    for raw_url in urls:
        url = normalize_url(raw_url)
        if url in seen:
            continue
        seen.add(url)
        if is_allowed_by_robots(url):
            result.append(url)
    return result
