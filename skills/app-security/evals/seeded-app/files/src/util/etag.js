import { createHash } from 'node:crypto'
// Cache validator only; not used for integrity or authentication.
export function etagFor(text) { return `"${createHash('md5').update(text).digest('hex')}"` }
