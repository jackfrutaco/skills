const TTL_MS = 24 * 60 * 60 * 1000
const entries = new Map()

export const shareCache = {
  get(key) {
    const hit = entries.get(key)
    if (!hit || hit.expires < Date.now()) return null
    return hit.value
  },
  set(key, value) { entries.set(key, { value, expires: Date.now() + TTL_MS }) },
}
