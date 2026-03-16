---
name: audit
description: Run the full SignalStance audit suite — launches 6 specialized agents in parallel to review security, error handling, data integrity, API robustness, frontend quality, and code optimization, then triages findings, implements critical fixes, and builds test coverage.
user-invocable: true
---

Run the full SignalStance audit workflow using the `audit-suite` agent. Follow this 4-phase process:

## Phase 1: Parallel Audit
Launch all 6 audit agents in parallel using the Agent tool. Each agent should be given the subagent_type matching its name. Run them all simultaneously:

1. **security-auditor** — review for XSS, injection, path traversal, tenant isolation, prompt injection, API key exposure
2. **error-resilience** — find crash paths, unhandled exceptions, race conditions, resource leaks
3. **data-integrity** — audit SQLite concurrency, schema gaps, state machine bugs, orphaned data
4. **api-robustness** — check Claude API error handling, rate limits, feed fetching, cost management
5. **frontend-reviewer** — find SPA bugs, state management issues, DOM problems, accessibility gaps
6. **codebase-optimizer** — identify dead code, duplication, architecture debt, performance issues

Save each agent's raw findings to `audit-reports/` as numbered markdown files (01-security.md through 06-code-quality.md).

## Phase 2: Triage
After all 6 agents complete, synthesize their findings into a unified triage report at `audit-reports/00-triage-summary.md`. Rank all findings by severity (Critical > High > Medium > Low > Info) across all domains.

## Phase 3: Implement
Launch the `implementation-executor` agent with the Critical and High priority findings from the triage report. It should implement fixes and save its report to `audit-reports/07-implementation.md`.

## Phase 4: Test
Launch the `test-architect` agent to build test coverage around the fixes and any other critical untested paths. Save its report to `audit-reports/08-test-coverage.md`.

## Final
Write an executive summary to `audit-reports/09-final-summary.md` with total findings, what was fixed, and what remains.

Create the `audit-reports/` directory if it doesn't exist. Begin immediately.

$ARGUMENTS
