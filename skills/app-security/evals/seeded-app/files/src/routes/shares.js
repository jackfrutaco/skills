import { randomBytes } from 'node:crypto'
import { insert, query, remove } from '../db.js'
import { getSession } from '../auth/session.js'
import { canReadDoc } from '../auth/policy.js'
import { shareCache } from '../cache/share-cache.js'

// POST /docs/:id/shares -> public read-only link
export function createShare(req) {
  const session = getSession(req)
  if (!session) return { status: 401 }
  const [doc] = query('SELECT * FROM docs WHERE id = ?', [req.params.id])
  if (!canReadDoc(session.userId, doc)) return { status: 404 }
  const token = randomBytes(24).toString('base64url')
  insert('shares', { token, docId: doc.id, createdBy: session.userId })
  return { status: 201, body: { url: `/s/${token}` } }
}

// DELETE /shares/:token -> revoke
export function revokeShare(req) {
  const session = getSession(req)
  if (!session) return { status: 401 }
  const [share] = query('SELECT * FROM shares WHERE token = ?', [req.params.token])
  if (!share) return { status: 404 }
  const [doc] = query('SELECT * FROM docs WHERE id = ?', [share.docId])
  if (!canReadDoc(session.userId, doc)) return { status: 404 }
  remove('shares', 'token', share.token)
  return { status: 204 }
}

// GET /s/:token -> anonymous read
export function readShare(req) {
  const cached = shareCache.get(req.params.token)
  if (cached) return { status: 200, body: cached }
  const [share] = query('SELECT * FROM shares WHERE token = ?', [req.params.token])
  if (!share) return { status: 404 }
  const [doc] = query('SELECT * FROM docs WHERE id = ?', [share.docId])
  const view = { title: doc.title, body: doc.body }
  shareCache.set(req.params.token, view)
  return { status: 200, body: view }
}
