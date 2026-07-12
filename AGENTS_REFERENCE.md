# Personal Coach — Architecture & Reference

## Memory layout (`coach/memory/`)

| File | Format |
|---|---|
| `meta.md` | YAML frontmatter: agent metadata, updated_at |
| `goals.md` | YAML list with id, title, created, target_date, metric, notes |
| `habits.md` | YAML list with id, title, cue, action, reward |
| `resources.md` | YAML list of resource groups |
| `profile.md` | User profile (YAML frontmatter + Markdown body) |
| `checkpoint.md` | Coaching checkpoint with phase, topic, next_task |
| `sessions/session-YYYYMMDD-HHMMSS.md` | YAML frontmatter (id, date, skill, duration_min, rating, notes, tags) + body |
| `daily/YYYY-MM-DD.md` | Daily note with brain dump, tasks, notes, session log, summary |
| `inbox/captures/` | Loose items waiting to be organized |
| `inbox/processed/` | Archived processed inbox items |
| `templates/daily-note.md` | Template for new daily notes |
| `conversations/conv-YYYYMMDD-HHMMSS.md` | Thinking partner conversation logs |
| `decisions.md` | Master log of all decisions made |
| `rates.json` | Rate card for quotation maker |
| `quotations/` | Generated quotation XLSX files |
| `backups/memory-backup-YYYYMMDD-HHMMSS.zip` | Timestamped ZIP backups |

Session files are sorted reverse-chronologically by stem.

## Workflow

1. Start session → `session_hooks.py pre` → propose next task.
2. User completes task → `store_session.py` saves + auto-triggers `post_session` (insights + index).
3. Periodically run `extract_insights.py` (auto-runs after every session).
4. Run `evolve_skill.py` when multiple insights cluster.
5. Remember everything — never let the user repeat context.

### Daily Workflow (Morning → Evening)

- **Morning**: `morning_plan.py "brain dump..."` — creates daily note, auto-categorizes
- **During Day**: Capture to `memory/inbox/captures/`, process with `inbox_processor.py`
- **Evening**: `daily_review.py` — marks completed tasks, migrates incomplete, summary
- **Weekly**: `weekly_synthesis.py` — 7-day pattern analysis, wins, stalls, skill breakdown
- **Stuck?**: `thinking_partner.py "problem"` — Socratic questioning

## Output directory (`coach/work/`)

| Directory | Content |
|---|---|
| `content/blogs/` | Published blog posts and guides |
| `content/schemas/` | PHP schema markup MU plugins |
| `content/fixes/` | On-page SEO fix copy files |
| `content/social/` | Reddit posts and social content |
| `content/facebook/` | Facebook catalog, shop guides |
| `content/drafts/` | Drafts, notes, reference files |
| `reports/` | Daily and project work reports |
| `research/` | Audits, competitor analysis, keyword research |
| `n8n/` | n8n workflow JSON exports |
| `scripts/` | Standalone scripts and tests |

## Plan Lifecycle

Plans in `process/plans/` with subdirectories: `active/`, `completed/`, `backlog/`.
- Create: `py -3 coach/tools/new_plan.py "<title>"`
- Naming: `plan-title-YYYYMMDD-HHMMSS.md`
- Context router: `process/context/all-context.md`

## LightRAG

LightRAG v1.5.1 (`pip install lightrag-hku`) provides graph-based RAG indexing.
- **Auto-fallback**: If Ollama is not running, gracefully falls back to TF-IDF.
- **Storage**: `coach/memory/.lightrag/`
- **Prerequisite**: Ollama running with `nomic-embed-text` and `llama3.2:3b` models
- `search_index()` supports modes: `hybrid` (default), `local`, `global`, `tfidf`

## MCP Servers (opencode.json)

| Server | Command | Purpose |
|---|---|---|
| `n8n-mcp` | `n8n-mcp` | n8n workflow automation |
| `coach` | `py -3 coach/tools/mcp_server.py` | Memory, goals, habits, sessions |

## ECC — Everything Claude Code

ECC (`.opencode/ecc-temp/`) provides 240+ development skills, 35 commands, and specialized agents.

Commands: `/plan`, `/code-review`, `/security`, `/verify`, `/learn`, `/eval`, `/checkpoint`, `/orchestrate`, `/evolve`

