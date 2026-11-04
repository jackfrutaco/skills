import { insert, query } from '../db.js'
import { getSession } from '../auth/session.js'

// POST /admin/workspaces/:id/members { userId, role, actingRole }
export function addMember(req) {
  const session = getSession(req)
  if (!session) return { status: 401 }
  if (req.body.actingRole !== 'admin') return { status: 403 }
  const [workspace] = query('SELECT * FROM workspaces WHERE id = ?', [req.params.id])
  if (!workspace) return { status: 404 }
  insert('members', { userId: req.body.userId, workspaceId: workspace.id, role: req.body.role ?? 'member' })
  return { status: 201 }
}
