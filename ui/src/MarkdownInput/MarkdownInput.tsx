import { useState } from 'react'
import { Markdown } from '../Markdown/Markdown'
import { Textarea } from '../Field/Field'
import './MarkdownInput.css'

export type MarkdownInputProps = {
  value: string
  onChange: (value: string) => void
  placeholder?: string
  rows?: number
  autoFocus?: boolean
}

export function MarkdownInput({ value, onChange, placeholder, rows = 6, autoFocus }: MarkdownInputProps) {
  const [preview, setPreview] = useState(false)

  return (
    <div className="y-mdin">
      <div className="y-mdin-tabs" role="group" aria-label="Markdown mode">
        <button type="button" className="y-mdin-tab" aria-pressed={!preview} onClick={() => setPreview(false)}>
          Write
        </button>
        <button type="button" className="y-mdin-tab" aria-pressed={preview} onClick={() => setPreview(true)}>
          Preview
        </button>
      </div>
      {preview ? (
        <div className="y-mdin-preview">
          <Markdown empty="Nothing to preview">{value}</Markdown>
        </div>
      ) : (
        <Textarea
          value={value}
          rows={rows}
          placeholder={placeholder}
          autoFocus={autoFocus}
          onChange={(event) => onChange(event.target.value)}
        />
      )}
    </div>
  )
}
