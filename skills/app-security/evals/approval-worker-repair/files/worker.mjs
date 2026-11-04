// Synthetic local evaluation fixture. Never deploy.
import { readFileSync, writeFileSync, existsSync } from 'node:fs'
export function openWorker(file) {
  const state = existsSync(file) ? JSON.parse(readFileSync(file, 'utf8')) :
    { owners: { alice: true, bob: true }, jobs: {}, receipts: [], next: 0 }
  const save = () => writeFileSync(file, JSON.stringify(state))
  const own = (owner, id) => state.jobs[id]?.owner === owner
  save()
  return {
    queue(owner, body) {
      if (!state.owners[owner]) return { status: 403 }
      const id = String(++state.next)
      state.jobs[id] = { owner, recipient: body.recipient, text: body.text, approved: false, cancelled: false, delivered: false }
      save(); return { status: 202, id }
    },
    edit(owner, id, body) {
      if (!own(owner, id) || !state.owners[owner]) return { status: 403 }
      Object.assign(state.jobs[id], { recipient: body.recipient, text: body.text })
      save(); return { status: 200 }
    },
    approve(owner, id) {
      if (!own(owner, id) || !state.owners[owner]) return { status: 403 }
      state.jobs[id].approved = true
      save(); return { status: 200 }
    },
    revoke(owner) { state.owners[owner] = false; save() },
    cancel(owner, id) {
      if (!own(owner, id)) return { status: 403 }
      state.jobs[id].cancelled = true; save(); return { status: 200 }
    },
    run(id) {
      const job = state.jobs[id]
      if (!job?.approved) return { status: 403 }
      state.receipts.push({ id, owner: job.owner, recipient: job.recipient, text: job.text })
      job.delivered = true
      save(); return { status: 200 }
    },
    snapshot() { return structuredClone(state) },
  }
}
