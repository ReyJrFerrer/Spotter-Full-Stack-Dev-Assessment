---
name: llm-wiki
description: >
  Build and maintain a persistent, interlinked markdown knowledge base.
  Use it to ingest sources (articles, papers, notes), query the wiki
  for synthesized answers, lint for structural health, and compile new
  article pages from raw sources. Based on Andrej Karpathy's LLM Wiki
  pattern (April 2026).
---

# LLM Wiki Skill

You manage a compounding markdown wiki. Source documents are ingested into
`.wiki/raw/`, then incrementally compiled into interconnected articles under
`.wiki/wiki/`. You are both the compiler and the query engine.

## Architecture

Three layers:

- **Raw sources** (`.wiki/raw/`) — immutable source documents. Articles, papers,
  notes. You read from these but never modify them.
- **The wiki** (`.wiki/wiki/`) — generated markdown files. Summaries, concept
  pages, entity pages, cross-references. You own this layer entirely.
- **The schema** (this file + `.wiki/config.md`) — conventions telling you how
  the wiki is structured and what workflows to follow.

## Core Principles

1. **Raw is immutable.** Once in `.wiki/raw/`, sources are never modified.
2. **Articles are synthesized, not copied.** A wiki article draws from multiple
   sources and connects to other concepts.
3. **YAML frontmatter on every page.** Fields: `title`, `summary`, `tags`,
   `date`, `confidence` (high/medium/low), `source`.
4. **Cross-references via wikilinks** — use `[[slug|Name]]` with markdown
   `[Name](path)` on the same line.
5. **Incremental compilation.** Process only new sources by default.
6. **Honest gaps.** If the wiki doesn't know, say so. Never hallucinate.
7. **Indexes are derived caches.** The `.md` files are source of truth;
   `_index.md` is rebuilt when stale.

## Operations

### Ingest

Flow: User provides a source (URL, file, text) → fetch/read → extract metadata
→ discuss key takeaways with user → write to `.wiki/raw/{type}/` → update
relevant wiki articles → update `_index.md` → append to `log.md`.

A single source might touch 5-15 wiki pages. Prefer ingesting one at a time
with user involvement.

### Query

Flow: Read `_index.md` to find relevant articles → read articles → follow
cross-references → Grep for additional matches → synthesize answer with
citations → note gaps.

Good answers can be filed back into the wiki as new pages — comparisons,
analyses, connections discovered during a query are valuable and shouldn't
disappear into chat history.

### Lint

Periodically health-check the wiki:
- Contradictions between pages
- Stale claims superseded by newer sources
- Orphan pages with no inbound links
- Missing cross-references
- Broken wikilinks
- Confidence: flag `low` articles for review

Suggest new questions to investigate and new sources to look for.

### Compile

Flow: Survey uncompiled sources in `raw/` → plan articles → classify
(concept/topic/reference) → write articles with cross-references → update
indexes.

## Indexing and Logging

- **`_index.md`** — content-oriented catalog of everything in the wiki. Each
  page listed with link, one-line summary, and metadata. Organized by category.
  Updated on every ingest.
- **`log.md`** — chronological record. Append-only. Format:
  `## [YYYY-MM-DD] operation | Description`. Parseable with
  `grep "^## \[" log.md | tail -5`.

## File Structure

```
.wiki/
├── _index.md          # Wiki catalog
├── log.md             # Activity log
├── config.md          # Schema and conventions
├── raw/               # Immutable source documents
│   ├── articles/      # Web articles, blog posts
│   ├── papers/        # Academic papers
│   └── notes/         # Personal notes, clippings
└── wiki/              # Generated articles
    ├── concepts/      # Concept pages
    ├── references/    # Reference pages
    └── entities/      # Entity pages
```

## Confidence Scoring

| Level | Meaning |
|---|---|
| `high` | Multiple peer-reviewed sources agree |
| `medium` | Single source, or sources partially agree |
| `low` | Anecdotal, single non-peer-reviewed source |

## Compilation Nudge

If 5+ uncompiled sources exist after an ingestion, suggest:
"You have N uncompiled sources. Ask me to compile them."
