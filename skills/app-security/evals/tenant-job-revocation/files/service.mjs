// Deliberately vulnerable, isolated evaluation fixture. Never deploy.
export function createService() {
  const memberships = new Map([['alice', new Set(['red'])], ['bob', new Set(['blue'])]])
  const rows = new Map([['red', ['red-report']], ['blue', ['blue-report']]])
  const jobs = new Map()
  const effects = []
  let nextId = 0
  return {
    effects,
    exportNow(session, body) {
      if (!session?.userId || !memberships.has(session.userId)) return { status: 401 }
      const tenant = body.tenantId
      if (!rows.has(tenant)) return { status: 404 }
      effects.push({ userId: session.userId, tenant })
      return { status: 200, rows: rows.get(tenant) }
    },
    enqueue(session, tenant) {
      if (!memberships.get(session?.userId)?.has(tenant)) return { status: 403 }
      const id = String(++nextId)
      jobs.set(id, { userId: session.userId, tenant, allowedAtCreation: true })
      return { status: 202, id }
    },
    revoke(userId, tenant) { memberships.get(userId)?.delete(tenant) },
    run(id) {
      const job = jobs.get(id)
      if (!job?.allowedAtCreation) return { status: 403 }
      effects.push({ userId: job.userId, tenant: job.tenant })
      return { status: 200, rows: rows.get(job.tenant) }
    },
  }
}

if (process.argv.includes('--probe')) {
  const app = createService()
  const alice = { userId: 'alice' }
  const allowed = app.exportNow(alice, { tenantId: 'red' })
  const crossTenant = app.exportNow(alice, { tenantId: 'blue' })
  const pending = app.enqueue(alice, 'red')
  app.revoke('alice', 'red')
  const afterRevocation = app.run(pending.id)
  console.log(JSON.stringify({ allowed, crossTenant, afterRevocation, effects: app.effects }, null, 2))
}
