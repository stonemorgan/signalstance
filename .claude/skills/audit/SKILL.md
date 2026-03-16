---
name: audit
description: Run the full SignalStance audit suite — launches 6 specialized agents in parallel to review security, error handling, data integrity, API robustness, frontend quality, and code optimization, then triages findings, implements critical fixes, and builds test coverage.
context: fork
agent: audit-suite
user-invocable: true
disable-model-invocation: false
---

Run the full SignalStance audit workflow. Follow the 4-phase process defined in your agent instructions:

1. Launch all 6 audit agents in parallel
2. Synthesize findings into a triage report
3. Implement critical and high priority fixes
4. Build test coverage around the fixes

Save all reports to `audit-reports/`. Begin immediately.

$ARGUMENTS
