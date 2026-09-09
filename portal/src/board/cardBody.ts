export type CardTodo = { id: string; text: string; done: boolean }
export type CardComment = { id: string; text: string; at: string }
export type CardDetail = { description: string; todos: CardTodo[]; comments: CardComment[] }

export const emptyDetail: CardDetail = { description: '', todos: [], comments: [] }

export function readCardDetail(body: Record<string, unknown>): CardDetail {
  return {
    description: typeof body.description === 'string' ? body.description : '',
    todos: Array.isArray(body.todos) ? body.todos.filter(isTodo) : [],
    comments: Array.isArray(body.comments) ? body.comments.filter(isComment) : [],
  }
}

export function writeCardDetail(body: Record<string, unknown>, detail: CardDetail): Record<string, unknown> {
  return { ...body, description: detail.description, todos: detail.todos, comments: detail.comments }
}

export function newId(): string {
  return crypto.randomUUID()
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null
}

function isTodo(value: unknown): value is CardTodo {
  return isRecord(value) && typeof value.id === 'string' && typeof value.text === 'string' && typeof value.done === 'boolean'
}

function isComment(value: unknown): value is CardComment {
  return isRecord(value) && typeof value.id === 'string' && typeof value.text === 'string' && typeof value.at === 'string'
}
