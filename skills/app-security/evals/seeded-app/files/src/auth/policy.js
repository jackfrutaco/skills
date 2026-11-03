import { query } from '../db.js'

export function isMember(userId, workspaceId) {
  return query('SELECT * FROM members WHERE userId = ?', [userId])
    .some((m) => m.workspaceId === workspaceId)
}

export function memberRole(userId, workspaceId) {
  return query('SELECT * FROM members WHERE userId = ?', [userId])
    .find((m) => m.workspaceId === workspaceId)?.role ?? null
}

// The single read policy for documents.
export function canReadDoc(userId, doc) {
  return Boolean(doc) && isMember(userId, doc.workspaceId)
}
