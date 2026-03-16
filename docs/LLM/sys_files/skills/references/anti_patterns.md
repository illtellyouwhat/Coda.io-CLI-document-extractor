# Coda Anti-Patterns 

---

## 1️⃣ Structural Anti‑Patterns

### 🔹 1. Filter‑Based Lookups Instead of Relations

**Symptoms:**

- Formulas use `.Filter()` to connect tables via text fields.
    
- Typo‑sensitive dependencies (`[Invoices].Filter([ClientName]=thisRow.[ClientName])`).
    

**Why It’s Bad:**

- No referential integrity; poor performance.
    
- Text mismatches break lookups.
    

**Fix:**  
Use **Relation Columns** and **Linked Relations** for two‑way connections. Remove redundant text fields.

**Refs:** [Relations](https://help.coda.io/hc/en-us/articles/39555878926861) | [Linked Relations](https://help.coda.io/hc/en-us/articles/39555809935629)

---

### 🔹 2. Duplicate or Near‑Duplicate Views

**Symptoms:**

- Multiple connected views of the same base table with identical filters.
    
- Users confused which view to use.
    

**Why It’s Bad:**

- Redundant maintenance; inconsistent changes.
    

**Fix:**  
Run a **Redundant Views Audit** (see `/references/analysis_templates.md`). Keep canonical view; merge duplicates.

**Refs:** [Connected Table Views](https://help.coda.io/hc/en-us/articles/39555897467021)

---

### 🔹 3. The “God Table”

**Symptoms:**

- 50+ columns; mixed entities (projects, tasks, meetings) in one table.
    

**Why It’s Bad:**

- Sparse columns, complex logic, user confusion.
    

**Fix:**  
Split entities into separate tables; connect via relations.

**Refs:** [Tables Overview](https://help.coda.io/hc/en-us/articles/39555768266893)

---

### 🔹 4. Canvas Columns as Data Stores

**Symptoms:**

- Rich text or media blobs stored per row.
    
- Slow load times.
    

**Fix:**  
Use **Detail Views** linked to base tables. Limit per‑row canvas content.

**Refs:** [Canvas Column Type](https://help.coda.io/hc/en-us/articles/39555806187917)

---

### 🔹 5. Circular Dependencies

**Symptoms:**

- Tables mutually reference each other.
    
- Random formula recalculations.
    

**Fix:**  
Enforce one‑directional data flow. Use automations to update dependent tables if needed.

**Refs:** [Formulas Guide](https://help.coda.io/hc/en-us/categories/37412218438221-Formulas)

---

## 2️⃣ Formula Anti‑Patterns

### 🔹 6. Deeply Nested Formulas

**Why It’s Bad:** Hard to debug, slow to compute.

**Fix:** Break logic into helper columns or use `WithName()` for intermediate steps.

**Refs:** [Formula Reference](https://help.coda.io/hc/en-us/articles/39555768341005)

---

### 🔹 7. Filter Chaining

**Why It’s Bad:** Multiple `.Filter()` calls trigger multiple scans.

**Fix:** Combine into one filter:  
`[Table].Filter([Status]="Active", [Priority]="High", [Owner]=User())`

---

### 🔹 8. Hard‑Coded Values

**Why It’s Bad:** Hidden business rules.

**Fix:** Move constants to a **Settings Table** and reference via relations.

---

### 🔹 9. Missing Error Handling

**Why It’s Bad:** Blank or error‑filled columns.

**Fix:** Use `IfError()` or conditional `If(IsBlank(...))` to handle nulls gracefully.

---

### 🔹 10. Filter‑After‑Compute

**Why It’s Bad:** Calculations done before filtering.

**Fix:** Filter first, then sort or compute (saves 10‑100× compute time).

---

## 3️⃣ Automation Anti‑Patterns

### 🔹 11. Automation Loops / “Spaghetti”

**Why It’s Bad:** Infinite triggers and unclear data flow.

**Fix:** Consolidate related automations; add **loop guards** and **status flags**.

**Refs:** [Automations in Coda](https://help.coda.io/hc/en-us/articles/39555778179853)

---

### 🔹 12. No Error Handling in Automations

**Fix:** Add logging + alert rows or Slack notifications when automation fails.

---

### 🔹 13. Over‑Automation

**Fix:**  
Use **formulas** for in‑row logic (real‑time, simple).  
Reserve **automations** for multi‑row actions or external integrations.

---

### 🔹 14. Trigger‑Happy Automations

**Fix:** Specify column change conditions (`When [Status] or [Budget] changed`).

---

## 4️⃣ View & Presentation Anti‑Patterns

### 🔹 15. The Kitchen Sink View

**Why It’s Bad:** 40+ columns shown; slow and unreadable.

**Fix:** Create minimal‑column summary views; hide helpers.

---

### 🔹 16. Unscoped Large Views

**Fix:** Add grouping or filters by Status/Owner/Date; use boards or timelines.

**Refs:** [Tables & Views Hub](https://help.coda.io/hc/en-us/categories/37412217582221-Tables-and-views)

---

## 5️⃣ Performance & Maintenance Anti‑Patterns

### 🔹 17. No Archiving Strategy

**Fix:** Archive completed rows (>12 months) via scheduled automation.

**Refs:** [Automations](https://help.coda.io/hc/en-us/articles/39555778179853)

---

### 🔹 18. No Locking During Refactors

**Fix:** Lock critical tables/views while editing.

**Refs:** [Lock Tables & Views](https://help.coda.io/hc/en-us/articles/39555768033677)

---

### 🔹 19. No Monitoring or Changelog

**Fix:** Add Health Check page tracking load times, automation success, and doc size.

---

## 6️⃣ UX & Data Entry Anti‑Patterns

### 🔹 20. No Data Validation

**Fix:** Use Select Lists, Number, and Date types with constraints.

---

### 🔹 21. No Default Values

**Fix:** Automate default row setup (Status="Not Started", Date=Today()).

---

### 🔹 22. Inconsistent Terminology

**Fix:** Maintain a **Glossary Table** mapping canonical term → aliases.

---

### 🔹 23. Missing Loading States / Error Clarity

**Fix:** Use buttons with loading indicators and descriptive error messages.

---

## ✅ Quick Remediation Table

|Area|Symptom|Fix|Reference|
|---|---|---|---|
|Structure|Filter joins|Replace with relations|[Relations]|
|Views|Duplicate configs|Run Redundant Views Audit|[Connected Views]|
|Automations|Trigger loops|Add loop guards|[Automations]|
|Canvas|Heavy per‑row content|Use detail views|[Canvas Column Type]|
|Performance|No archiving|Scheduled automation cleanup|[Automations]|

---

**End of File — Optimized for quick reference during audits and AI‑guided diagnostics.**