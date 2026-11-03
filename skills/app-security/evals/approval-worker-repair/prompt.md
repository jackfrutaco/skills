---
tags: [skill-creator]
max_turns: 20
timeout_seconds: 600
allowed_tools: [Read, Glob, Grep, Skill, Write, Edit, Bash]
---

Fix the approval boundary in this local notification worker. An owner approves one recipient and text; editing that content must require fresh approval. Revocation or cancellation must stop pending delivery, including after reopening the state file. Retrying a completed job must not send twice. Preserve legitimate queue/edit/approve/deliver behavior and cross-owner isolation. Implement the repair and run meaningful tests; provide the patch and a concise evidence report. All recipients and delivery receipts here are synthetic. You may write only inside this fixture and the assigned output directory. No real services, credentials, installation or deployment.

Input files: worker.mjs, README.md
