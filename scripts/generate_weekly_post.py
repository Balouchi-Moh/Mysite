#!/usr/bin/env python3
"""
Weekly content draft generator.

Reads new articles from trusted sources (scripts/sources.json), asks
Gemini to write an ORIGINAL Persian + English summary and professional
analysis (never a translation/reproduction of the source text), and
creates the new blog post files + a data/posts.json entry.

This script never publishes anything by itself — it only edits files
in the working directory. The GitHub Actions workflow that calls this
script then opens a Pull Request, so a human always approves before
anything goes live on the site.
"""
import json
import os
import re
import sys
import datetime
import urllib.request

import requests
import feedparser
from bs4 import BeautifulSoup

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.0-flash")
GEMINI_URL = (
    f"https://generativelanguage.googleapis.com/v1beta/models/"
    f"{GEMINI_MODEL}:generateContent?key={GEMINI_API_KEY}"
)


def load_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")


def slugify(text):
    text = re.sub(r"[^a-zA-Z0-9\s-]", "", text).strip().lower()
    text = re.sub(r"[\s_-]+", "-", text)
    return text[:60].strip("-") or "post"


def fetch_article_text(url):
    """Best-effort extraction of the main readable text of an article."""
    try:
        resp = requests.get(url, timeout=20, headers={"User-Agent": "Mozilla/5.0"})
        resp.raise_for_status()
    except Exception as e:
        print(f"  ! could not fetch article body: {e}")
        return ""
    soup = BeautifulSoup(resp.text, "html.parser")
    for tag in soup(["script", "style", "nav", "header", "footer", "form"]):
        tag.decompose()
    article = soup.find("article") or soup.find("main") or soup.body
    if not article:
        return ""
    paragraphs = [p.get_text(" ", strip=True) for p in article.find_all("p")]
    text = "\n".join(p for p in paragraphs if len(p) > 40)
    # Keep it bounded — we only need enough for a faithful summary, not the
    # full text (this also keeps us well clear of any copyright concerns:
    # the model summarizes/paraphrases, it never has the full article to copy).
    return text[:6000]


def find_next_article():
    sources = load_json(os.path.join(ROOT, "scripts", "sources.json"))["sources"]
    used = load_json(os.path.join(ROOT, "scripts", "used_sources.json"))
    used_urls = set(used["processed_urls"])

    for src in sources:
        print(f"Checking source: {src['name']} ({src['feed_url']})")
        try:
            # Fetch with browser-like headers first — some sites block the
            # default feedparser/urllib user-agent and return a challenge
            # page instead of the real XML feed, which breaks parsing.
            resp = requests.get(
                src["feed_url"],
                timeout=20,
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                                  "Chrome/120.0 Safari/537.36",
                    "Accept": "application/rss+xml, application/xml, text/xml, */*",
                },
            )
            resp.raise_for_status()
            feed = feedparser.parse(resp.content)
        except Exception as e:
            print(f"  ! feed error: {e}")
            continue
        if getattr(feed, "bozo", 0):
            print(f"  ! feed parse warning (bozo): {feed.get('bozo_exception')}")
            print(f"  -> first 300 chars of response, for debugging: {resp.text[:300]!r}")
        print(f"  -> {len(feed.entries)} entries found in this feed")
        if not feed.entries:
            print("  -> feed returned zero entries; check the feed_url is correct "
                  "and reachable (try opening it in a browser).")
        for entry in feed.entries:
            link = entry.get("link")
            if not link:
                continue
            if link in used_urls:
                print(f"  -> already processed, skipping: {link}")
                continue
            title = entry.get("title", "").strip()
            body = fetch_article_text(link)
            if len(body) < 300:
                print(f"  ! skipping (couldn't extract enough text): {link}")
                continue
            return {
                "source_name": src["name"],
                "source_url": link,
                "source_title": title,
                "source_text": body,
            }
    return None


