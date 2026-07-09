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

Hierarchy nodes (Category, Subcategory, ProductGroup, Brand) are FIXED —
managed via seed/migration, not via Telegram admin handlers.

---

# Open Questions (resolve before implementation)

- Should Category/Subcategory/ProductGroup/Brand support archiving/hiding without deletion?
