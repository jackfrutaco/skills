#!/usr/bin/env node
// Self-runnable tests for the ci skill's scripts and gate templates.
// Usage: node evals/test_scripts.mjs   (exit 0 = pass; needs Node 22+ and git)
// No network: the collector is tested through a fake API, and git repos are throwaway.
import "./tests/gate.test.mjs"
import "./tests/reports.test.mjs"
import "./tests/release.test.mjs"
import "./tests/health.test.mjs"
import "./tests/upsert.test.mjs"
import "./tests/local-adapter.test.mjs"
import "./tests/behavior-runner.test.mjs"
