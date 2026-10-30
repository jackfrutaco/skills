# Delivery

Deploy exactly what was verified, in order, and prove what is live.

## The evidence chain

```
gate passed for candidate C (run R, attempt A, policy P)
  → build once → artifact D (digest) + release.json {C, R, A, D, gate}
  → promotion job: release.mjs check (digest, candidate, repository, gate, not stale)
  → provider deploy of those bytes, tagged C
  → read back the live version's tag == C, then a meaningful health check
```

- **One workflow, one DAG** when it fits: `build` needs `gate`, `deploy` needs `build`,
  all in the same run for the pushed commit. A separate workflow triggered by `push`
  does not wait for CI; `workflow_run` can chain workflows but must check the upstream
  conclusion, branch, event and repository, and must not run untrusted PR artifacts.
- **Build once.** Upload the verified bundle (for Workers, see the table below). If the
  provider must build from source, pin the commit and record the provider's version id,
  and say that the bytes are rebuilt.
- **Manual dispatch** goes through the same full gate and checks; the example deploys
  from `push` and `workflow_dispatch` on the default branch only. There is no bypass
  input.
- **Serialize production**: a `concurrency` group with `cancel-in-progress: false` on the
  deploy job, plus `release.mjs check --deployed <live SHA>`, which denies a candidate
  older than what is live (an older run finishing last) and a candidate that does not
  descend from it unless `--allow-diverged true` is a deliberate choice. When the live
  version cannot be identified (first deploy, an untagged manual deploy, an unreadable
  provider) pass `--deployed unknown`: promotion is denied unless
  `--allow-unknown-live "<reason>"` is given, for example from a repository variable
  set for the first deploy and removed afterwards.
- **Production environment** (`environment: production`) holds deploy credentials, so
  only jobs that name it can read them; add required reviewers when the project wants a
  human approval.

`templates/ci/release.mjs` implements the manifest and check; the example workflow in
`evals/fixtures/workflows/ci.yml` wires it.

## Health and read-back

Success is not "the deploy command exited 0". After promotion:

1. Read back the provider's live version and confirm it carries the candidate.
2. Hit an endpoint that exercises real behavior and returns the version (for example
   `/health` returning `{"version":"<sha>", "db":"ok"}`), with a timeout. A static 200
   is not health.
3. On failure, follow the recovery decision below; do not loop deploys.

## Cloudflare (existing targets, existing account route)

Commands run offline (`--dry-run`) with Wrangler 4.119.0 on a Worker with static assets
and a dynamic import (2026-10-30); not yet run against a real account:

| Need | Workers | Pages |
|---|---|---|
| Bundle without uploading | `wrangler deploy --dry-run --outdir dist/worker`; the module is named after `main` (`src/worker.ts` → `worker.js`). Copy the assets directory into the artifact too (`dist/assets`); the bundle does not include it. Not `--outfile`: that writes Wrangler's upload form data, not a module | build output dir |
| Upload a version, tagged | `wrangler versions upload dist/worker/<module>.js --no-bundle --assets dist/assets --tag <sha> --message <text>` | `wrangler pages deploy <dir> --project-name <p> --branch <b> --commit-hash <sha>` |
| Route traffic | `wrangler versions deploy --version-tag <sha>@100 --yes` (or `<id>@10` for a gradual rollout) | production branch deploy |
| Read what is live | `wrangler deployments status --json` then `wrangler versions view <id> --json` (`annotations["workers/tag"]`) | `wrangler pages deployment list --project-name <p> --environment production --json` |
| Roll back | `wrangler rollback <version-id>`, limits below | dashboard or API rollback to an eligible production deployment |

- Use the target's existing Wrangler config and the account route the project already
  uses. In CI that means an API token secret scoped to the account and the needed
  Workers/Pages permissions; a desktop's logged-in session does not carry over to a
  hosted runner. If no credential exists, report the blocker; do not create a token or
  switch accounts or providers without authority naming that.
- Gradual rollout: upload, deploy at a small percentage, watch health and errors, then
  100%. Both versions serve traffic meanwhile, so they must be compatible with the same
  data and bindings.

## Recovery limits

Rollback restores code, not data:

- A Workers rollback does not restore KV, D1, R2, Durable Object state or secrets, and
  can be refused when bindings or Durable Object migrations changed. Pages rolls back
  only to earlier successful production deployments, not previews.
- Schema changes use expand → migrate → contract across releases, so the previous
  version still runs on the current schema. A destructive migration has no binary
  rollback; recovery is roll-forward or restore from backup, decided in advance.
- Write the recovery decision for each release type in the project's deploy doc:
  when to roll back, when to roll forward, who decides, how data is restored.

## Drills

Drills (a deliberately failing test, a rollback, a bad canary) run on a disposable or
staging target, or a draft PR, with no production publication and no other person's
data. Production drills need authority that names that effect.

## Other providers

Vercel, Netlify, Fly, Railway, AWS and others keep their own pipeline owner. Apply the
same chain (gate → immutable artifact or pinned commit → serialized promotion →
read-back → health) in their terms and say the recipe is unqualified guidance.
