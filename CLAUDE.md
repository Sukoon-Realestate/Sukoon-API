# CLAUDE.md — GeenadeProject

Django 5.0 + DRF + SimpleJWT + Unfold admin. Settings package `Project/` with a `settings_modules/`
split, apps under `apps/`, single repo-root `.env`, `Makefile` shortcuts, virtualenv at `./Venv/`.
All API views are **function-based** (`@api_view`); keep code human-readable and minimal.

---

## CORE RULE — Auto-route every task

**Before answering directly, always check the routing table below.** If a prompt matches the
keywords of an agent or skill, **invoke it automatically** — do not wait for the user to name it.
If several match, pick the most specific; for multi-part work, chain them (e.g. build → review →
test). Only answer inline when nothing fits (simple questions, quick edits, conversation).

Matching is case-insensitive and partial — a keyword anywhere in the prompt counts.

---

## SKILLS (invoke with the Skill tool)

### `/django-feature`  ← preferred for almost all feature work here
Encodes THIS project's layout (settings split, `apps/`, Makefile, JWT, django-filter, Unfold).
**Trigger words:** add, create, build, scaffold, new app, new model, model, field, migration,
migrate, makemigrations, serializer, serialize, viewset, view, endpoint, route, url, api, crud,
list/detail/create/update/delete endpoint, filter, django-filter, pagination, permission,
authenticate, jwt, token, login, signup, register, admin, unfold, register model, queryset,
manager, signal, app, feature, generic view, apiview.

### `/code-review`
Review the working diff for bugs + cleanups (effort: low/medium/high/max/ultra).
**Trigger words:** review, review my changes, review the diff, check my code, look over, feedback
on, is this correct, code review, pr review, before i commit, before i push, find bugs in my diff.

### `/security-review`
Security pass on pending branch changes.
**Trigger words:** security review, security check, is this secure, vulnerability, vuln, exploit,
injection, xss, csrf, secure my changes, audit the diff, owasp.

### `/init`
Generate/update project documentation in CLAUDE.md.
**Trigger words:** init, document the project, generate claude.md, project docs, onboarding doc.

### `/run`
Launch/drive the actual app to see a change working.
**Trigger words:** run, run the app, start, start server, runserver, launch, boot, serve,
open the app, dev server, screenshot the app.

### `/verify`
Run the app and confirm a fix/feature actually works.
**Trigger words:** verify, confirm it works, does it work, test manually, validate, check the fix,
make sure it works, prove it works.

### `/webapp-testing`
Playwright-driven browser testing of the running app.
**Trigger words:** test in browser, e2e, end to end, playwright, browser test, click through,
test the ui, frontend test, integration test in browser.

### `/simplify`
Quality-only cleanup of changed code (reuse, simplify, efficiency). No bug hunting.
**Trigger words:** simplify, clean up, refactor lightly, tidy, dry up, reduce duplication,
make cleaner, polish the code.

### `/fewer-permission-prompts`
Add an allowlist to cut permission prompts.
**Trigger words:** stop asking permission, fewer prompts, allowlist, auto-approve commands,
reduce permission prompts.

### `/skill-creator`
Create or improve a skill.
**Trigger words:** create a skill, new skill, make a skill, edit skill, improve skill, build skill.

### Other skills (invoke when clearly relevant)
- `/docx` → **word doc, .docx, letter, memo, report (Word)**
- `/pdf` → **pdf, .pdf, merge pdf, split pdf, extract from pdf, fill form, ocr**
- `/pptx` → **slides, deck, presentation, .pptx, pitch deck**
- `/claude-api` → **claude, anthropic, opus, sonnet, haiku, anthropic sdk, model id, prompt caching, tool use, llm pricing**
- `/deep-research` → **deep research, research report, investigate thoroughly, multi-source, cited report**
- `/frontend-design` / `/web-artifacts-builder` / `/canvas-design` → **UI design, poster, visual art, react artifact** (rarely needed for this backend project)

---

## AGENTS (spawn with the Agent tool — `subagent_type`)

### django-developer  ← deep Django work beyond a single feature
**Trigger words:** django, drf, rest framework, async view, async orm, middleware, settings,
celery, channels, websocket, signal, custom user, abstractuser, model inheritance, manager,
queryset optimization, select_related, prefetch_related, django 5, enterprise pattern, modernize.

### python-pro
**Trigger words:** python, type hint, typing, mypy, dataclass, asyncio, async/await, decorator,
generator, context manager, pytest, packaging, pip, poetry, uv, script, utility, refactor python.

### api-designer
**Trigger words:** api design, design api, rest, restful, graphql, openapi, swagger, spec,
contract, versioning, api versioning, endpoint design, resource modeling, rate limit, pagination
design, idempotency, webhook design, hateoas.

### backend-developer
**Trigger words:** backend, server-side, service, microservice, business logic, scalability,
architecture (backend), throughput, queue, worker, background job, caching layer, redis.

### fullstack-developer
**Trigger words:** fullstack, full stack, end-to-end feature, frontend and backend, ui plus api,
whole feature across layers.

### database-administrator
**Trigger words:** database setup, postgres, postgresql, mysql, replication, high availability,
backup, restore, disaster recovery, connection pool, db config, provisioning, failover.

