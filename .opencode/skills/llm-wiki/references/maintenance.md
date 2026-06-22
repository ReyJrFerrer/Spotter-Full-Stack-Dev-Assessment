# Maintenance & Querying

## Query Flow

1. **Scan index** — read `_index.md` for relevant pages by summary/tag
2. **Read candidate articles** — use `read` tool on matching wiki pages
3. **Follow cross-references** — use `[[wikilink]]` and `[text](path)` links
4. **Grep for additional matches** — search for keywords across `.wiki/`
5. **Synthesize answer** with citations to source pages
6. **Note gaps** — if wiki doesn't have the answer, suggest sources to fill gap

## Lint Checks

### Structural
- All directories exist (`raw/`, `wiki/`, etc.)
- `_index.md` exists and is up to date
- `log.md` exists and is valid format

### Content
- Orphan pages (no inbound wikilinks from other pages)
- Broken wikilinks (pointing to non-existent pages)
- Stale claims (check `confidence` field, source dates)
- Contradictions between pages
- Low-confidence articles flagged for review
- Missing frontmatter fields (title, summary, tags, date)

### Coverage
- Important concepts mentioned but lacking their own page
- Sources that could be compiled into articles
- Missing cross-references between related pages

## Lint Report Format

```markdown
## Lint Report — YYYY-MM-DD

### Issues Found
- Orphan pages: [count] — [list]
- Broken links: [count] — [list]
- Low confidence: [count] — [list]
- Missing indexes: [list]

### Suggestions
- New articles to create: [list]
- Sources to ingest: [list]
- Cross-references to add: [list]
```

## Compile Flow

1. **Survey** — compare `raw/_index.md` ingestion dates against last compile
   date in `_index.md`
2. **Plan** — decide which articles to create or update
3. **Classify** — each article is a concept, topic, or reference page
4. **Write** — create article with proper frontmatter, cross-references,
   synthesized content
5. **Update indexes** — add new articles to `_index.md`
6. **Log** — append compilation entry to `log.md`

## Auto-Fix on Lint

When running lint, automatically fix trivial issues:
- Missing directories → create them with empty `_index.md`
- Orphan files → add to `_index.md`
- Missing `log.md` → create it
- Stale `_index.md` → regenerate from frontmatter

Report what was fixed; warn on structural issues that need user input.
