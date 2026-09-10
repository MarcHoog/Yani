export const INBOX_DRAG_TYPE = 'application/x-yani-inbox-item'

export function readDescription(body: Record<string, unknown>): string {
  return typeof body.description === 'string' ? body.description : ''
}

export function writeDescription(body: Record<string, unknown>, description: string): Record<string, unknown> {
  return { ...body, description }
}
