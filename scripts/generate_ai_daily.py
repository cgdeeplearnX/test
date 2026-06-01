#!/usr/bin/env python3
"""Generate a daily AI news report from trusted RSS feeds."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
import argparse
import html
import json
import os
from pathlib import Path
import re
import textwrap
from typing import Iterable
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
import xml.etree.ElementTree as ET


DEFAULT_FEEDS = [
    ("OpenAI Blog", "https://openai.com/news/rss.xml"),
    ("Anthropic News", "https://www.anthropic.com/news/rss.xml"),
    ("Google DeepMind Blog", "https://deepmind.google/discover/blog/rss.xml"),
    ("Meta AI Blog", "https://ai.meta.com/blog/rss/"),
    ("Microsoft AI Blog", "https://blogs.microsoft.com/ai/feed/"),
    ("NVIDIA Blog AI", "https://blogs.nvidia.com/blog/category/deep-learning/feed/"),
    ("Hugging Face Blog", "https://huggingface.co/blog/feed.xml"),
    ("MIT Technology Review AI", "https://www.technologyreview.com/feed/"),
    ("VentureBeat AI", "https://venturebeat.com/category/ai/feed/"),
]

AI_KEYWORDS = {
    "ai",
    "artificial intelligence",
    "agi",
    "agent",
    "agents",
    "anthropic",
    "chatgpt",
    "claude",
    "deepmind",
    "diffusion",
    "embedding",
    "gemini",
    "generative",
    "gpt",
    "hugging face",
    "inference",
    "language model",
    "llm",
    "machine learning",
    "model",
    "multimodal",
    "neural",
    "openai",
    "sora",
    "transformer",
    "\u4eba\u5de5\u667a\u80fd",
    "\u5927\u6a21\u578b",
    "\u751f\u6210\u5f0f",
    "\u673a\u5668\u5b66\u4e60",
}


@dataclass(frozen=True)
class NewsItem:
    title: str
    url: str
    source: str
    summary: str
    published: str


def zh(value: str) -> str:
    return value.encode("ascii").decode("unicode_escape")


def fetch_url(url: str, timeout: int = 20) -> str:
    request = Request(
        url,
        headers={
            "User-Agent": "ai-daily-news-bot/1.0 (+https://github.com/cgdeeplearnX/test)",
            "Accept": "application/rss+xml, application/xml, text/xml, */*",
        },
    )
    with urlopen(request, timeout=timeout) as response:
        return response.read().decode("utf-8", errors="replace")


def clean_text(value: str | None) -> str:
    if not value:
        return ""
    value = re.sub(r"<[^>]+>", " ", value)
    value = html.unescape(value)
    value = re.sub(r"\s+", " ", value)
    return value.strip()


def parse_date(value: str | None) -> str:
    if not value:
        return ""
    try:
        parsed = parsedate_to_datetime(value)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc).isoformat()
    except (TypeError, ValueError, IndexError):
        return clean_text(value)


def child_text(element: ET.Element, names: Iterable[str]) -> str:
    for name in names:
        found = element.find(name)
        if found is not None and found.text:
            return found.text
    return ""


def atom_link(element: ET.Element) -> str:
    for link in element.findall("{*}link"):
        href = link.attrib.get("href")
        if href:
            return href
    return child_text(element, ["link", "{*}link"])


def parse_rss_items(feed_xml: str, source: str) -> list[NewsItem]:
    root = ET.fromstring(feed_xml)
    entries = root.findall(".//item") or root.findall(".//{*}entry")
    items: list[NewsItem] = []
    for entry in entries:
        title = clean_text(child_text(entry, ["title", "{*}title"]))
        url = clean_text(atom_link(entry))
        summary = clean_text(
            child_text(entry, ["description", "summary", "content", "{*}summary", "{*}content"])
        )
        published = parse_date(
            child_text(entry, ["pubDate", "published", "updated", "{*}published", "{*}updated"])
        )
        if title and url:
            items.append(
                NewsItem(
                    title=title,
                    url=url,
                    source=source,
                    summary=summary,
                    published=published,
                )
            )
    return items


def filter_ai_items(items: Iterable[NewsItem]) -> list[NewsItem]:
    filtered = []
    seen_urls = set()
    for item in items:
        haystack = f"{item.title} {item.summary} {item.source}".lower()
        if item.url in seen_urls:
            continue
        if any(keyword in haystack for keyword in AI_KEYWORDS):
            filtered.append(item)
            seen_urls.add(item.url)
    return filtered


def sort_items(items: Iterable[NewsItem]) -> list[NewsItem]:
    return sorted(items, key=lambda item: item.published or "", reverse=True)


def build_prompt(report_date: str, items: list[NewsItem]) -> str:
    source_lines = []
    for index, item in enumerate(items[:12], start=1):
        source_lines.append(
            f"{index}. {item.title}\n"
            f"   Source: {item.source}\n"
            f"   Published: {item.published or 'unknown'}\n"
            f"   URL: {item.url}\n"
            f"   Summary: {item.summary or 'No summary provided.'}"
        )
    instruction = zh(
        "\\u4f60\\u662f\\u4e00\\u4e2a\\u4e25\\u8c28\\u7684 AI "
        "\\u884c\\u4e1a\\u65e5\\u62a5\\u7f16\\u8f91\\u3002"
        "\\u53ea\\u57fa\\u4e8e\\u4e0b\\u9762\\u7ed9\\u51fa\\u7684"
        "\\u6765\\u6e90\\u5199\\u4e2d\\u6587\\u65e5\\u62a5\\uff0c"
        "\\u4e0d\\u8981\\u6dfb\\u52a0\\u6ca1\\u6709\\u6765\\u6e90"
        "\\u652f\\u6301\\u7684\\u4fe1\\u606f\\u3002"
    )
    request = zh(
        "\\u8bf7\\u8f93\\u51fa Markdown\\uff0c\\u5305\\u542b\\uff1a"
        "\\u4eca\\u65e5\\u91cd\\u70b9\\u3001\\u8be6\\u7ec6\\u5185\\u5bb9"
        "\\u3001\\u6765\\u6e90\\u5217\\u8868\\u3002"
    )
    return f"{instruction}\n\nDate: {report_date}\n\n{request}\n\n" + "\n\n".join(source_lines)


def extract_response_text(payload: dict) -> str:
    if isinstance(payload.get("output_text"), str):
        return payload["output_text"].strip()
    chunks = []
    for output in payload.get("output", []):
        for content in output.get("content", []):
            if content.get("type") in {"output_text", "text"} and content.get("text"):
                chunks.append(content["text"])
    return "\n".join(chunks).strip()


def summarize_with_openai(report_date: str, items: list[NewsItem]) -> tuple[str | None, str | None]:
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        return None, None

    model = os.environ.get("OPENAI_MODEL", "gpt-4.1-mini")
    body = {
        "model": model,
        "input": build_prompt(report_date, items),
    }
    request = Request(
        "https://api.openai.com/v1/responses",
        data=json.dumps(body).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    with urlopen(request, timeout=60) as response:
        payload = json.loads(response.read().decode("utf-8"))
    return extract_response_text(payload), model


def fallback_item_summary(item: NewsItem) -> str:
    if item.summary:
        return item.summary[:240] + ("..." if len(item.summary) > 240 else "")
    return zh("\\u8be5\\u6765\\u6e90\\u672a\\u63d0\\u4f9b\\u6458\\u8981\\uff0c\\u8bf7\\u6253\\u5f00\\u539f\\u6587\\u67e5\\u770b\\u7ec6\\u8282\\u3002")


def render_markdown(
    report_date: str,
    generated_at: datetime,
    items: list[NewsItem],
    source_errors: list[str],
    model_used: str | None,
    model_markdown: str | None = None,
) -> str:
    title = zh("\\u6bcf\\u65e5 AI \\u8981\\u95fb")
    generated_label = zh("\\u751f\\u6210\\u65f6\\u95f4")
    no_key_label = zh("\\u672a\\u914d\\u7f6e")
    fallback_note = zh("\\uff0c\\u672c\\u65e5\\u62a5\\u4f7f\\u7528 RSS \\u6807\\u9898\\u548c\\u6458\\u8981\\u751f\\u6210\\u57fa\\u7840\\u7248\\u672c\\u3002")
    highlights_label = zh("\\u4eca\\u65e5\\u91cd\\u70b9")
    no_items_text = zh("\\u4eca\\u65e5\\u672a\\u4ece\\u914d\\u7f6e\\u7684\\u4fe1\\u606f\\u6e90\\u4e2d\\u5339\\u914d\\u5230 AI \\u76f8\\u5173\\u65b0\\u95fb\\u3002")
    details_label = zh("\\u8be6\\u7ec6\\u5185\\u5bb9")
    source_label = zh("\\u6765\\u6e90")
    time_label = zh("\\u65f6\\u95f4")
    unknown_label = zh("\\u672a\\u77e5")
    link_label = zh("\\u94fe\\u63a5")
    model_label = zh("\\u6458\\u8981\\u6a21\\u578b")
    warning_label = zh("\\u91c7\\u96c6\\u8b66\\u544a")
    notes_label = zh("\\u8bf4\\u660e")
    notes_text = zh("\\u672c\\u6587\\u4ef6\\u7531 GitHub Actions \\u81ea\\u52a8\\u751f\\u6210\\u3002\\u8bf7\\u4ee5\\u539f\\u59cb\\u6765\\u6e90\\u94fe\\u63a5\\u4e3a\\u51c6\\uff0c\\u91cd\\u8981\\u51b3\\u7b56\\u524d\\u5e94\\u590d\\u6838\\u5b98\\u65b9\\u516c\\u544a\\u6216\\u4e00\\u624b\\u8d44\\u6599\\u3002")

    lines = [
        f"# {title} - {report_date}",
        "",
        f"> {generated_label}: {generated_at.astimezone(timezone.utc).isoformat()}",
        "",
    ]

    if model_markdown:
        lines.extend([model_markdown.strip(), ""])
    else:
        lines.extend(
            [
                f"> {no_key_label} `OPENAI_API_KEY`{fallback_note}",
                "",
                f"## {highlights_label}",
                "",
            ]
        )
        if items:
            for index, item in enumerate(items[:10], start=1):
                lines.append(f"{index}. {item.title} ({item.source})")
        else:
            lines.append(no_items_text)
        lines.extend(["", f"## {details_label}", ""])
        for index, item in enumerate(items[:10], start=1):
            lines.extend(
                [
                    f"### {index}. {item.title}",
                    "",
                    fallback_item_summary(item),
                    "",
                    f"- {source_label}: {item.source}",
                    f"- {time_label}: {item.published or unknown_label}",
                    f"- {link_label}: {item.url}",
                    "",
                ]
            )

    if model_used:
        lines.extend([f"> {model_label}: `{model_used}`", ""])

    if source_errors:
        lines.extend([f"## {warning_label}", ""])
        for error in source_errors:
            lines.append(f"- {error}")
        lines.append("")

    lines.extend(
        [
            f"## {notes_label}",
            "",
            notes_text,
            "",
        ]
    )
    return "\n".join(lines)


def load_news() -> tuple[list[NewsItem], list[str]]:
    all_items: list[NewsItem] = []
    errors: list[str] = []
    for source, url in DEFAULT_FEEDS:
        try:
            feed_xml = fetch_url(url)
            all_items.extend(parse_rss_items(feed_xml, source))
        except (ET.ParseError, HTTPError, URLError, TimeoutError, OSError) as exc:
            errors.append(f"{source}: {exc}")
    return sort_items(filter_ai_items(all_items)), errors


def output_path_for(report_date: str, output_dir: Path) -> Path:
    return output_dir / f"{report_date}-ai-daily.md"


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate a daily AI news markdown report.")
    parser.add_argument("--date", default=datetime.now(timezone.utc).date().isoformat())
    parser.add_argument("--output-dir", default="reports")
    args = parser.parse_args()

    report_date = args.date
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    items, source_errors = load_news()
    model_markdown = None
    model_used = None
    if items:
        try:
            model_markdown, model_used = summarize_with_openai(report_date, items)
        except (HTTPError, URLError, TimeoutError, OSError, json.JSONDecodeError) as exc:
            source_errors.append(f"OpenAI summary skipped: {exc}")

    markdown = render_markdown(
        report_date=report_date,
        generated_at=datetime.now(timezone.utc),
        items=items,
        source_errors=source_errors,
        model_used=model_used,
        model_markdown=model_markdown,
    )
    output_file = output_path_for(report_date, output_dir)
    output_file.write_text(markdown, encoding="utf-8")
    print(
        textwrap.dedent(
            f"""\
            Generated {output_file}
            Items: {len(items)}
            Warnings: {len(source_errors)}
            """
        ).strip()
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
