import { query } from '../db.js'
import { sendEmail } from '../util/mailer.js'

// Runs outside the request: renders the document and emails it.
export function processExport(jobId) {
  const [job] = query('SELECT * FROM jobs WHERE id = ?', [jobId])
  if (!job || job.status !== 'queued') return
  const [doc] = query('SELECT * FROM docs WHERE id = ?', [job.docId])
  if (!doc) { job.status = 'failed'; return }
  job.result = `# ${doc.title}\n\n${doc.body}`
  job.status = 'done'
  sendEmail(job.notifyEmail, `Export: ${doc.title}`, job.result)
}
