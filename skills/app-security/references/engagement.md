# Engagement and evidence boundaries

Reuse existing authorization. Record only what is missing; do not turn every code
review into an interview. Host rules and the user's latest constraints govern.

## Choose the deliverable

| Deliverable | What it establishes | What remains outside it |
| --- | --- | --- |
| Source review | Reachable paths and control implementation at a revision | Runtime configuration, exploitability with real identities |
| Control verification | A named requirement under specified positive/negative conditions | Unselected requirements or whole-system certification |
| Vulnerability reproduction | A bounded observed effect with known prerequisites | Other deployments or an exhaustive search |
| Penetration test | An authorized adversarial exercise with scope, rules, discovery, controlled exploitation and reporting | Universal security, compliance certification, untested assets |

A scanner is one input to these activities. A list of OWASP risks is not a test
plan. State coverage gaps even when every attempted test passes.

## Before an active probe

Record a compact rules-of-engagement block in the private report:

- Exact target/build/environment, permitted test identities and owner authorization.
- Allowed operations and data; excluded third parties, production services and accounts.
- Request/concurrency/byte/time limits, permitted tool/network destinations and costs.
- Stop conditions: unexpected real data, a non-test target, service degradation,
  authority change, an unbounded side effect or inability to observe the effect.
- Incident contact/route if supplied, evidence location/retention and cleanup ownership.

Local synthetic fixtures need no new permission when local tests are already
authorized. A hostname in a repository, account read grant, or request to
"audit" does not authorize sending exploit traffic to a live service. Continue
source work if live authorization or tooling is missing.

Inspect candidate commands and dependencies before execution. Avoid installation
hooks, upload defaults, recursive live discovery and autonomous exploitation.
Use a fake downstream sink for messages/payments/deletion; count attempts as well
as successful effects. Stop at the first sufficient harmless reproduction, not
at the maximum damage possible.

## Findings and closeout

Give each finding a stable ID, prerequisites, control owner, a minimal reproduction,
impact, counterevidence, repair and negative/positive retest. Keep severity separate
from confidence. Prefer a meaningful attack chain over ten symptoms of one missing
boundary. Track newly discovered related paths as separate coverage, not implied fixes.

Retain only redacted evidence needed to reproduce. Clean up only fixtures/resources
created for this test and record anything left behind. A repair is closed only for
the tested revision and environment; rollout, customer adoption and live revocation
are separate states. An active incident may need an operator or specialist before
any further probe. See [operations](operations.md).

Method basis: [NIST SP 800-115 §5.2 and Appendix B](https://nvlpubs.nist.gov/nistpubs/Legacy/SP/nistspecialpublication800-115.pdf).
Use its engagement lifecycle; ignore its 2008 tool inventory.
