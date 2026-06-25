import os
import httpx
import asyncio
from concurrent.futures import ThreadPoolExecutor
from bs4 import BeautifulSoup
from googlesearch import search
from ddgs import DDGS

for k in (
    "HTTP_PROXY",
    "HTTPS_PROXY",
    "ALL_PROXY",
    "http_proxy",
    "https_proxy",
    "all_proxy",
):
    os.environ.pop(k, None)

_executor = ThreadPoolExecutor(max_workers=8)

_headers = {"User-Agent": "Mozilla/5.0"}

_links = []
_texts = []


async def _fetch_text(url: str) -> str:
    async with httpx.AsyncClient(
        timeout=httpx.Timeout(8.0), follow_redirects=True
    ) as client:
        try:
            r = await client.get(url, headers=_headers)
            x = BeautifulSoup(r.text, "html.parser")
            for tag in x(["script", "style", "header", "footer", "nav", "noscript"]):
                tag.decompose()
            return " ".join(x.get_text(" ", strip=True).split())
        except:
            return ""


def _gg(q, n=2):
    try:
        return [{"url": u} for u in search(q, num_results=n)]
    except:
        return []


def _ddg(q, n=2):
    try:
        out = []
        with DDGS() as d:
            for r in d.text(q, max_results=n):
                out.append({"url": r.get("href", "")})
        return out
    except:
        return []


def _bing(q, n=2):
    try:
        import requests as _r
        r = _r.get(
            "https://www.bing.com/search",
            params={"q": q},
            headers=_headers,
            timeout=10,
        )
        x = BeautifulSoup(r.text, "html.parser")
        out = []
        for i in x.select(".b_algo"):
            a = i.select_one("h2 a")
            if a:
                out.append({"url": a.get("href", "")})
        return out[:n]
    except:
        return []


def find(q, n=2):
    global _links, _texts
    _links.clear()
    _texts.clear()

    res = _gg(q, n) + _ddg(q, n) + _bing(q, n)

    seen = set()
    for i in res:
        u = i["url"]
        if not u or u in seen:
            continue
        seen.add(u)
        try:
            import requests as _r
            r = _r.get(u, headers=_headers, timeout=10)
            x = BeautifulSoup(r.text, "html.parser")
            for tag in x(["script", "style", "header", "footer", "nav", "noscript"]):
                tag.decompose()
            t = " ".join(x.get_text(" ", strip=True).split())
        except:
            t = ""
        if not t:
            continue
        _links.append(u)
        _texts.append(t[:2000])
    return _texts


async def find_async(q, n=2):
    global _links, _texts
    _links.clear()
    _texts.clear()

    loop = asyncio.get_event_loop()
    res = await asyncio.gather(
        loop.run_in_executor(_executor, _gg, q, n),
        loop.run_in_executor(_executor, _ddg, q, n),
        loop.run_in_executor(_executor, _bing, q, n),
    )

    all_results = []
    for r in res:
        all_results.extend(r)

    seen = set()
    fetch_tasks = []
    urls = []
    for i in all_results:
        u = i["url"]
        if not u or u in seen:
            continue
        seen.add(u)
        urls.append(u)
        fetch_tasks.append(_fetch_text(u))

    if fetch_tasks:
        texts = await asyncio.gather(*fetch_tasks, return_exceptions=False)
        for u, t in zip(urls, texts):
            if t:
                _links.append(u)
                _texts.append(t[:2000])
    return _texts


def get_links():
    return _links


def get_texts():
    return _texts


def get_result():
    return {"links": _links, "texts": _texts}
