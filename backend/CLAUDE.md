# CLAUDE.md — Sukoon Backend API

Django 4.2 + DRF + SimpleJWT + Channels. Settings package `config/settings/`, apps under `core_apps/`,
environment from `Pipfile.lock`. Target architecture (`sprints/ARCHITECTURE.md`): explicit class-based views
over domain services; remaining function views are migration debt tracked in `sprints/ROUTE_MATRIX.md`.

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
Encodes THIS project's layout (`core_apps/`, `config/settings/` split, lock-based env, CBV + services target, MVP scope, Makefile).
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
- Use the `Makefile` targets. The environment is built from `Pipfile.lock` (Python 3.11, includes
  `pillow-heif`): `pipenv install`, or a hash-checked `backend/.venv` as described in the
  `django-feature` skill. There is no `./Venv/`.
- Settings live in `config/settings/` (`base.py` + one module per environment). Tests use
  `config.settings.test` (pytest.ini); PostgreSQL tests use `config.settings.postgres_test` with disposable
  `TEST_POSTGRES_*` values. Deployed env comes from the repo-root `.env`/platform; never read or edit it for tests.
- Apps live in `core_apps/<app>/` (urls → thin views → serializers → `services/`).
- Architecture target (user-approved; see `sprints/ARCHITECTURE.md`): new and converted HTTP endpoints are
  explicit class-based views; domain services own transactions, locks, authority and side effects. The existing
  526 `@api_view` routes are migration debt converted by sprints 05–10 — do not add new `@api_view` functions
  and do not change route names/aliases/contracts during conversion.
- DRF endpoints use cookie/SimpleJWT auth (`core_apps.common.cookie_auth`), django-filter and the configured
  pagination/renderer. Admin is Django admin plus the `admin_api` staff API (no django-unfold).
- The MVP release switch (`SUKOON_MVP`, default true) gates deferred routes in `core_apps/common/mvp_scope.py`;
  run both `make test-baseline-mvp` and `make test-baseline-restoration` for cross-cutting changes.
- Regenerate `sprints/ROUTE_MATRIX.md` (`make route-matrix`) whenever routes change.
- Never alter `db.sqlite3`, `commerce_sandbox.sqlite3`, `.demo/`, `media/` or production state to make tests pass.

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
