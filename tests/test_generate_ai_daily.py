from datetime import datetime, timezone
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import generate_ai_daily as daily


SAMPLE_RSS = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>Sample</title>
    <item>
      <title>OpenAI releases a new model update</title>
      <link>https://example.com/openai-model</link>
      <description>Developers get better tool calling and lower latency.</description>
      <pubDate>Mon, 01 Jun 2026 00:00:00 GMT</pubDate>
    </item>
    <item>
      <title>Quarterly smartphone sales report</title>
      <link>https://example.com/phones</link>
      <description>Hardware market news.</description>
      <pubDate>Mon, 01 Jun 2026 01:00:00 GMT</pubDate>
    </item>
  </channel>
</rss>
"""


def test_parse_rss_items_extracts_entries():
    items = daily.parse_rss_items(SAMPLE_RSS, "Sample Feed")

    assert len(items) == 2
    assert items[0].title == "OpenAI releases a new model update"
    assert items[0].url == "https://example.com/openai-model"
    assert items[0].source == "Sample Feed"
    assert items[0].published.startswith("2026-06-01")


def test_filter_ai_items_keeps_ai_related_items():
    items = daily.parse_rss_items(SAMPLE_RSS, "Sample Feed")

    filtered = daily.filter_ai_items(items)

    assert [item.title for item in filtered] == ["OpenAI releases a new model update"]


def test_render_markdown_includes_sources_and_fallback_note():
    item = daily.NewsItem(
        title="Anthropic announces model safety research",
        url="https://example.com/safety",
        source="Example",
        summary="A research update about AI model evaluations.",
        published="2026-06-01T00:00:00+00:00",
    )

    markdown = daily.render_markdown(
        report_date="2026-06-01",
        generated_at=datetime(2026, 6, 1, tzinfo=timezone.utc),
        items=[item],
        source_errors=["Bad Feed: timed out"],
        model_used=None,
    )
    report_title = daily.zh("\\u6bcf\\u65e5 AI \\u8981\\u95fb")
    no_key_label = daily.zh("\\u672a\\u914d\\u7f6e")

    assert f"# {report_title} - 2026-06-01" in markdown
    assert "Anthropic announces model safety research" in markdown
    assert "https://example.com/safety" in markdown
    assert f"{no_key_label} `OPENAI_API_KEY`" in markdown
    assert "Bad Feed: timed out" in markdown
