# AI Usage

This project was built in a pair-programming session with an AI coding assistant.
This file records — honestly — what tool was used, how it was directed, what was
accepted/changed/rejected, the mistakes the assistant made along the way, and how
the work was verified.

## Tools

- **Claude Code** (Anthropic, model Opus 4.8) running in the terminal/IDE.
- The assistant had access to the shell, the local filesystem, Docker, and the
  project's own toolchain (ruff, mypy, pytest, Django management commands). All
  code, tests, Docker, CI, and docs were drafted by the assistant and reviewed by
  the author at defined checkpoints.

## How it was driven

The author ran the session as a real project: **spec → plan → implement in small,
reviewed steps**, with explicit ground rules — *no code before plan approval; the
author makes the design decisions; the assistant surfaces trade-offs and risks;
business logic must stay testable and isolated.*

Representative author prompts (paraphrased):
- "Restate the problem and list every open decision with 2–3 options, trade-offs,
  and your recommendation. No code."
- Selected the design via structured Q&A: REST/DRF, persisted `Order`/`OrderItem`,
  bounding-dimension fit with 90° rotation, cheapest-that-fits, Postgres-only,
  Decimal cm/g.
- "Add PostgreSQL via `DATABASE_URL` + Docker, 12-factor settings, quality gates
  (ruff, mypy+django-stubs, pytest ≥90%), GitHub Actions CI, and these
  deliverables." (Expanded the original plan.)
- "Approve the plan, but stop for my review at four checkpoints; show diffs and the
  output of `manage.py check`, ruff, mypy, pytest."
- "Review your own work as a senior reviewer; list findings with severity, fix the
  real ones, re-run the gates."
- "Add `seed_demo`, bring up Docker, and curl a fitting and a non-fitting order;
  confirm the response includes reason, utilisation metrics, and ranked
  alternatives."
- "Write the README, DESIGN.md (with rotation proof + ADRs), AI_USAGE.md, and
  capture test output."

## Accepted vs. changed vs. rejected

**Accepted (assistant proposed, author took as-is):**
- The layered, framework-free core (`selection/`) with a thin service adapter.
- All four primary design recommendations (REST/DRF, persisted order, bounding-fit,
  cheapest-that-fits) and the sub-decisions (90° rotation, Decimal cm/g, single
  box, explicit no-fit result).
- The sorted-side rotation test and the documented bin-packing limitation.
- The test-first core and the coverage/omit strategy.

**Changed / expanded by the author:**
- Scope grew well beyond the assistant's initial plan: Postgres + Docker + Compose
  healthcheck, 12-factor config, full quality-gate suite, GitHub Actions CI, and a
  formal documentation set. The assistant folded these into a revised plan before
  any code.
- Review cadence: the author replaced "pause after every step" with **four** named
  checkpoints and asked for diffs + gate output at each.
- Response contract: the author required **utilisation metrics** and **ranked
  alternatives**, which the original API did not return. This drove an engine
  change (`BoxEvaluation`, ranked `alternatives`) mid-build.

**Rejected / corrected by the author:**
- The author rejected the assistant's first "exit planning" attempt in order to
  inject the checkpoint structure — i.e. declined the proposed working cadence and
  substituted their own.

## Mistakes the assistant made during the build

Recorded for honesty; all were caught and fixed before the relevant checkpoint:

1. **Strict-mypy own goal (×68 errors).** The models first used a shared
   `**dict` of field kwargs; under `strict` mypy this collapsed every
   `DecimalField` argument to `object`. Fixed by writing the fields explicitly.
2. **Runtime `TypeError` from typing generics.** `ModelAdmin[Product]` and
   `TabularInline[...]` are not subscriptable at runtime without django-stubs'
   `monkeypatch()`. The first mypy run crashed importing admin. Fixed by calling
   `django_stubs_ext.monkeypatch()` in settings and adding the small runtime dep.
3. **Port clash.** Compose published Postgres on 5432, which was already in use
   locally; the container failed to start. Re-published on host port **5433**.
4. **Shell bug.** A readiness loop assigned to `status`, which is read-only in zsh;
   the script errored until the variable was renamed.
5. **Lint misses.** Several iterations to satisfy ruff: line-length on a couple of
   strings, `zip(..., strict=True)` (B905), and import ordering (I001).
6. **Shipped a gap, then caught it in self-review.** The first API cut included a
   **dead serializer** (`RecommendedBoxSerializer`) and **omitted utilisation and
   alternatives** — both flagged in the senior-review pass and fixed.
7. **Missing tool.** YAML validation needed PyYAML, which wasn't installed; it was
   installed temporarily and then removed (not a project dependency).

## How we verified

- **Static gates:** `ruff check` + `ruff format --check`; `mypy .` under `strict`
  with django-stubs + drf-stubs; `manage.py makemigrations --check --dry-run` for
  model/migration drift.
- **Tests:** `pytest` with a `--cov-fail-under=90` gate. The framework-free core is
  unit-tested with no database; the service and API are integration-tested against
  Postgres. Final state: **26 tests, 100% coverage.** See [TEST_OUTPUT.md](TEST_OUTPUT.md).
- **End-to-end:** `docker compose up` (Postgres health-checked, app on gunicorn),
  `seed_demo`, then real `curl` calls for a fitting and a non-fitting order — the
  actual JSON bodies and HTTP statuses were inspected, confirming `reason`,
  utilisation metrics, and ranked alternatives.
- **Architecture invariant:** `grep -r django selection/` returns nothing, proving
  the business core stays framework-free.
- **CI:** the GitHub Actions workflow runs the same four gates against a Postgres
  service container. Note: the workflow was validated structurally and by running
  its exact commands locally; a green check on GitHub requires pushing the repo to
  a remote (not done in this session).
