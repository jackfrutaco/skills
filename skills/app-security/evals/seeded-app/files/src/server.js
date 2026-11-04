import { getDoc } from './routes/docs.js'
import { requestExport, getExport } from './routes/exports.js'
import { createShare, revokeShare, readShare } from './routes/shares.js'
import { addMember } from './routes/admin.js'
import { health } from './routes/health.js'
import { drain } from './jobs/queue.js'
import { processExport } from './jobs/export-worker.js'

export const routes = {
  'GET /docs/:id': getDoc,
  'POST /exports': requestExport,
  'GET /exports/:jobId': getExport,
  'POST /docs/:id/shares': createShare,
  'DELETE /shares/:token': revokeShare,
  'GET /s/:token': readShare,
  'POST /admin/workspaces/:id/members': addMember,
  'GET /health': health,
}

// The worker drains the queue every second in production.
export function tick() { drain(processExport) }
