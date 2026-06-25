import httpx
import re

api = "https://ru.wikipedia.org/w/api.php"

text = ""
link = ""


def wiki(query):
    global text, link
    text = ""
    link = ""
    try:
        r = httpx.get(
            api,
            params={
                "action": "query",
                "list": "search",
                "srsearch": query,
                "format": "json",
                "srlimit": 5,
            },
            headers={"User-Agent": "LLM-WIKI/1.0"},
            timeout=8,
        )
        if r.status_code != 200:
            return
        data = r.json()
        results = data.get("query", {}).get("search", [])
        if not results:
            return
        item = results[0]
        text = re.sub("<.*?>", "", item.get("snippet", ""))
        link = "https://ru.wikipedia.org/wiki/" + item.get("title", "").replace(" ", "_")
    except:
        pass


async def wiki_async(query):
    global text, link
    text = ""
    link = ""
    try:
        async with httpx.AsyncClient(timeout=8) as client:
            r = await client.get(
                api,
                params={
                    "action": "query",
                    "list": "search",
                    "srsearch": query,
                    "format": "json",
                    "srlimit": 5,
                },
                headers={"User-Agent": "LLM-WIKI/1.0"},
            )
            if r.status_code != 200:
                return
            data = r.json()
            results = data.get("query", {}).get("search", [])
            if not results:
                return
            item = results[0]
            text = re.sub("<.*?>", "", item.get("snippet", ""))
            link = "https://ru.wikipedia.org/wiki/" + item.get("title", "").replace(" ", "_")
    except:
        pass


def get_text():
    return text


def get_link():
    return link
