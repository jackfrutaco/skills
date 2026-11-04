# Local notification fixture
Deliberately incomplete security; never deploy. Node built-ins only. The exported
`openWorker(file)` reads or creates a JSON store. Every state-changing method saves.
Delivery appends a receipt to that store; it never uses a network. Keep temporary
stores under this fixture directory. The existing API is consumed by a CLI:
`queue(owner, {recipient,text})`, `edit(owner,id,body)`, `approve(owner,id)`,
`revoke(owner)`, `cancel(owner,id)`, `run(id)`, `snapshot()`.
Owners alice and bob start active. Approval is for exact content and is single-use.
User-supplied recipient values are test labels, not usable addresses.
