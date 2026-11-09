# CLAUDE.md — Sukoon Monorepo

Sukoon is a real-estate platform. This repo holds `backend/` (Django API — see `backend/CLAUDE.md`) and `frontend/` (Next.js — see `frontend/AGENTS.md`); the Flutter mobile app lives in the separate `sokoun` repo. Run `make help` for monorepo commands.

---

## 📝 ALWAYS — Log Completed Tasks to WORKLOG.md

After finishing **any task requested by the user** (a feature, fix, refactor, config change, etc.), append an entry to the repo-root `WORKLOG.md` before ending your turn. It is the user's daily record for tech-lead/Plane review, so each entry must be self-contained.

- Append under today's date heading (`## YYYY-MM-DD`); create that heading if it's a new day.
- Write it as a finished, copy-pasteable summary — past tense, no "I will". Note any follow-ups or caveats the tech lead should see.
- Skip only for pure questions/conversation where nothing was changed. When in doubt, log it.

```markdown
### <short task title>
- **What:** <one line on what was done>
- **Why:** <reason / ticket context>
- **Details:** <key changes, decisions, anything the tech lead should notice>
- **Files:** <files touched>
```
