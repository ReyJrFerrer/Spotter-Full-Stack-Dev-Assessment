# Wiki Configuration

## Structure

| Path | Purpose |
|---|---|
| `raw/` | Immutable source documents |
| `raw/articles/` | Web articles, blog posts |
| `raw/papers/` | Academic papers |
| `raw/notes/` | Personal notes, clippings |
| `wiki/` | Generated articles |
| `wiki/concepts/` | Concept pages |
| `wiki/references/` | Reference pages |
| `wiki/entities/` | Entity pages |

## Conventions

### Page Sizing
- Keep articles under ~200 lines (avoid timeout on large writes)
- Write skeleton first (frontmatter + headers), then append sections with Edit

### YAML Frontmatter
Every `.md` file must have:

```yaml
---
title: "Page Title"
type: concept|topic|reference|source  # depending on file location
summary: "One-line summary"
tags: [tag1, tag2]
date: 2026-06-22
confidence: high|medium|low
sources: []  # paths to raw/ files for wiki articles
---
```

### Cross-References
Use dual format on every link:

```
[[slug|Name]] ([Name](../category/slug.md))
```

### Log Format
```
## [YYYY-MM-DD] operation | Description
```

Parseable with: `grep "^## \[" log.md | tail -5`

## Operations Guide

See `.opencode/skills/llm-wiki/SKILL.md` for full workflow details.

| Operation | Trigger | When |
|---|---|---|
| Ingest | User shares a source | On user request |
| Query | User asks about knowledge in wiki | On user request |
| Lint | Health check | Periodically (every 7+ days) |
| Compile | After 5+ uncompiled sources | Suggested after ingest |
