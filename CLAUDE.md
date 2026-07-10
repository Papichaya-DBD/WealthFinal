# Yuanta Wealth Website — Project Instructions

## Git workflow (standing rule, confirmed by user 2026-07-10)

After making any file edit in this repo that gets uploaded to HubSpot via `hs cms upload`, **commit the change to git immediately afterward — do not ask for confirmation first.** This applies to every edit session, not just large batches.

- Stage only the specific files that were actually changed (never `git add -A`/`.`).
- Write commit messages in the existing style seen in `git log` (`type: short description`, e.g. `fix: related-section missing self-category sibling cards`, `style: ai-summary-box mobile background image`). Describe the *why*/effect, not a narration of the diff.
- End every commit message with:
  ```
  Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
  ```
- Do **not** push to the `origin` remote (`github.com/Papichaya-DBD/WealthFinal`) automatically — pushing still requires explicit user confirmation each time, per standard safety practice for shared/remote state.
- This rule only covers local commits as an audit trail alongside HubSpot's Design Manager history. It does not change any other confirmation requirements (e.g. still recap + confirm before editing files per user's established workflow preference).
