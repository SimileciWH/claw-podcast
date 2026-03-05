# ci_runner
Purpose: Run CI/test pipeline and report pass/fail with evidence.
Inputs: repo, branch, test commands.
Outputs: CI result summary and failing stage details.
Writes: worklog type `ci`.
Acceptance: status must be unambiguous; failed stages include actionable logs.

Policy:
- If all required CI checks pass, mark `merge_ready=true` for downstream `github_repo_ops`.
- No manual human approval is required for merge when `merge_ready=true`.
