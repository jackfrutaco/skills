const pending = []
export function enqueue(jobId) { pending.push(jobId) }
export function drain(handler) { while (pending.length) handler(pending.shift()) }
