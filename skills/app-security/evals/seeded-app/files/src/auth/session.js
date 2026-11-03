import { createHmac, timingSafeEqual } from 'node:crypto'

const SECRET = process.env.SESSION_SECRET ?? 'test-only-session-secret'

export function sign(userId) {
  const mac = createHmac('sha256', SECRET).update(userId).digest('hex')
  return `${userId}.${mac}`
}

// Returns { userId } for a valid signed cookie, otherwise null.
export function getSession(req) {
  const raw = req.cookies?.session
  if (!raw) return null
  const [userId, mac] = raw.split('.')
  const expected = createHmac('sha256', SECRET).update(userId).digest('hex')
  if (!mac || mac.length !== expected.length) return null
  if (!timingSafeEqual(Buffer.from(mac), Buffer.from(expected))) return null
  return { userId }
}
