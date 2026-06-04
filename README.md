# AI Daily

AI Daily 是一个由 GitHub Actions 自动生成的 AI 行业日报仓库。工作流会每天抓取多个 AI 相关 RSS 信息源，筛选新闻条目，并生成 Markdown 格式的中文日报到 `reports/` 目录。

## 自动化工作流

仓库配置了 `.github/workflows/ai-daily.yml`，工作流名称为 **AI Daily Report**。

触发方式：

- 定时触发：每天 `00:30 UTC` 运行一次，对应北京时间 `08:30`。
- 手动触发：可在 GitHub Actions 页面通过 `workflow_dispatch` 手动运行。

执行内容：

1. 检出仓库代码。
2. 使用 Python 3.12 环境。
3. 执行日报生成脚本：

   ```bash
   python scripts/generate_ai_daily.py --date "$(TZ=Asia/Shanghai date +%F)"
   ```

4. 将生成或更新的 `reports/` 文件提交回 `main` 分支。
5. 如果没有文件变化，则跳过提交。

## 日报生成逻辑

核心脚本位于 `scripts/generate_ai_daily.py`。

脚本会从以下来源抓取 RSS 内容：

- OpenAI Blog
- Anthropic News
- Google DeepMind Blog
- Meta AI Blog
- Microsoft AI Blog
- NVIDIA Blog AI
- Hugging Face Blog
- MIT Technology Review AI
- VentureBeat AI

随后脚本会根据 AI 相关关键词筛选新闻，例如 `AI`、`agent`、`LLM`、`GPT`、`Claude`、`Gemini`、`人工智能`、`大模型` 等。

## OpenAI 配置

如果仓库配置了 `OPENAI_API_KEY`，脚本会调用 OpenAI Responses API，把筛选后的新闻整理成中文 Markdown 日报。

需要配置的 GitHub Secret：

- `OPENAI_API_KEY`：OpenAI API Key。

可选 GitHub Variable：

- `OPENAI_MODEL`：用于摘要生成的模型，默认值为 `gpt-4.1-mini`。

如果没有配置 `OPENAI_API_KEY`，脚本仍会生成基础版日报，内容来自 RSS 标题和摘要，不会调用模型生成深度整理。

## 输出文件

日报默认输出到 `reports/` 目录，文件名格式为：

```text
YYYY-MM-DD-ai-daily.md
```

例如：

```text
reports/2026-06-04-ai-daily.md
```

## 本地运行

可在本地直接运行：

```bash
python scripts/generate_ai_daily.py --date 2026-06-04
```

也可以指定输出目录：

```bash
python scripts/generate_ai_daily.py --date 2026-06-04 --output-dir reports
```

如需启用 OpenAI 摘要生成，请先设置环境变量：

```bash
export OPENAI_API_KEY="your_api_key"
export OPENAI_MODEL="gpt-4.1-mini"
```

Windows PowerShell 示例：

```powershell
$env:OPENAI_API_KEY="your_api_key"
$env:OPENAI_MODEL="gpt-4.1-mini"
python scripts/generate_ai_daily.py --date 2026-06-04
```

## 说明

本仓库的主要内容由 GitHub Actions 自动维护。日报内容依赖 RSS 源、网络可用性和 OpenAI API 配置情况；重要决策前请以原始来源链接为准。