# Box Recommender

[![CI](https://github.com/atharva-patil-23/box-recommender-/actions/workflows/ci.yml/badge.svg)](https://github.com/atharva-patil-23/box-recommender-/actions/workflows/ci.yml)

**Repository:** <https://github.com/atharva-patil-23/box-recommender->

A small Django service that recommends the most suitable shipping box for an
ecommerce order. Given a set of products (each with dimensions and weight) and a
catalogue of boxes (each with internal dimensions, a weight capacity, and a cost),
it returns the cheapest single box that can hold the whole order — with capacity
utilisation and ranked alternatives.

## Contents
- [Problem](#problem)
- [Design rationale](#design-rationale)
- [API reference](#api-reference)
- [Setup](#setup)
- [Quality gates & tests](#quality-gates--tests)
- [Assumptions](#assumptions)
- [Limitations](#limitations)

## Problem

When a customer places an order, the warehouse needs to know which box to pack it
in. Each product has dimensions (cm) and weight (g); each box has internal
dimensions (cm), a maximum weight capacity (g), and a cost. The system recommends
the **single most suitable box** for an order, or reports that none fits.

"Most suitable" is defined as the **cheapest box that fits**, ties broken by
smallest internal volume, then name (for determinism).

## Design rationale

The business logic lives in a **framework-free core** ([`selection/`](selection/))
built only from `Decimal`/`int` dataclasses — it has zero Django imports and is
unit-tested in isolation. Django is an adapter around it:

```
HTTP (DRF view)  ->  service (ORM <-> dataclasses)  ->  selection core (pure)
orders/api.py        orders/services.py                 selection/engine.py
```

- **`selection/`** — `recommend_box(items, boxes)`; pure functions, no side effects.
- **`orders/services.py`** — the *only* place the ORM meets the core: it maps
  `Product`/`Box` rows to dataclasses, runs the recommendation, and persists the
  outcome on the `Order`.
- **`orders/api.py`** — a thin DRF view: validate → service → JSON.

This keeps the algorithm testable without a database or HTTP, and keeps the fit
rules in one auditable place. See [docs/DESIGN.md](docs/DESIGN.md) for the
rotation proof and the architecture decision records (ADRs).

### How a box is chosen

An order **fits** a box when **all** hold:
1. **Per-item dimensions** — every item fits the box comparing *sorted* side
   lengths, which permits 90° axis rotation (see the proof in DESIGN.md).
2. **Total volume** — Σ(quantity × item volume) ≤ box internal volume.
3. **Total weight** — Σ(quantity × item weight) ≤ box weight capacity.

The cheapest fitting box wins; the rest are returned as ranked alternatives.

## API reference

### `POST /api/orders/`

Creates an order and returns the box recommendation.

**Request**
```json
{ "items": [ { "product_id": 1, "quantity": 2 }, { "product_id": 3, "quantity": 1 } ] }
```

**Response — fit found (`201`)**
```json
{
  "order_id": 3,
  "fit_found": true,
  "reason": null,
  "recommended_box": {
    "id": 4, "name": "Medium", "cost": "2.50",
    "utilisation": { "volume_pct": 24.1, "weight_pct": 20.0 }
  },
  "alternatives": [
    { "id": 2, "name": "Large", "cost": "5.00", "utilisation": { "volume_pct": 6.3, "weight_pct": 8.0 } }
  ]
}
```

**Response — no fit (`201`)**
```json
{
  "order_id": 4,
  "fit_found": false,
  "reason": "No available box can hold this order within its dimension, volume and weight limits.",
  "recommended_box": null,
  "alternatives": []
}
```

A no-fit is a *successful computation*, so it returns `201`. Bad input returns `400`.

**Validation errors (`400`)** — empty `items`, unknown `product_id`, `quantity < 1`
or `> 10000`, or the same product listed twice.

**Field notes**
- `cost` is a decimal string to avoid float drift.
- `utilisation.*_pct` is `order total ÷ box capacity` as a percentage (one decimal).
  Bounded at 100% because only fitting boxes are evaluated.
- `alternatives` are the other fitting boxes, cheapest-first.

### curl

```bash
# Fitting order
curl -s -X POST http://localhost:8000/api/orders/ \
  -H 'Content-Type: application/json' \
  -d '{"items":[{"product_id":1,"quantity":2},{"product_id":3,"quantity":1}]}'

# Non-fitting order
curl -s -X POST http://localhost:8000/api/orders/ \
  -H 'Content-Type: application/json' \
  -d '{"items":[{"product_id":6,"quantity":5}]}'
```

## Setup

Configuration is 12-factor: everything comes from environment variables
(see [.env.example](.env.example)). PostgreSQL is the only database engine —
local, Docker, and CI all use it via `DATABASE_URL` (no SQLite fallback).

### Option A — Docker (recommended)

```bash
docker compose up -d --build          # starts Postgres (health-checked) + the app
docker compose exec web python manage.py seed_demo   # load demo products & boxes
# app is now on http://localhost:8000  (admin at /admin/)
```

The app container waits for Postgres to be healthy, applies migrations on start,
and serves via gunicorn. Postgres is published on host port **5433** to avoid
clashing with a local Postgres on 5432.

### Option B — Local virtualenv

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
cp .env.example .env                  # points DATABASE_URL at localhost:5433
docker compose up -d db               # or any Postgres reachable via DATABASE_URL
python manage.py migrate
python manage.py seed_demo
python manage.py runserver
```

Create an admin user with `python manage.py createsuperuser` to browse data at
`/admin/`.

## Quality gates & tests

```bash
ruff check . && ruff format --check .              # lint + format
mypy .                                             # strict types (django-stubs)
python manage.py makemigrations --check --dry-run  # no model/migration drift
pytest                                             # tests + >=90% coverage gate
```

CI ([.github/workflows/ci.yml](.github/workflows/ci.yml)) runs these four gates in
order against a Postgres service container — see the latest run on
[GitHub Actions](https://github.com/atharva-patil-23/box-recommender-/actions/workflows/ci.yml).
Latest local capture: [TEST_OUTPUT.md](TEST_OUTPUT.md).

## Assumptions

- All measurements share one unit system: **cm** for length, **grams** for weight,
  money for cost. No unit conversion is performed.
- Dimensions and weights are positive (enforced by model validators).
- One order is packed into **one** box; orders are not split across boxes.
- A product appears at most once per order (combine duplicates into a quantity).
- Box rotation is free (90° axis rotations); see the proof in DESIGN.md.

## Limitations

- **Not true 3D bin packing.** Each item is checked against the box independently,
  plus aggregate volume and weight guards. We do **not** verify that all items can
  be physically arranged inside the box simultaneously. This is a deliberate,
  documented approximation (see [ADR-0002](docs/DESIGN.md#adr-0002-fit-model)); it
  can occasionally report a fit a real packer would reject.
- **Single box only** — no multi-box splitting.
- **No auth / rate limiting** on the endpoint (out of scope for this exercise).
