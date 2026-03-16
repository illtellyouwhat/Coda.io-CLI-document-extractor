# Coda Component Reference

---

## 🧱 Tables

**Docs:** [Overview – Tables](https://help.coda.io/hc/en-us/articles/39555768266893)

### Core Types

|Type|Purpose|Example|
|---|---|---|
|Master / Entity|Primary data objects|Projects, Customers|
|Lookup / Reference|Static or controlled vocabularies|Status, Category, Settings|
|Junction|Many-to-many links|ProjectMembers (Projects ↔ People)|
|Log / History|Immutable audit trail|Activity Log, API Sync Log|
|Summary / Calculation|Aggregations of other tables|Monthly Revenue Summary|
|Staging / Temporary|Intermediary processing|Import buffer|

### Table Health Audit

- **Row volume:** Over 25k? Consider archiving.
    
- **Purpose clarity:** Does each table represent one entity type?
    
- **Relations:** Are links explicit or text-based?
    
- **Formula density:** Too many computed columns per row?
    

### Common Anti‑Patterns

- **God Table:** Multiple entities in one table → split.
    
- **Duplicate Data:** Same info in multiple tables → centralize + relate.
    
- **Sparse Columns:** Many nulls → re‑model structure.
    

---

## 🔢 Columns

**Docs:** [Column Types](https://help.coda.io/hc/en-us/articles/39555809714445)

### Key Types & Audit Focus

|Type|Audit Focus|Notes|
|---|---|---|
|Text|Check for inconsistent formatting|Replace with Select/Relation|
|Number|Check units & precision|Normalize scales|
|Date/DateTime|Validate time zone consistency|Avoid text dates|
|Select / Multi‑Select|Ensure defined lists|Prefer over free text|
|Person|Confirm access & ownership context|Enforces permissions|
|Relation|Confirm correct target & linked relation|Critical structural link|
|Button|Verify idempotency & confirmation|Avoid business logic here|
|Canvas|Assess for bloat|Prefer detail views|

### Formula Column Levels

|Level|Pattern|Risk|
|---|---|---|
|1|Simple reference `[Table].[Col]`|✅ Low|
|2|Filtered lookup `.Filter(...).First()`|⚠️ Moderate|
|3|Aggregation `.Filter(...).Sum()`|⚠️ Moderate‑High|
|4|Nested / multi‑table|🔥 High (refactor candidate)|

### Optimization

- Replace chained `Filter()` calls with single combined filter.
    
- Cache expensive aggregations in helper columns updated via automation.
    
- Use `WithName()` to flatten nested logic.
    

---

## 👁️ Views

**Docs:** [Tables & Views Hub](https://help.coda.io/hc/en-us/categories/37412217582221-Tables-and-views) | [Create Connected Views](https://help.coda.io/hc/en-us/articles/39555897467021)

### Core Types

|View Type|Ideal Use|Performance Tip|
|---|---|---|
|Table|Bulk edit / analysis|Hide unused columns|
|Board|Workflow / Kanban|Group by select values|
|Calendar|Scheduling|One date column only|
|Timeline|Multi‑step projects|Limit visible span|
|Card|Browsing records|Use summary fields only|
|Detail|Read‑only forms|Link from pages not canvas columns|

### Audit Checklist

- Does this view have a unique purpose?
    
- Are filters early and simple?
    
- Is it redundant with another view?
    
- Are hidden columns impacting load time?
    

### Optimization Patterns

- **Reduce Columns:** Only display essentials; hide helpers.
    
- **Group Intelligently:** 1–2 levels max; avoid text grouping.
    
- **Merge Redundant Views:** Use filter controls for user flexibility.
    

---

## 🧮 Formulas

**Docs:** [Formula Reference](https://help.coda.io/hc/en-us/categories/37412218438221-Formulas)

### Core Patterns

|Pattern|Purpose|Performance|
|---|---|---|
|Lookup|Retrieve related data|✅ Excellent|
|Aggregation|Totals/Counts|⚠️ Moderate (table scan)|
|Conditional|Business logic|✅ Good if shallow|
|Multi‑Step (WithName)|Structured complex logic|⚠️ Moderate|

### Optimization Techniques

- Always **filter first** then compute.
    
- Replace `.Filter().Filter()` chains with one filter.
    
- Use **Relation** instead of manual text matches.
    
- Cache heavy formulas in separate columns updated by automation.
    

---

## 🔘 Buttons

**Docs:** [Buttons Guide](https://help.coda.io/hc/en-us/articles/39555768430349)

### Types

|Type|Use|Risk|
|---|---|---|
|Action|Update current row|Low|
|Batch|Update filtered set|Medium|
|Creation|Add new rows|Medium|
|Integration|Call external API|High (auth & idempotency)|

### Best Practices

- Verb‑first naming (“Mark Complete”, “Send Email”).
    
- Confirm() before destructive actions.
    
- Provide visible feedback (toast or status column).
    
- Make idempotent (safe multiple clicks).
    

---

## ⚙️ Automations

**Docs:** [Automations Overview](https://help.coda.io/hc/en-us/articles/39555778179853)

### Core Triggers

|Type|Example|
|---|---|
|Row Added / Changed|Update linked totals|
|Time‑based|Scheduled archiving|
|Button / Manual|Manual batch actions|

### Audit Questions

- Are triggers too broad? (`When any column changes` → restrict).
    
- Is there loop protection (status flag)?
    
- Are errors logged?
    
- Can it be merged with another automation?
    

### Optimization

- Use fewer, multi‑step automations instead of chains.
    
- Log both successes and failures.
    
- Lock tables before destructive updates.
    

---

## 📦 Packs (Integrations)

**Docs:** [Using Packs](https://help.coda.io/hc/en-us/categories/37412217390733-Packs)

### Key Audit Points

- What’s the **data direction** (import/export/bidirectional)?
    
- How is **auth** handled (shared vs user credential)?
    
- Is sync **incremental** or full reload?
    
- Are **rate limits** or **quotas** monitored?
    

### Best Practices

- Always maintain a **Sync Status Table** (timestamp, count, result).
    
- Use incremental updates when possible.
    
- Avoid storing secrets in formulas.
    

---

## 🧭 Pages & Navigation

**Docs:** [Organizing Pages](https://help.coda.io/hc/en-us/articles/39555897811405)

### Structure Checklist

- Logical grouping (2–3 levels max)
    
- Clear home/dashboard page
    
- Avoid orphaned or temporary pages
    
- Consistent naming (“Projects – Active”, “Projects – Archive”)
    

### Optimization

- Group related sections under folders.
    
- Keep dashboards lightweight (few embedded heavy views).
    
- Periodically review usage analytics; delete stale pages.
    

---

## 🔗 Cross‑Component Dependency Map

**Purpose:** Visualize interconnections for audit or optimization.

|Component|Depends On|Used By|Risk Level|
|---|---|---|---|
|Table: Projects|Clients|Tasks, Views|High|
|Automation: Sync Projects|Projects|Clients, Logs|Medium|
|Button: Create Task|Projects|Tasks|Low|

**Recommendations:**

- Use visual dependency mapping tools.
    
- Highlight circular references.
    
- Identify high‑risk nodes with many dependents.
    

---

**End of File — Updated Oct 2025 for verified Coda behavior and terminology alignment.**