### database-optimizer
**Trigger words:** slow query, query optimization, optimize query, index, indexing, n+1,
explain analyze, query plan, db performance, slow page, optimize database, denormalize.

### performance-engineer
**Trigger words:** performance, slow, latency, speed up, optimize, bottleneck, profiling, profile,
memory leak, cpu, load test, benchmark, throughput, response time.

### security-auditor
**Trigger words:** security audit, audit security, secure, vulnerability assessment, threat,
risk, compliance, hardening, jwt security, cors, secrets, auth review, owasp, pentest review.

### penetration-tester
**Trigger words:** pentest, penetration test, exploit, attack, offensive security, ctf,
exploit a vuln, prove the vulnerability.

### code-reviewer
**Trigger words:** code review (agent), review code quality, best practices, maintainability,
review for, quality check, lint review, style review.

### architect-reviewer
**Trigger words:** architecture, system design, design decision, tradeoff, technology choice,
should i use, pattern, structure the project, macro design, evaluate design.

### refactoring-specialist
**Trigger words:** refactor, restructure, clean architecture, reduce complexity, extract,
decouple, technical debt, code smell, rewrite messy code, modularize.

### test-automator
**Trigger words:** test, tests, write tests, unit test, test coverage, coverage, pytest,
test framework, automated tests, ci tests, factory, fixture, mock.

### qa-expert
**Trigger words:** qa, quality assurance, test plan, test strategy, test cases, acceptance
criteria, quality metrics, regression plan.

### debugger
**Trigger words:** debug, bug, error, exception, traceback, stack trace, crash, not working,
broken, fails, fix the error, why is this failing, 500 error.

### error-detective
**Trigger words:** investigate error, correlate errors, root cause, logs, log analysis,
recurring error, intermittent, flaky, error spike, across services.

### deployment-engineer
**Trigger words:** deploy, deployment, ci/cd, ci pipeline, pipeline, github actions, release,
rollout, build pipeline, automate deploy.

### devops-engineer
**Trigger words:** devops, docker, dockerfile, compose, container, nginx, infrastructure,
infra, automation, kubernetes, k8s, terraform, environment, env config, provisioning.

### build-engineer
**Trigger words:** build, build system, compile, build time, build performance, makefile,
build cache, monorepo build.

### dependency-manager
**Trigger words:** dependency, dependencies, requirements.txt, upgrade package, update package,
version conflict, vulnerable dependency, audit deps, pip freeze, bump version.

### documentation-engineer
**Trigger words:** documentation, docs, document, api docs, write guide, tutorial, reference docs,
docstring (large scale), readme system.

### readme-generator
**Trigger words:** readme, generate readme, readme.md, project readme.

### git-workflow-manager
**Trigger words:** git workflow, branching strategy, git flow, merge strategy, rebase strategy,
commit convention, pr workflow, release branching.

### compliance-auditor / gdpr-ccpa-compliance
**Trigger words:** compliance, gdpr, ccpa, hipaa, pci, soc 2, iso, data privacy, consent,
right to deletion, data subject, regulatory.

### accessibility-tester
**Trigger words:** accessibility, a11y, wcag, screen reader, aria, contrast, keyboard navigation.

### ui-designer / ui-ux-tester
**Trigger words:** ui, ux, design system, component, visual design, usability, user flow,
mockup, layout, interface design.

### chaos-engineer
**Trigger words:** chaos, resilience, failure injection, game day, fault tolerance,
disaster simulation.

### Specialist agents (use only when explicitly relevant)
- ad-security-reviewer → **active directory, kerberos, ldap, domain controller**
- powershell-security-hardening → **powershell, ps1, remoting, execution policy**
- electron-pro → **electron, desktop app**
- ai-writing-auditor → **ai writing, remove ai patterns, humanize text**

---

## Project conventions (always honor)
- Use the `Makefile` targets and the `./Venv/` virtualenv for commands.
- Respect the settings layout: `Project/settings.py` + the `Project/settings_modules/*` split
  (`DJANGO_SETTINGS_MODULE = "Project.settings"`); env comes from a single repo-root `.env`.
- All API views are function-based (`@api_view`) — no APIView/ViewSet/generic class views.
  Favor short, human-readable code; inline serializers/helpers a feature doesn't need.
- New code goes in `apps/<appname>/`.
- DRF endpoints use SimpleJWT auth, django-filter, and the configured DRF pagination.
- Admin uses django-unfold.

---

## ALWAYS — Log every completed task to WORKLOG.md

After you finish **any task the user asked for** (a feature, fix, refactor, config change, etc.),
append an entry to `WORKLOG.md` before ending your turn. This is the user's daily record for
tech-lead/Plane review, so each entry must be self-contained.

- Append under today's date heading (`## YYYY-MM-DD`); create that heading if it's a new day.
- Use the entry template at the bottom of `WORKLOG.md`:
  ```
  ### <short task title>
  - **What:** <one line on what was done>
  - **Why:** <reason / ticket context>
  - **Details:** <key changes, decisions, anything the tech lead should notice>
  - **Files:** <files touched>
  ```
- Write it as a finished, copy-pasteable summary — past tense, no "I will". Note any follow-ups or
  caveats the tech lead should see.
- Skip only for pure questions/conversation where nothing was changed. When in doubt, log it.
