import { Markdown } from './Markdown'

export default { title: 'Markdown' }

const wrap = { maxWidth: 520, padding: 20, borderRadius: 16, background: 'var(--surface)' }

const source = `## Board panel

Cards keep their long form here, written in **markdown** with \`inline code\`.

- lists work
- so do [links](https://example.com)
- and ~~strikethrough~~

1. ordered too
2. second

> Rationale lives in the card, not in a wiki page.

\`\`\`sql
SELECT id, title FROM cards WHERE column_id = $1;
\`\`\`

| Store | Holds |
|---|---|
| Postgres | Cards |
| Neo4j | Identity |
`

export const Prose = () => (
  <div style={wrap}>
    <Markdown>{source}</Markdown>
  </div>
)

export const Empty = () => (
  <div style={wrap}>
    <Markdown>{''}</Markdown>
  </div>
)
