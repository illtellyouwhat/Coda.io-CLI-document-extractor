# 🦩 Understanding Coda.io Document Structure  
*A Human-Readable Reference for Developers and Analysts*

---

### 🧠 In one line:
> **Coda is a graph of data, logic, and presentation.**  
> Tables define *what exists*, formulas define *how it behaves*, and canvases define *how it’s experienced*.

---

## 1. The Big Picture

A **Coda document** is both a **database** and a **canvas**.  
It combines structured data (tables) with interactive pages (canvases) that visualize or manipulate that data through controls and formulas.

Every Coda doc can be described as a **graph** of nodes and edges:

```
Doc
 ├── Pages (Canvas surfaces)
 │    ├── Controls (Canvas inputs)
 │    ├── Embedded Views of Tables
 │    └── Named Formulas
 ├── Tables (Base data grids)
 │    ├── Columns (Fields, sometimes formulas or buttons)
 │    ├── Rows (Data entries)
 │    └── Relations (Lookups to other tables)
 ├── Relations (Edges between tables)
 ├── Named Formulas (Global computed values)
 └── Controls (User-facing inputs)
```

Each node type has its own API endpoint and its own function in the ecosystem.

---

## 2. Vocabulary Overview

### 📘 **Doc**
The root container.  
Holds all pages, tables, controls, and formulas in a single workspace.  
Exported as: `doc.json`

---

### 📄 **Page**
Also called a **Canvas Page**.  
A page is the writing surface where content lives — text, tables, views, controls, buttons, etc.  
Each page may have a **parent page** (to form a hierarchy).  

- API: `GET /docs/{docId}/pages`
- Exported as: `pages/<pageId>.json`
- Fields:  
  - `id`, `name`, `contentType: "canvas"`  
  - `parent.id` → parent page
  - `browserLink` → link in UI

**Important:**  
Page metadata does *not* list its contents directly.  
To see which tables, views, or controls appear on a page, use:
- the **Views** list (`tableType=view`)  
- or the **Page Content endpoint** (`/pages/{pageId}/content`).

---

### 🧱 **Canvas**
The editable area of a page (similar to a Notion or Google Doc body).  
It can include:
- Text blocks  
- Embedded table **views**  
- **Canvas controls** (interactive inputs)  
- Buttons or charts

> The word *canvas* refers to the editable page surface, not a data object itself.

---

### 🗂️ **Table**
A structured dataset — Coda’s equivalent of a spreadsheet sheet or a database table.  
There are two kinds:

| Type | ID Prefix | Description |
|------|------------|--------------|
| **Base Table** | `grid-` | The master source of rows and columns. |
| **View** | `table-` | A filtered or formatted view of a base table, embedded on pages. |

- API: `GET /docs/{docId}/tables`
- Exported as: `tables/<tableId>/schema.json`
- Fields:  
  - `id`, `name`, `tableType: "base" | "view"`  
  - `columns[]` (with types, formulas, lookups)

---

### 📊 **Column**
Defines a field inside a table or view.  
Each column can have a **type**, **formula**, and optional **lookup relation**.

Common column properties:
- `name`: column name  
- `type`: data type (text, number, date, etc.)  
- `formula`: column-level formula  
- `lookup`: `{ table.id, table.name }` → cross-table reference  
- `controlType`: `"button"` if it’s an action column

---

### 🔗 **Relation (Edge)**
Represents a connection between two tables, usually through a **lookup column**.

Exported as: `relations/edges.jsonl`  
Each line defines one link:

```json
{
  "type": "relation",
  "fromTableId": "grid-Projects",
  "columnName": "Client",
  "toTableId": "grid-Clients",
  "formatType": "lookup",
  "isArray": true
}
```

This allows the doc to act like a relational database.

---

### 🧮 **Formulas**
Formulas are Coda’s computation layer — they calculate values, filter data, and respond to controls.

There are **two main kinds**:

| Kind | Where it lives | Scope | Example |
|------|----------------|-------|----------|
| **Column Formula** | Inside a column of a base table | Per-row calculation | `=[Price]*[Qty]` |
| **Named Formula** | Global doc-level object, often on a page | Computed once, reusable anywhere | `TotalSales := Sum([Orders].[Amount])` |

**API Paths**
- Column Formulas → via `/tables/{tableId}/columns`
- Named Formulas → via `/docs/{docId}/formulas`

Named formulas can reference tables, columns, and controls anywhere in the doc.

---

### 🎛️ **Controls**
Interactive inputs that let users filter or modify data dynamically.

There are **two distinct types**:

| Kind | Where it lives | API Source | Function |
|------|----------------|-------------|-----------|
| **Canvas Controls** | On a page’s canvas | `/docs/{docId}/controls` | Inputs like dropdowns, sliders, or textboxes used in formulas or filters |
| **Button Columns** | Inside table schemas | `/tables/{tableId}/columns` (look for `"controlType": "button"`) | Buttons that perform actions on rows/tables |

Canvas controls belong to pages; button controls belong to tables.

---

## 3. Graph Relationships (Edges)

| From | → | To | Description |
|------|---|----|-------------|
| `page.id` | → `parent.id` | Page hierarchy |
| `view.id` | → `sourceTable.id` | Each view links to its base table |
| `column.id` | → other `column.id` / `control.id` | Column formulas depending on other fields or controls |
| `control_canvas.id` | → `page.id` | Canvas controls live on a page |
| `control_button.id` | → `table.id` | Button columns belong to tables |
| `named_formula.id` | → `[tables, controls, columns]` | Global dependencies for named formulas |
| `lookup.column` | → `target.table` | Relational edge between tables |

---

## 4. Visibility vs Structure

Coda distinguishes between **structural data** and **visible content**.

| Layer | Retrieved by | Describes | Notes |
|-------|---------------|------------|-------|
| **Structural** | `/tables`, `/columns`, `/controls`, `/formulas` | What exists and how it’s wired | Needed for dependency graph |
| **Visual (Canvas)** | `/pages/{pageId}/content` | What’s actually visible and interactive on a page | Needed to understand UX and context |

- **Structural view** shows *potential connections* (what could interact).  
- **Canvas view** shows *actual composition* (what the user sees).  

For accurate LLM explanations of user behavior (“what happens if I change this?”), both layers are required.

---

## 5. Dependency Hierarchy

```
Canvas Control (page input)
   ↓
View Filter or Named Formula
   ↓
Base Table (grid)
   ↓
Column Formulas
   ↓
Other Derived Columns / Button Columns
```

---

## 6. Key Takeaways

1. **Tables** store data; **Views** display filtered slices of those tables.  
2. **Pages (Canvases)** are user interfaces that host **views**, **controls**, and **buttons**.  
3. **Controls** feed into **formulas** and **filters**, affecting what data users see.  
4. **Formulas** exist both at the column level (local) and document level (global).  
5. **Relations** tie tables together via lookup columns, forming the relational graph.  
6. To fully understand a document, you must merge:  
   - The **schema layer** (structure, formulas, relations)  
   - The **canvas layer** (what’s actually visible on each page)

---


