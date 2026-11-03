import { insert, query } from '../db.js'
import { getSession } from '../auth/session.js'
import { enqueue } from '../jobs/queue.js'

// POST /exports { docId } -> 202 { jobId }
export function requestExport(req) {
  const session = getSession(req)
  if (!session) return { status: 401 }
  const [user] = query('SELECT * FROM users WHERE id = ?', [session.userId])
  const job = insert('jobs', {
    id: `job_${Date.now().toString(36)}`,
    docId: String(req.body.docId),
    requestedBy: session.userId,
    notifyEmail: user.email,
    status: 'queued',
  })
  enqueue(job.id)
  return { status: 202, body: { jobId: job.id } }
}

// GET /exports/:jobId -> the requester's own job result only.
export function getExport(req) {
  const session = getSession(req)
  if (!session) return { status: 401 }
  const [job] = query('SELECT * FROM jobs WHERE id = ?', [req.params.jobId])
  if (!job || job.requestedBy !== session.userId) return { status: 404 }
  return { status: 200, body: { status: job.status, result: job.result } }
}
