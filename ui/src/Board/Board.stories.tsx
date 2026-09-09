import { Bot, CalendarClock, MessageSquare } from 'lucide-react'
import { Board, type BoardColumn } from './Board'

export default { title: 'Board' }

const wrap = { padding: 16, background: 'var(--bg)' }

const columns: BoardColumn[] = [
  {
    id: 'backlog',
    title: 'Backlog',
    cards: [
      { id: 'c1', title: 'Repurpose catalog to work landscape', badges: [{ label: 'Ssot' }] },
      {
        id: 'c2',
        title: 'Wire MCP server to the board API',
        badges: [{ label: 'Mcp' }, { label: 'High', tone: 'danger' }],
      },
      { id: 'c3', title: 'Decide attachment flow for cards' },
    ],
  },
  {
    id: 'doing',
    title: 'Doing',
    cards: [
      {
        id: 'c4',
        title: 'First iteration of the kanban board',
        badges: [{ label: 'Ui', tone: 'accent' }],
        meta: (
          <>
            <CalendarClock /> Friday
          </>
        ),
      },
    ],
  },
  {
    id: 'waiting',
    title: 'Waiting',
    cards: [
      {
        id: 'c5',
        title: 'License renewal quote from vendor',
        badges: [{ label: 'Waiting on reply', tone: 'warn' }],
        meta: (
          <>
            <MessageSquare /> 2 comments
          </>
        ),
      },
    ],
  },
  {
    id: 'done',
    title: 'Done',
    cards: [
      {
        id: 'c6',
        title: 'Nightly graph sync automation',
        badges: [{ label: 'Automated', tone: 'success' }],
        meta: (
          <>
            <Bot /> yani
          </>
        ),
      },
      { id: 'c7', title: 'Scaffold ssot-api with Neo4j' },
    ],
  },
]

export const Default = () => (
  <div style={wrap}>
    <Board columns={columns} onCardClick={() => {}} onCardMove={() => {}} />
  </div>
)

export const EmptyColumn = () => (
  <div style={wrap}>
    <Board
      columns={[
        { id: 'todo', title: 'To do', cards: [{ id: 'c1', title: 'Only card on the board' }] },
        { id: 'doing', title: 'Doing', cards: [] },
        { id: 'done', title: 'Done', cards: [] },
      ]}
    />
  </div>
)

export const ReadOnly = () => (
  <div style={wrap}>
    <Board
      columns={[
        {
          id: 'doing',
          title: 'Doing',
          cards: [
            { id: 'c1', title: 'Cards without callbacks render as plain tiles' },
            { id: 'c2', title: 'No hover, no grab cursor', badges: [{ label: 'Read only' }] },
          ],
        },
      ]}
    />
  </div>
)
