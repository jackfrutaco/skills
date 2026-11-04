import { query } from '../db.js'
import { getSession } from '../auth/session.js'
import { canReadDoc } from '../auth/policy.js'
import { etagFor } from '../util/etag.js'

export function getDoc(req) {
  const session = getSession(req)
  if (!session) return { status: 401 }
  const [doc] = query('SELECT * FROM docs WHERE id = ?', [req.params.id])
  if (!canReadDoc(session.userId, doc)) return { status: 404 }
  return { status: 200, headers: { etag: etagFor(doc.body) }, body: doc }
}
