import { useState } from 'react'
import { MarkdownInput } from './MarkdownInput'

export default { title: 'MarkdownInput' }

const wrap = { maxWidth: 480, padding: 20, borderRadius: 16, background: 'var(--surface)' }

export const Writing = () => {
  const [value, setValue] = useState('Ship the **panel**, then wire `todo-api`.\n\n- markdown in the description\n- markdown in comments')

  return (
    <div style={wrap}>
      <MarkdownInput value={value} onChange={setValue} />
    </div>
  )
}

export const EmptyState = () => {
  const [value, setValue] = useState('')

  return (
    <div style={wrap}>
      <MarkdownInput value={value} onChange={setValue} placeholder="Describe the card" rows={4} />
    </div>
  )
}