Agents: `planner`, `code-reviewer`, `python-reviewer`, `security-reviewer`, `doc-updater`, `harness-optimizer`

## claude-mem
Installed at `~/.claude/plugins/marketplaces/thedotmack/plugin/`.
- Search: `npx claude-mem search <query>` (requires Bun)

## n8n-mcp
Installed globally (`n8n-mcp@2.57.2`). Runs as stdio MCP server via `opencode.json`.

## Skills (`.opencode/skills/`)

Skills live in `.opencode/skills/<name>/SKILL.md`. **66+ skills installed**:

| Source | Skills | Coverage |
|---|---|---|
| `coreyhaines31/marketingskills` | 43 | SEO, CRO, copywriting, analytics, ads, email, social, schema, pricing, referrals, onboarding, etc. |
| `obra/superpowers` | 3 | writing-plans, executing-plans, writing-skills |
| `NVIDIA/skills` | 1 | skill-evolution |
| `awrshift/claude-memory-kit` | 1 | memory-kit |
| Custom (local) | 5 | web-development, wordpress, hugo, frontend-security, prompt-master |
| `Egonex-AI/Understand-Anything` | 8 | understand, understand-chat, understand-dashboard, understand-diff, understand-domain, understand-explain, understand-knowledge, understand-onboard |

ECC adds **240+ additional skills** at `.opencode/ecc-temp/skills/`.

## Skill Registry (Quick Reference)

| Skill | Trigger Keywords |
|---|---|
| `seo-audit` | seo, search engine, ranking, organic, google |
| `programmatic-seo` | programmatic seo, seo at scale |
| `schema` | schema, structured data, json-ld, rich results |
| `ai-seo` | ai seo, llm, chatgpt, ai overviews |
| `content-strategy` | content strategy, editorial, content plan |
| `copywriting` | copy, writing, headlines, persuasive, conversion copy |
| `analytics` | analytics, ga4, tracking, metrics |
| `pricing` | pricing, monetization, tiers |
| `launch` | launch, go-to-market, gtm |
| `cro` | conversion, cro, a/b test, optimize, funnel |
| `site-architecture` | site architecture, sitemap, information architecture |
| `referrals` | referral, viral, word of mouth |
| `web-development` | html, css, javascript, build website, create site, landing page |
| `wordpress` | wordpress, woocommerce, wp theme, plugin, elementor |
| `hugo` | hugo, hugo theme, hugo templates, static site generator |
| `deep-research` | research, deep dive, investigate, competitive research |
| `n8n-workflows` | n8n, automation, workflow automation, zapier |
| `frontend-design` | premium design, modern ui, beautiful interface |
| `d3-visualization` | d3, chart, graph, data visualization, dashboard |

## Project: safehome → aslielectronics.com

- **Repo:** `github.com/ashim-khan-root/safehome`
- **Local clone:** `personal-coach/safehome/`
- **Deployment:** GitHub main → Cloudflare Pages → **aslielectronics.com**
- **Blog source:** `safehome/content/blog/` (Hugo markdown)
- **Format:** YAML frontmatter with title, date, author, description, summary, tags, categories, draft, weight
- **Publish:** `git add`, `git commit`, `git push` → Cloudflare auto-deploys
- Always write blog posts into the safehome repo, not as loose drafts.

## Blog Writing Convention (Secuview)

Always include this RankMath-optimized block at the top of blog posts:

```yaml
---
rankmath_title: "Primary Keyword | Secondary Keyword - Secuview Qatar"
rankmath_description: "160-char meta description with primary keyword, CTA, and location. Ends with period."
rankmath_permalink: /blog/keyword-rich-slug/
rankmath_focus_keyword: "primary keyword"
rankmath_related_keywords: [keyword1, keyword2, keyword3]
---
```

Rules:
- **Title**: 50-60 chars, front-load primary keyword, include "Qatar" and/or "Secuview"
- **Description**: 150-160 chars, include keyword + CTA + location, end with period
- **Permalink**: lowercase, hyphens, target keyword only (no stop words)
- **Content**: H2/H3 structure, FAQ section at bottom, internal links to product categories, Qatar-specific (pricing, climate, vendors)
