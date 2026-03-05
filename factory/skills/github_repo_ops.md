# github_repo_ops
Purpose: Perform git/GitHub operations for branch, PR, and merge flow.
Inputs: repo path, operation plan.
Outputs: branch/pr identifiers and operation results.
Writes: worklog type `gate` or `release`.
Acceptance: CI-linked PR flow created; branch protection blockers reported explicitly.

Policy:
- Always open PR for changes to main.
- If required CI checks are green, merge PR into main automatically (no manual human approval gate).
- If merge is blocked (branch protection/conflict/check pending), report blocker and retry when checks become mergeable.