def call_gemini(article):
    prompt = f"""You are a professional construction-management consultant
writing a short blog note for your own website, based on an article you
read elsewhere. You must NOT translate or reproduce the source text —
write an ORIGINAL summary in your own words, plus 2-3 sentences of your
own professional perspective/analysis as an experienced construction
management consultant (20+ years, Lean Construction specialist).

Source article title: {article['source_title']}
Source website: {article['source_name']}
Source article text (for your reference only — do not copy phrases from it):
---
{article['source_text']}
---

Return ONLY valid JSON (no markdown fences, no extra text) with exactly
these fields:
{{
  "tag_fa": "short 1-3 word Persian topic label, uppercase style e.g. LEAN CONSTRUCTION",
  "tag_en": "same label in English",
  "title_fa": "Persian title for this note, natural and engaging, NOT a literal translation of the source title",
  "title_en": "English title for this note",
  "excerpt_fa": "one Persian sentence, under 30 words, for use as a card preview",
  "excerpt_en": "one English sentence, under 30 words",
  "lead_fa": "one Persian sentence italic lead/subtitle for the article page",
  "lead_en": "one English sentence italic lead/subtitle",
  "body_fa_paragraphs": ["array of 4-6 Persian paragraphs, each a plain string with no HTML, forming the full article body with an original summary plus your professional analysis"],
  "body_en_paragraphs": ["array of 4-6 English paragraphs, matching the Persian ones"]
}}
"""
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.7, "responseMimeType": "application/json"},
    }
    req = urllib.request.Request(
        GEMINI_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    text = data["candidates"][0]["content"]["parts"][0]["text"]
    return json.loads(text)


def paragraphs_to_html(paragraphs, first_as_h2=False):
    html_parts = []
    for i, p in enumerate(paragraphs):
        html_parts.append(f"    <p>{p}</p>")
    return "\n".join(html_parts)


def fill_template(template_path, tokens):
    with open(template_path, encoding="utf-8") as f:
        content = f.read()
    for key, value in tokens.items():
        content = content.replace(f"__{key}__", value)
    return content


def main():
    if not GEMINI_API_KEY:
        print("ERROR: GEMINI_API_KEY environment variable is not set.")
        sys.exit(1)

    article = find_next_article()
    if not article:
        print("No new articles found from any source this week. Nothing to do.")
        return

    print(f"Found new article: {article['source_title']} ({article['source_url']})")
    print("Calling Gemini to write an original summary + analysis...")
    result = call_gemini(article)

    slug = slugify(result["title_en"])
    today = datetime.date.today().isoformat()
    read_time = str(max(3, len(result["body_en_paragraphs"]) * 1))

    fa_tokens = {
        "TITLE": result["title_fa"],
        "EXCERPT": result["excerpt_fa"],
        "LEAD": result["lead_fa"],
        "TAG": result["tag_fa"],
        "READ_TIME": read_time,
        "SLUG": slug,
        "SOURCE_NAME": article["source_name"],
        "SOURCE_URL": article["source_url"],
        "BODY": paragraphs_to_html(result["body_fa_paragraphs"]),
    }
    en_tokens = {
        "TITLE": result["title_en"],
        "EXCERPT": result["excerpt_en"],
        "LEAD": result["lead_en"],
        "TAG": result["tag_en"],
        "READ_TIME": read_time,
        "SLUG": slug,
        "SOURCE_NAME": article["source_name"],
        "SOURCE_URL": article["source_url"],
        "BODY": paragraphs_to_html(result["body_en_paragraphs"]),
    }

    fa_html = fill_template(os.path.join(ROOT, "scripts/templates/article_fa.html"), fa_tokens)
    en_html = fill_template(os.path.join(ROOT, "scripts/templates/article_en.html"), en_tokens)

    fa_path = os.path.join(ROOT, "blog", f"{slug}.html")
    en_path = os.path.join(ROOT, "en", "blog", f"{slug}.html")
    with open(fa_path, "w", encoding="utf-8") as f:
        f.write(fa_html)
    with open(en_path, "w", encoding="utf-8") as f:
        f.write(en_html)
    print(f"Wrote {fa_path}")
    print(f"Wrote {en_path}")

    # Prepend new entry to data/posts.json
    posts_path = os.path.join(ROOT, "data", "posts.json")
    posts_data = load_json(posts_path)
    posts_data["posts"].insert(0, {
        "id": slug,
        "status": "published",
        "date": today,
        "icon": "lean",
        "tag_fa": result["tag_fa"],
        "tag_en": result["tag_en"],
        "title_fa": result["title_fa"],
        "title_en": result["title_en"],
        "excerpt_fa": result["excerpt_fa"],
        "excerpt_en": result["excerpt_en"],
        "link_fa": f"blog/{slug}.html",
        "link_en": f"en/blog/{slug}.html",
    })
    save_json(posts_path, posts_data)
    print(f"Updated {posts_path}")

    # Mark this source article as processed
    used_path = os.path.join(ROOT, "scripts", "used_sources.json")
    used_data = load_json(used_path)
    used_data["processed_urls"].append(article["source_url"])
    save_json(used_path, used_data)
    print(f"Updated {used_path}")

    # Append to sitemap.xml (best-effort, simple string insert)
    sitemap_path = os.path.join(ROOT, "sitemap.xml")
    with open(sitemap_path, encoding="utf-8") as f:
        sitemap = f.read()
    new_urls = (
        f'  <url><loc>https://lean-construction.ir/blog/{slug}.html</loc><priority>0.6</priority></url>\n'
        f'  <url><loc>https://lean-construction.ir/en/blog/{slug}.html</loc><priority>0.5</priority></url>\n'
        f'</urlset>'
    )
    sitemap = sitemap.replace('</urlset>', new_urls)
    with open(sitemap_path, "w", encoding="utf-8") as f:
        f.write(sitemap)
    print("Updated sitemap.xml")

    print("\nDone. A Pull Request will now be opened for human review.")


if __name__ == "__main__":
    main()
