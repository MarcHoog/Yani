import type { ReactNode } from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import './Markdown.css'

export type MarkdownProps = { children: string; empty?: string }

const components = {
  a: ({ children, href }: { children?: ReactNode; href?: string }) => (
    <a href={href} target="_blank" rel="noreferrer noopener">
      {children}
    </a>
  ),
}

export function Markdown({ children, empty = '-' }: MarkdownProps) {
  if (!children.trim()) return <div className="y-md y-md--empty">{empty}</div>

  return (
    <div className="y-md">
      <ReactMarkdown remarkPlugins={[remarkGfm]} components={components}>
        {children}
      </ReactMarkdown>
    </div>
  )
}
