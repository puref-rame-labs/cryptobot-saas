# Catalog Hierarchy

---

# Purpose

Extends flat Product model with browsable catalog structure for marketplace resale.

---

# Hierarchy

Category → Subcategory → ProductGroup → Brand → Product

---

# Category

Fields:
- id
- title

---

# Subcategory

Fields:
- id
- title
- category_id (FK → Category.id)

---

# ProductGroup

Represents device type / product kind (e.g. "Планшет", "Ноутбук").

Fields:
- id
- title
- subcategory_id (FK → Subcategory.id)

---

# Brand

Fields:
- id
- title
- product_group_id (FK → ProductGroup.id)

---

# Product (existing, extended)

Fields (existing):
- id
- title
- description
- price
- currency
- telegram_file_id
- file_type
- status (DRAFT / READY / PUBLISHED / ARCHIVED)

New field:
- brand_id (FK → Brand.id)

---

# Invariants

- Brand is REQUIRED for every Product (no nullable brand)
- Every level MUST reference its immediate parent only (no skipping levels)
- Deleting a parent node MUST NOT cascade-delete Products silently — requires explicit reassignment or archive step
- Product purchasable rule unchanged: purchasable ONLY if status == PUBLISHED, independent of parent node status

---

# UI / Navigation Rule

When a user navigates to a leaf node (Brand) and no Product exists
with status == PUBLISHED under it:

- Display message: "Пока нет доступных товаров в этой категории"
- Do NOT show empty list silently
- Do NOT hide empty branches from navigation menus (MVP decision)

Rationale: simpler implementation, no extra existence-check query
per navigation level. Revisit if empty branches become frequent
enough to hurt UX.

---

# Hierarchy Management

STATUS (2026-09-08): SUPERSEDED. Hierarchy nodes were previously
managed ONLY via seed/migration (see "Admin UI Hierarchy Management"
below for the current model). This section is kept for historical
reference — hierarchy nodes are no longer fixed at deploy time.

Original constraint (now lifted): "Hierarchy nodes (Category,
Subcategory, ProductGroup, Brand) are FIXED — managed via
seed/migration, not via Telegram admin handlers."

`bootstrap_catalog.py` (known_issues.md fix, 2026-08-20) still seeds
a minimal demo hierarchy on a genuinely empty database at bot
startup — this is unrelated to admin UI management and continues to
run as-is. Admin UI management (below) operates on top of whatever
hierarchy exists, whether seeded or manually created.

---

# Admin UI Hierarchy Management (2026-09-08)

## Purpose

Allow an admin to create and delete Category/Subcategory/
ProductGroup/Brand nodes directly through the Telegram bot, without
requiring an Alembic migration or a code deploy for routine catalog
changes. This is a CRUD change over existing tables — no schema
change, no new migration.

## Scope

Applies to:
- Repository layer: `create()` on each of
  CategoryRepository/SubcategoryRepository/ProductGroupRepository/
  BrandRepository (existing files, extended)
- New `count_*` methods per repository, used only to gate deletion
- New use-case module:
  `app/application/catalog/use_cases/manage_hierarchy.py`
  (Create*/Delete* use-cases per level, `HierarchyNodeNotEmptyError`)
- New FSM states: `app/states/hierarchy_state.py`
- New handler module: `app/handlers/hierarchy_admin.py`
- New keyboard: `hierarchy_level_kb()` in
  `app/handlers/keyboards/catalog.py`

Does NOT apply to:
- Product model or Product lifecycle (unchanged)
- `bootstrap_catalog.py` (unaffected — still seeds on empty DB)
- Any database schema/migration (no new tables, no new columns)

## Creation Flow

Admin-only, via `/addhierarchy`:

1. Admin selects target level (Category / Subcategory / ProductGroup
   / Brand) via inline keyboard
2. If the level requires a parent (all except Category), the bot
   walks the admin through existing-node selection at each level
   above, reusing the existing navigation use-cases
   (GetCategoriesUseCase / GetSubcategoriesUseCase /
   GetProductGroupsUseCase — same ones used by `newproduct.py`)
