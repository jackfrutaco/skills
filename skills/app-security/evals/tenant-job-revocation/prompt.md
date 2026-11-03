---
tags: [skill-creator]
max_turns: 12
timeout_seconds: 300
allowed_tools: [Read, Glob, Grep, Skill, Write, Edit, Bash]
---

Review this small report-export service before launch. It is review only: don't
change the service or deploy anything. Check the protection we have and the most
important gaps. You may run `node service.mjs --probe`; it uses synthetic in-memory
data, has no network/filesystem writes, and exits on its own. Give me a prioritized
report with evidence, a suggested repair and a way to check it. We have no live
deployment evidence yet.

Input files: service.mjs, README.md
