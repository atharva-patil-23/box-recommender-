# Design

This document explains *why* the system is built the way it is: the architecture,
the geometric basis for the rotation-aware fit test, and the architecture decision
records (ADRs).

## Architecture

```
            HTTP request (JSON)
                  │
         ┌────────▼─────────┐   orders/api.py
         │  DRF APIView      │   validate input, shape response (thin)
         └────────┬─────────┘
                  │ OrderLine[]
         ┌────────▼─────────┐   orders/services.py
         │  Service adapter  │   ORM ⇄ dataclasses, persist Order, the ONLY
         └────────┬─────────┘   place the database meets the core
                  │ Item[], BoxSpec[]
         ┌────────▼─────────┐   selection/engine.py + types.py
         │  Selection core   │   pure functions, Decimal/int only, NO Django
         └───────────────────┘
```

The core is deliberately ignorant of Django, HTTP, and the database. It receives
plain value objects and returns a `Recommendation`. Everything framework-specific
lives at the edges. This is what makes the business rules unit-testable in
milliseconds without a database, and what keeps the fit logic in one auditable
place. A grep for `django` in `selection/` returns nothing — that is an enforced
invariant of the design.

## The rotation-aware fit test, and why it is correct

The core fit primitive compares **sorted** side lengths:

```python
def dimensions_fit(item_sides, box_sides):   # both sorted ascending
    return all(i <= b for i, b in zip(item_sides, box_sides))
```

This single line encodes "the item fits the box in *some* 90° axis-aligned
orientation." Here is the proof.

### Model

Restrict to axis-aligned placement (the warehouse turns an item in 90° steps so
its edges stay parallel to the box edges). An orientation is then a bijection
`f` assigning each item side to a distinct box axis. The item fits in orientation
`f` iff `item_sideᵢ ≤ box_axis_f(ᵢ)` for every `i`. The item fits the box iff
**some** such bijection exists.

### Claim

Let the item sides be the multiset `A = {x, y, z}` and the box sides
`B = {a, b, c}`. Write `A₍₁₎ ≤ A₍₂₎ ≤ A₍₃₎` and `B₍₁₎ ≤ B₍₂₎ ≤ B₍₃₎` for the
ascending sorts. Then:

> A fitting bijection exists **iff** `A₍ₖ₎ ≤ B₍ₖ₎` for every `k`.

So sorting both side-lists and comparing pointwise is exactly the fit test — no
need to enumerate the 6 orientations.

### Proof

**(⇐) Sorted pointwise ⇒ a bijection exists.** Pair the `k`-th smallest item side
with the `k`-th smallest box side. By assumption `A₍ₖ₎ ≤ B₍ₖ₎` for all `k`, so this
bijection is fitting. ∎

