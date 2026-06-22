# Ingestion Workflow

## Source Types

| Type | Directory | Example |
|---|---|---|
| Article | `raw/articles/` | Blog post, news article |
| Paper | `raw/papers/` | Academic paper, arxiv |
| Note | `raw/notes/` | Personal notes, meeting notes |
| Web page | `raw/articles/` | Any web content |

## Ingestion Flow

1. **Identify source type** from user input (URL, file path, pasted text)
2. **Fetch/read** the content
   - URLs: use `webfetch` tool
   - Files: use `read` tool
   - Text: accept directly
3. **Extract metadata**: title, author, date, url, tags
4. **Discuss key takeaways** with user (optional but recommended)
5. **Write to raw**: `raw/{type}/{slug}.md` with YAML frontmatter
6. **Update or create wiki articles** that this source touches
7. **Update `_index.md`** — add entry for new source
8. **Append to `log.md`**

## Raw File Format

```markdown
---
title: "Article Title"
type: article
source: "https://example.com/article"
date: 2026-06-22
author: "Author Name"
tags: [tag1, tag2]
confidence: medium
---

Content of the source document...

Key points extracted during ingestion...
```

## Wiki Article Format

```markdown
---
title: "Concept Name"
type: concept
summary: "One-line summary"
tags: [tag1, tag2]
confidence: high
sources:
  - raw/articles/source-1.md
  - raw/papers/paper-1.md
date: 2026-06-22
---

# Concept Name

Synthesized content drawing from multiple sources...

[[related-concept|Related Concept]] ([Related Concept](wiki/concepts/related-concept.md))
```

## After Ingestion

- Check if 5+ uncompiled sources exist → suggest compilation
- Ask user if they want to explore related topics
- Ask user if any existing articles need updating
