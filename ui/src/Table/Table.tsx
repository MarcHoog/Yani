import type { ReactNode } from 'react'
import './Table.css'

export type TableProps = { columns: string[]; rows: ReactNode[][]; empty?: string }

function cell(value: ReactNode) {
  if (value === null || value === undefined || value === '') return <span className="y-table-empty">-</span>
  return value
}

export function Table({ columns, rows, empty = 'Nothing here' }: TableProps) {
  return (
    <div className="y-table-wrap">
      <table className="y-table">
        <thead>
          <tr>
            {columns.map((column) => (
              <th key={column}>{column}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.length === 0 && (
            <tr>
              <td className="y-table-none" colSpan={columns.length}>
                {empty}
              </td>
            </tr>
          )}
          {rows.map((row, i) => (
            <tr key={i}>
              {row.map((value, j) => (
                <td key={j}>{cell(value)}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
