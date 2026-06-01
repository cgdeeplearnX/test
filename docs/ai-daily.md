# AI Daily Automation

This repository generates a daily AI news report with GitHub Actions.

## How it works

- Schedule: every day at 08:30 Asia/Shanghai time.
- Output: `reports/YYYY-MM-DD-ai-daily.md`.
- Sources: trusted RSS feeds from AI labs, developer platforms, and AI news outlets.
- Fallback: if `OPENAI_API_KEY` is not configured, the script still creates a basic report from RSS titles and summaries.
- Optional model summary: add `OPENAI_API_KEY` to repository secrets to generate a more polished Chinese Markdown report.

## Manual run

In GitHub, open **Actions > AI Daily Report > Run workflow**.

Local run:

```bash
python scripts/generate_ai_daily.py
```

## Optional configuration

- Secret: `OPENAI_API_KEY`
- Repository variable: `OPENAI_MODEL`, default `gpt-4.1-mini`

Generated reports should be treated as a reading aid. For important decisions, verify the original linked sources.
