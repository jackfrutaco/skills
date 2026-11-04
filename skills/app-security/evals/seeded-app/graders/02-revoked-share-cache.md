---
type: llm
focus: trace
weight: 1
---

Reports that a revoked share link keeps serving the document because readShare reads shareCache before the share row and revokeShare never invalidates the cache. Severity High or Medium.
