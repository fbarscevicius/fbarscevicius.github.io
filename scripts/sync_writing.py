#!/usr/bin/env python3
"""Rebuild the writing list in index.html from the anvilwright RSS feed.

Replaces everything between the WRITING:START and WRITING:END markers with the
latest essays (title, ISO date, one-line summary). Stdlib only, so the Action
needs no dependencies. Exits 0 whether or not anything changed; the workflow
commits only when the file actually differs.
"""

import html
import re
import sys
import urllib.request
import xml.etree.ElementTree as ET
from email.utils import parsedate_to_datetime
from pathlib import Path

FEED = "https://anvilwright.com/rss.xml"
INDEX = Path(__file__).resolve().parent.parent / "index.html"
LIMIT = 5
START = "<!-- WRITING:START"
END = "<!-- WRITING:END -->"


def fetch_items():
    req = urllib.request.Request(FEED, headers={"User-Agent": "writing-sync"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        root = ET.fromstring(resp.read())
    items = []
    for item in root.findall("./channel/item")[:LIMIT]:
        date = parsedate_to_datetime(item.findtext("pubDate")).strftime("%Y-%m-%d")
        items.append(
            {
                "title": item.findtext("title", "").strip(),
                "link": item.findtext("link", "").strip(),
                "summary": " ".join(item.findtext("description", "").split()),
                "date": date,
            }
        )
    return items


def render(items):
    blocks = []
    for it in items:
        blocks.append(
            "            <li class=\"writing-item\">\n"
            f"              <a class=\"writing-link\" href=\"{html.escape(it['link'], quote=True)}\">\n"
            f"                <time class=\"writing-date\">{it['date']}</time>\n"
            f"                <span class=\"writing-title\">{html.escape(it['title'], quote=False)}</span>\n"
            "                <span class=\"writing-summary\">\n"
            f"                  {html.escape(it['summary'], quote=False)}\n"
            "                </span>\n"
            "              </a>\n"
            "            </li>"
        )
    return "\n".join(blocks)


def main():
    items = fetch_items()
    if not items:
        print("no items in feed; leaving index.html untouched")
        return 0

    text = INDEX.read_text()
    pattern = re.compile(
        r"(" + re.escape(START) + r".*?-->\n)(.*?)(\n\s*" + re.escape(END) + r")",
        re.DOTALL,
    )
    if not pattern.search(text):
        print("markers not found in index.html", file=sys.stderr)
        return 1

    new_text = pattern.sub(lambda m: m.group(1) + render(items) + m.group(3), text)
    if new_text == text:
        print("writing list already current")
    else:
        INDEX.write_text(new_text)
        print(f"updated writing list with {len(items)} essays")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
