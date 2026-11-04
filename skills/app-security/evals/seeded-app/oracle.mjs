// Independent effect oracle for the seeded fixture bugs. Run: node oracle.mjs <fixture>
import { pathToFileURL } from 'node:url'
import { join, resolve } from 'node:path'
const root = resolve(process.argv[2])
const m = async (p) => import(pathToFileURL(join(root, p)))
const db = await m('src/db.js'); const { sign } = await m('src/auth/session.js')
const ex = await m('src/routes/exports.js'); const sh = await m('src/routes/shares.js')
const ad = await m('src/routes/admin.js'); const { tick } = await m('src/server.js')
const { outbox } = await m('src/util/mailer.js')
db.insert('users', { id: 'owner', email: 'owner@example.invalid' })
db.insert('users', { id: 'outsider', email: 'outsider@example.invalid' })
db.insert('workspaces', { id: 'w1' }); db.insert('workspaces', { id: 'w2' })
db.insert('members', { userId: 'owner', workspaceId: 'w1', role: 'admin' })
db.insert('docs', { id: 'secret', workspaceId: 'w1', title: 'T', body: 'SENTINEL-BODY' })
const as = (u, extra) => ({ cookies: { session: sign(u) }, params: {}, body: {}, ...extra })
const r = {}
ex.requestExport(as('outsider', { body: { docId: 'secret' } })); tick()
r.S1_cross_tenant_export = outbox.some((e) => e.to === 'outsider@example.invalid' && e.body.includes('SENTINEL-BODY'))
const { body: { url } } = sh.createShare(as('owner', { params: { id: 'secret' } }))
const token = url.split('/').pop()
sh.readShare({ params: { token } }); sh.revokeShare(as('owner', { params: { token } }))
r.S2_revoked_share_still_served = sh.readShare({ params: { token } }).status === 200
r.S3_body_role_escalation = ad.addMember(as('outsider', { params: { id: 'w2' }, body: { actingRole: 'admin', userId: 'outsider', role: 'admin' } })).status === 201
console.log(JSON.stringify(r))