3. Admin sends the title as a plain text message
4. Node is created via the corresponding repository `create()`
   method inside a `UnitOfWork`, flushed, and its id returned to
   the admin

If a required parent level has zero existing nodes (e.g. no
Category exists yet when creating a Subcategory), the flow rejects
with a message telling the admin to create the missing parent
level first — same invariant as before ("Every level MUST reference
its immediate parent only"), just now surfaced as a live UI check
instead of only a DB constraint.

`/listhierarchy` displays the full tree with node IDs (Category →
Subcategory → ProductGroup → Brand), needed because deletion (below)
is ID-based rather than navigation-based.

## Deletion Flow — RESOLVED: Block, Don't Cascade (variant 1)

Decided 2026-09-08, closing the "Open Questions" item this file
previously carried ("Should Category/Subcategory/ProductGroup/Brand
support archiving/hiding without deletion?").

Two other options were considered and explicitly rejected:
- **Require explicit reassignment** before deletion (move children
  to another parent first) — more admin-friendly, but adds
  meaningful UI complexity (a "move to..." picker) for a v1 feature;
  deferred, not ruled out permanently.
- **Cascade-archive** the whole subtree in one action — rejected as
  too risky for v1: a single delete action could silently archive
  an arbitrary number of already-sold Products, and would create a
  new, currently-nonexistent link between hierarchy deletion and
  Product archival that the rest of the system (see "Interaction
  with Product Archival" below) is not designed to reason about.

Chosen behavior: `/delcategory`, `/delsubcategory`,
`/delproductgroup`, `/delbrand` (direct ID, admin-only, mirrors the
existing `/archive` / `/publish` / `/refund` command pattern) each
check for children before deleting:

- Category: blocked if any Subcategory references it
- Subcategory: blocked if any ProductGroup references it
- ProductGroup: blocked if any Brand references it
- Brand: blocked if any Product references it (via `brand_id`)

If blocked, the admin sees exactly how many child records exist
(e.g. "Нельзя удалить: внутри 3 групп товаров") — no silent failure,
no partial deletion. The admin must delete/reassign the blocking
children individually, bottom-up, before the parent can be removed.

This keeps the original invariant ("Deleting a parent node MUST NOT
cascade-delete Products silently") satisfied by construction: since
nothing cascades, there is no path by which a delete action can ever
reach a Product without the admin explicitly clearing every
intermediate level first.

## Interaction with Product Archival (Open Question, tracked not blocking)

`domain_model.md`'s Product Lifecycle (`DRAFT → READY → PUBLISHED →
ARCHIVED`) has no return path from ARCHIVED — the same terminal-state
property that originally justified blocking hierarchy deletion
instead of cascading it (see Deletion Flow above).

Because cascade-archival was rejected, hierarchy deletion and
Product archival remain fully decoupled for now: a Product can only
become ARCHIVED via the existing `/archive` command, never as a side
effect of a hierarchy node being deleted. This is intentional and
requires no further work today.

Flagged for revisit only if either of the following becomes a real
requirement later:
- Reassignment-based deletion (option 2 above) is implemented —
  would need to decide whether reassigning a Brand's ProductGroup
  affects any ARCHIVED Products under it (probably not, but should
  be an explicit decision, not an accident of implementation).
- Restore-from-archive (`ARCHIVED → PUBLISHED`) is ever implemented
  — would need to decide what happens if a restored Product's
  Brand/ProductGroup/Subcategory/Category has since been deleted
  (this cannot currently happen, since deletion is blocked while
  children exist — but a fully independent Product-archival-and-
  restore feature could theoretically re-open this question if
  hierarchy deletion rules ever change).

No action required now — documented so this isn't rediscovered as a
surprise later, same pattern as `known_issues.md`'s handling of the
EXPIRED → PAID / REFUNDED sequencing dependency.

---

# Open Questions

None remaining for hierarchy management itself (both prior open
questions — "should hierarchy support archiving/hiding" and "how is
hierarchy managed" — are resolved above, 2026-09-08). See "Interaction
with Product Archival" for the one deliberately-deferred, non-blocking
follow-up.
