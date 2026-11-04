---
type: llm
focus: trace
weight: 1
---

Reports that any account can export another workspace's document: the export worker (or requestExport) loads and emails the doc without the canReadDoc check that GET /docs applies. Severity Critical or High.
