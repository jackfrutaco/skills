# Synthetic desktop review packet

Status: supplied fixture evidence, not a real product audit.

- The source configuration uses contextIsolation=true, nodeIntegration=false,
  webSecurity=true and sandbox=false. A comment says the preload's existing RPC
  library needs Node and records a prior risk acceptance. Navigation and IPC sender
  guards exist, but their implementations and a running app are not supplied.
- A public container is deliberately distributed for customers to self-host. The
  desktop client also contains readable JavaScript. No private key, credential or
  customer data has been identified in either. A signature verification public key
  is embedded in the updater.
- The reminder API accepts any syntactically valid recipient. Its local source
  uses a per-IP Map with ten requests per minute, cleared at 10,000 entries. There
  is no recipient or aggregate budget in the supplied route. No deployed WAF,
  rate-limit or email-provider quota evidence is available. A provider call occurs
  after the record is persisted. CORS allows only the product website.
- The updater has isolated tests for missing signatures and modified signed fields.
  No test results, packaged binary, signing-account state or real update run are
  supplied.
- Development console access is useful to developers. Packaging defaults and
  whether command-line debug switches work in the released binary are unknown.
- The owner permits this review only. Changing registry visibility would break
  anonymous self-host installation unless a replacement distribution path exists.
