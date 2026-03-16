# Coda Document Analysis Templates 

## Template A — **Initial Document Assessment**

Quick situational scan when inheriting or diagnosing a Coda document.

### Metadata

|Field|Value|
|---|---|
|Document Name||
|Owner||
|Last Modified||
|Primary Users||
|Primary Purpose||
|Size Snapshot|Tables: [ ] / Views: [ ] / Automations: [ ] / Packs: [ ]|

### Observations

**What’s Working:**

- [ ]
    
- [ ]
    

**Immediate Risks:**

- [ ]
    
- [ ]
    

**Next Steps:**

-  Audit dependencies
    
-  Identify redundant views
    
-  Collect performance data
    

**Refs:** [Tables & Views Hub](https://help.coda.io/hc/en-us/categories/37412217582221-Tables-and-views)

---

## Template B — **Redundant Views Audit**

Used to detect duplicate or near-duplicate connected views of the same base table.

**Data Collection**

- **Base Table:** [Name]
    
- **Connected Views:** [List all views, page locations]
    
- **For each view:** Extract config `{visibleColumns[], filters[], groups[], sorts[], layoutType}`
    

**Analysis**

|View|Overlap %|Filter|Group|Sort|Layout|Action|
|---|---|---|---|---|---|---|
|View A|100%|Same|Same|Same|Table|Merge|
|View B|80%|Same|Diff|Same|Board|Keep|

**Outcome:** Consolidate redundant views, archive duplicates, and update navigation links.

**Refs:** [Create Connected Table Views](https://help.coda.io/hc/en-us/articles/39555897467021)

---

## Template C — **Impact of Deleting Column X**

Predict breakage and plan migrations before column deletion.

**Search Checklist**

1.  Formulas referencing column X
    
2.  Views filtering/grouping/sorting by X
    
3.  Buttons/automations reading/writing X
    
4.  Packs or APIs pulling from X
    

**Mitigation Steps**

- Create **shadow column**
    
- **Backfill** data
    
- Switch formulas and automations to new column
    
- **Lock** critical views during change
    
- Verify before deleting X
    

**Refs:** [Automations](https://help.coda.io/hc/en-us/articles/39555778179853) | [Lock Tables & Views](https://help.coda.io/hc/en-us/articles/39555768033677)

---

## Template D — **Buttons & Automations QA Matrix**

Evaluate reliability and safety of automations and user-triggered buttons.

|Check|Description|Status|
|---|---|---|
|Idempotent|Repeated runs produce consistent results|[ ]|
|Loop Guard|Prevents automation/button recursion|[ ]|
|Error Handling|Has failure paths and notifications|[ ]|
|Batch Logic|Uses row sets, not loops|[ ]|
|Confirmation|User prompt before destructive action|[ ]|
|Test Coverage|Happy/failure/edge paths verified|[ ]|

**Refs:** [Automations in Coda](https://help.coda.io/hc/en-us/articles/39555778179853)

---

## Template E — **Canvas & Canvas Columns Review**

Audit usage of rich text surfaces and embedded mini-canvases.

|Location|Type|Volume|Heavy Content?|Recommendation|
|---|---|---|---|---|
|Page X|Canvas|Large|No|OK|
|Table Y|Canvas Column|High|Yes|Convert to Detail View|

**Guidelines:**

- Prefer **detail views** over per-row canvases for performance.
    
- Keep canvas content light (text/images under ~100 KB per row).
    
- Consolidate templates into reusable detail pages.
    

**Refs:** [Canvas Overview](https://help.coda.io/hc/en-us/articles/39555851326221) | [Canvas Column Type](https://help.coda.io/hc/en-us/articles/39555806187917)

---

## Template F — **Dashboard Design Chooser**

Map data type and decision intent to ideal Coda view.

|Use Case|Recommended View|Reason|
|---|---|---|
|Status pipeline|Board|Group by stage; drag-and-drop updates|
|Scheduling|Calendar|Date-driven workflows|
|Multi-item spans|Timeline|Start/End visualization|
|Detailed record view|Detail|Lightweight read-only experience|
|Bulk editing|Table|Grid control + filters|

**Refs:** [Tables & Views Hub](https://help.coda.io/hc/en-us/categories/37412217582221-Tables-and-views)

---

## Template G — **View Config Diff Helper**

Compare two view JSONs to detect redundancy or drift.

**Input:** Two JSON objects: `A` and `B`  
**Fields to Compare:** `filters`, `groups`, `sorts`, `visibleColumns`, `layoutType`  
**Output:** Table showing differences and overlap ratio.

**Prompt Template:**

```
Compare view A and B configs.
Return JSON with differences and percentage overlap.
Suggest: [Merge / Keep both / Archive one].
```

---

## Template H — **Performance Snapshot**

Quick performance scan.

|Metric|Threshold|Measured|Notes|
|---|---|---|---|
|Doc load time|< 3 s optimal|||
|Largest table rows|< 25 k|||
|Active automations|< 10 recommended|||
|Filter chains > 2 levels|Avoid|||
|Heavy formulas (nested > 3)|Flag|||
|Canvas column count|< 500|||

**Refs:** [Performance Optimization Guide](https://help.coda.io/hc/en-us/articles/39555878926861) _(implied)_

---

## Template I — **Refactor Log Snapshot**

Mini change-tracking block for incremental updates.

|Date|Area|Change|Risk|Validation|Owner|
|---|---|---|---|---|---|
|YYYY-MM-DD|Views|Merged 3 redundant views|Low|✅ Tested|[Name]|
|YYYY-MM-DD|Columns|Migrated col X → col Y|Med|🧪 Pending|[Name]|

---

**End of File — Updated Oct 2025 for full parity with refactored SKILL.MD**