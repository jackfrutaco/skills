// GET /health: used by the public status page.
export function health() {
  return { status: 200, headers: { 'access-control-allow-origin': '*' }, body: { ok: true } }
}
