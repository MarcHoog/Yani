import { SquareKanban } from 'lucide-react'
import { Sidebar } from '@yani/ui'
import { BoardPage } from './board/BoardPage'

export function App() {
  return (
    <div className="app">
      <Sidebar
        brand="Yani"
        tag="personal"
        groups={[{ items: [{ label: 'Board', href: '/', icon: <SquareKanban />, active: true }] }]}
      />
      <main className="app-main">
        <BoardPage />
      </main>
    </div>
  )
}