**(⇒) A bijection exists ⇒ sorted pointwise.** Suppose a fitting bijection `f`
exists but, for contradiction, `A₍ₖ₎ > B₍ₖ₎` for some `k`. Consider the
`n − k + 1` largest item sides `A₍ₖ₎, A₍ₖ₊₁₎, …, A₍ₙ₎`. Each has value
`≥ A₍ₖ₎ > B₍ₖ₎`, so each must be matched to a box side with value strictly greater
than `B₍ₖ₎`. The box sides with value `≤ B₍ₖ₎` include at least `B₍₁₎, …, B₍ₖ₎`
(that's `k` of them), leaving at most `n − k` box sides strictly greater than
`B₍ₖ₎`. We are trying to place `n − k + 1` items into `≤ n − k` boxes — impossible
by pigeonhole. Hence no such `k` exists, i.e. `A₍ₖ₎ ≤ B₍ₖ₎` for all `k`. ∎

(The argument holds for any `n`; here `n = 3`.)

### Scope caveat

The proof covers **axis-aligned** orientations only. Arbitrary (diagonal)
rotations could in principle squeeze a marginally larger item into a box; we do
not model them. This is the standard, conservative "90° rotation" assumption and
is recorded in [ADR-0002](#adr-0002-fit-model).

---

## Architecture Decision Records

### ADR-0001: Framework-free business core
- **Status:** Accepted.
- **Context:** The brief stresses that business logic must be testable and
  isolated. Putting fit/selection logic in views or model methods couples it to
  HTTP and the ORM.
- **Decision:** Implement the algorithm in a `selection/` package using only
  `Decimal`/`int` dataclasses, with zero Django imports. Django interacts with it
  exclusively through `orders/services.py`.
- **Consequences:** The core is unit-tested without a database or HTTP and runs in
  milliseconds. Cost: a thin mapping layer (ORM rows → dataclasses) that must be
  maintained.

### ADR-0002: Fit model
- **Status:** Accepted.
- **Context:** True 3D bin packing is NP-hard and disproportionate for a "small
  system." A naive volume-only check is physically wrong (a long rod "fits" a flat
  box by volume).
- **Decision:** An order fits a box iff (1) every item fits by sorted-side
  dimensions (90° rotation allowed), **and** (2) total volume ≤ box volume, **and**
  (3) total weight ≤ capacity.
- **Consequences:** Catches the gross geometric and weight errors and stays
  testable. **Limitation:** items are checked against the box independently; we do
  not verify they coexist inside the box at once, so a fit can occasionally be
  reported that a real packer would reject. Documented in the README.

### ADR-0003: "Most suitable" = cheapest that fits
- **Status:** Accepted.
- **Context:** Each box carries an explicit cost, strongly implying cost is the
  objective. Alternatives (smallest volume, least waste) ignore that signal.
- **Decision:** Pick the cheapest fitting box; break ties by smallest internal
  volume, then by name (for deterministic output). Return the remaining fitting
  boxes as ranked alternatives, each with capacity utilisation.
- **Consequences:** Deterministic, business-aligned results. Utilisation and
  alternatives give the warehouse context without changing the choice.

### ADR-0004: Single box; no-fit is a successful result
- **Status:** Accepted.
- **Context:** "Which box should be used" implies one box. Splitting an order
  across boxes is a separate bin-packing problem.
- **Decision:** Recommend one box per order. If nothing fits, return
  `fit_found: false` with an explanatory `reason` and HTTP `201` (a valid
  computation, not a client error). Input errors are `400`.
- **Consequences:** Simpler scope and contract. If the business later wants
  splitting or a `422` on no-fit, both are localized changes.

### ADR-0005: PostgreSQL everywhere, 12-factor config
- **Status:** Accepted.
- **Context:** SQLite-locally / Postgres-in-prod causes behavior drift (types,
  constraints, ordering).
- **Decision:** Use PostgreSQL for local, Docker, and CI, configured through a
  single `DATABASE_URL`. No SQLite fallback. All settings come from the
  environment; `SECRET_KEY` must be set when `DEBUG=False`.
- **Consequences:** One engine, fewer surprises. Cost: a running Postgres is
  required even for local tests (provided via Docker Compose).

### ADR-0006: Decimal units, no conversion
- **Status:** Accepted.
- **Context:** Floating point introduces rounding errors at fit boundaries.
- **Decision:** Store and compute dimensions/weights/cost as `Decimal`; assume one
  unit system (cm, grams, money) across all data; perform no unit conversion.
- **Consequences:** Exact comparisons. Cost: callers must supply consistent units.

### ADR-0007: Persist Order + OrderItem
- **Status:** Accepted.
- **Context:** A transient (compute-only) order is simpler, but a real system wants
  an auditable record of what was ordered and which box was chosen.
- **Decision:** Persist `Order` and `OrderItem`, storing `fit_found` and the
  `recommended_box` on the order. A `UniqueConstraint(order, product)` prevents
  duplicate lines.
- **Consequences:** History and auditability; the recommendation reason is derived
  on demand rather than stored, keeping the schema lean.
