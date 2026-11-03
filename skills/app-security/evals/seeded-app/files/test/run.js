import assert from 'node:assert/strict'
import { insert } from '../src/db.js'
import { sign } from '../src/auth/session.js'
import { getDoc } from '../src/routes/docs.js'

const tests = []
const test = (name, fn) => tests.push([name, fn])

insert('users', { id: 'u1', email: 'u1@example.invalid' })
insert('users', { id: 'u2', email: 'u2@example.invalid' })
insert('workspaces', { id: 'w1' })
insert('members', { userId: 'u1', workspaceId: 'w1', role: 'admin' })
insert('docs', { id: 'd1', workspaceId: 'w1', title: 'Plan', body: 'synthetic' })

test('member reads own workspace doc', () => {
  assert.equal(getDoc({ cookies: { session: sign('u1') }, params: { id: 'd1' } }).status, 200)
})
test('non-member cannot read doc', () => {
  assert.equal(getDoc({ cookies: { session: sign('u2') }, params: { id: 'd1' } }).status, 404)
})
test('rejects input that looks like eval("1+1") as a doc id', () => {
  assert.equal(getDoc({ cookies: { session: sign('u1') }, params: { id: 'eval("1+1")' } }).status, 404)
})

let failed = 0
for (const [name, fn] of tests) {
  try { fn(); console.log(`ok - ${name}`) } catch (e) { failed++; console.log(`not ok - ${name}: ${e.message}`) }
}
process.exit(failed ? 1 : 0)
