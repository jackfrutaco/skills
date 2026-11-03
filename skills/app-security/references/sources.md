# Research provenance and reuse

Reviewed 2026-11-03. This is an original synthesis of selected primary guidance
and comparable skills, not an exhaustive standards review, certified methodology
or independent penetration test. Versioned references below support only the
named portions. Living vendor pages must be checked against the target version.

## Methods and controls actually read

| Source | Reviewed portion → use here |
| --- | --- |
| [NIST SP 800-115](https://nvlpubs.nist.gov/nistpubs/Legacy/SP/nistspecialpublication800-115.pdf), 2008 | §5.2 and Appendix B: engagement lifecycle and rules → scope, stop conditions, controlled testing and closeout; not its dated tool catalogue |
| [ASVS 5.0.0 session chapter](https://github.com/OWASP/ASVS/blob/180622b1329ee7ed349c9f5ce5e14fa91f42c359/5.0/en/0x16-V7-Session-Management.md) | Session lifecycle → W1's exact partial mapping |
| [ASVS 5.0.0 authorization chapter](https://github.com/OWASP/ASVS/blob/180622b1329ee7ed349c9f5ce5e14fa91f42c359/5.0/en/0x17-V8-Authorization.md) | Object/function/field/tenant and originating principal → W2; levels are stated rather than silently elevated |
| [ASVS 5.0.0 token chapter](https://github.com/OWASP/ASVS/blob/180622b1329ee7ed349c9f5ce5e14fa91f42c359/5.0/en/0x18-V9-Self-contained-Tokens.md) | Integrity, algorithms, keys, validity, purpose and audience → W1 |
| [WSTG 4.2 ATHZ-04](https://wstg.owasp.org/v4.2/4-Web_Application_Security_Testing/05-Authorization_Testing/04-Testing_for_Insecure_Direct_Object_References/), [SESS-06](https://wstg.owasp.org/v4.2/4-Web_Application_Security_Testing/06-Session_Management_Testing/06-Testing_for_Logout_Functionality/), [BUSL-06](https://wstg.owasp.org/v4.2/4-Web_Application_Security_Testing/10-Business_Logic_Testing/06-Testing_for_the_Circumvention_of_Work_Flows/) | Known-object comparisons, logout replay and workflow bypass → W1–W3; not every WSTG test |
| [Electron security](https://www.electronjs.org/docs/latest/tutorial/security), living | Sender/frame origin, bridge exposure, navigation, isolation and fuses → D1/D2 and separate packaged checks |
| [MCP security practices](https://modelcontextprotocol.io/docs/2026-07-28/tutorials/security/security_best_practices), observed 2026-07-28 route | Audience-bound tokens, confused deputy, SSRF and session handling → A3; not full protocol conformance |
| [OWASP LLM06:2025](https://genai.owasp.org/llmrisk/llm062025-excessive-agency/) | Excessive functionality, permissions, autonomy and downstream mediation → A1/A2 |
| [OWASP SSRF prevention](https://cheatsheetseries.owasp.org/cheatsheets/Server_Side_Request_Forgery_Prevention_Cheat_Sheet.html), living | Destination validation, DNS/connect binding and redirects → W5 |
| [Cloudflare token scope](https://developers.cloudflare.com/fundamentals/api/get-started/create-token/), living | Resource and operation scope, optional IP/lifetime restrictions → C1; not a login/setup recipe |
| [SLSA 1.2 artifact verification](https://slsa.dev/spec/v1.2/verifying-artifacts) | Consumer checks of signature, digest, trusted builder and expectations → C3; no level claimed |
| [OWASP Secrets Management](https://cheatsheetseries.owasp.org/cheatsheets/Secrets_Management_Cheat_Sheet.html), living | Credential lifecycle, revocation, auditing and recovery → operations/C5 |

Initial discovery also read [ASVS overview](https://asvs.owasp.org/),
[OWASP LLM Top 10 index](https://genai.owasp.org/llm-top-10/),
[NIST SSDF project](https://csrc.nist.gov/projects/ssdf) and
[SLSA 1.2 overview](https://slsa.dev/spec/v1.2/).
Overview pages informed breadth; they do not substantiate detailed implementation checks.

## Comparable skills inspected, not installed

| Primary source / pinned revision | Useful idea | Boundary retained here |
| --- | --- | --- |
| [Trail of Bits skills](https://github.com/trailofbits/skills/tree/711af095215ad4ecde5b90cd1d0124b3f1c4ca9e): audit-context-building, differential-review, variant-analysis | Build context before findings; inspect removed controls/callers; broaden a demonstrated defect into variants | No host-specific Workflow dependency or automatic severity escalation from missing tests. Repository licence: CC BY-SA 4.0 |
| [OpenAI security skills](https://github.com/openai/skills/tree/49f948faa9258a0c61caceaf225e179651397431/skills/.curated): security-best-practices, security-threat-model; Express reference sampled | Repository-grounded threat model and framework-specific evidence/false-positive guidance | Language support is narrower than all apps; do not present UUIDs as authorization. Relevant skill licences: Apache-2.0 |
| [Anthropic security-review command](https://github.com/anthropics/claude-code-security-review/blob/0c6a49f1fa56a1d472575da86a94dbc1edb78eda/.claude/commands/security-review.md) | Changed-code focus and deliberate false-positive review | Its PR scope excludes abuse/resource exhaustion and dependency findings; those exclusions cannot govern a whole-app audit. Repository licence: MIT |

Local Cobweb and Personal Security were read as workflow comparators: assessment
before edits, candidates versus confirmed findings, and recovery before removing
access. Their personal-device/project-hygiene domains are not app penetration testing.

No external skill text or executable was vendored into this package. The methods
and fixtures are original prose/code informed by those ideas. If later copying or
adapting upstream text/code, retain its attribution, licence and applicable notices;
do not assume that a public repository makes reuse unrestricted.

## Limits

CISA returned 403 and PTES timed out; neither is supporting evidence. Full ASVS,
WSTG, mobile assurance, custom cryptography, native-memory exploitation, current
vulnerability feeds, legal requirements and every cloud provider remain outside
this source review. W4/W6 and some operational cases are general engineering
synthesis requiring platform-specific primary guidance when implemented. Four
synthetic cases cannot qualify every method. Keep project-private findings and
live account details outside a distributable skill.
