import { LogOut, SquareKanban } from 'lucide-react'
import { Sidebar } from '@yani/ui'
import { SIGN_OUT_PATH, signOut } from './auth/auth'
import { BoardPage } from './board/BoardPage'

export function App() {
  function navigate(href: string) {
    if (href === SIGN_OUT_PATH) void signOut()
  }

  return (
    <div className="app">
      <Sidebar
        brand="Yani"
        tag="operator"
        groups={[
          { items: [{ label: 'Board', href: '/', icon: <SquareKanban />, active: true }] },
          { items: [{ label: 'Sign out', href: SIGN_OUT_PATH, icon: <LogOut /> }] },
        ]}
        onNavigate={navigate}
      />
      <main className="app-main">
        <BoardPage />
      </main>
    </div>
  )
}
