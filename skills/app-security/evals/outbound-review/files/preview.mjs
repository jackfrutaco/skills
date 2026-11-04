// Synthetic local evaluation fixture. Never deploy.
const fixtureHeader = 'FIXTURE_PRIVATE_HEADER_783'
const hops = new Map([
  ['https://previews.example/ok', { body: 'ok' }],
  ['https://previews.example/next', { redirect: 'https://internal.example/private' }],
  ['https://internal.example/private', { body: 'synthetic-internal-data' }],
])
export function createPreview() {
  const calls = []
  function transport(url, headers, left = 2) {
    calls.push({ url, forwardedCredential: Boolean(headers.authorization) })
    const next = hops.get(url)
    if (!next) return { status: 404 }
    if (next.redirect && left > 0) return transport(next.redirect, headers, left - 1)
    return { status: 200, body: (next.body ?? '').slice(0, 65536) }
  }
  return {
    calls,
    preview(raw) {
      let url
      try { url = new URL(raw) } catch { return { status: 400 } }
      if (url.origin !== 'https://previews.example' || url.username || url.password) return { status: 403 }
      return transport(url.href, { authorization: fixtureHeader })
    },
  }
}
if (process.argv.includes('--probe')) {
  const app = createPreview()
  const valid = app.preview('https://previews.example/ok')
  const direct = app.preview('https://internal.example/private')
  const redirected = app.preview('https://previews.example/next')
  console.log(JSON.stringify({ valid, direct, redirected, calls: app.calls }, null, 2))
}
