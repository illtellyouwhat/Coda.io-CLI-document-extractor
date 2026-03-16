canvasElementTypes:
  - type: "text"
    canonicalName: "Text block"
    description: "Free-form text paragraph on the canvas."
    source: "https://help.coda.io/en/collections/1908924-working-in-the-canvas" :contentReference[oaicite:1]{index=1}

  - type: "heading"
    canonicalName: "Heading block (H1…H6)"
    description: "Title or section headings for structure on the canvas."
    source: "https://teamtreehouse.com/library/introducing-coda/build-a-simple-coda-doc" :contentReference[oaicite:2]{index=2}

  - type: "divider"
    canonicalName: "Line/Divider"
    description: "Visual separator between sections on the canvas."
    source: "https://teamtreehouse.com/library/introducing-coda/build-a-simple-coda-doc" :contentReference[oaicite:3]{index=3}

  - type: "image"
    canonicalName: "Image"
    description: "An image placed on the canvas (uploaded or embedded)."
    source: "https://help.coda.io/hc/en-us/articles/39560556616589-Add-images-to-docs-and-tables" :contentReference[oaicite:4]{index=4}

  - type: "embed"
    canonicalName: "Embed block"
    description: "Embedded content (video, external app, iframe) added to canvas."
    source: "https://teamtreehouse.com/library/introducing-coda/build-a-simple-coda-doc" :contentReference[oaicite:5]{index=5}

  - type: "table"
    canonicalName: "Table (base table) or Table view"
    description: "Tables or views embedded in the canvas. Base tables store data; views display it."
    source: "https://help.coda.io/hc/en-us/articles/39555768266893-Overview-Tables" :contentReference[oaicite:6]{index=6}

  - type: "view"
    canonicalName: "View of a table"
    description: "A table view embedded on a canvas (board, calendar, timeline, etc.)."
    source: “Same as Table Overview” (no separate link)  

  - type: "button"
    canonicalName: "Button"
    description: "Interactive button on the canvas that triggers actions/automations."
    source: "https://help.coda.io/hc/en-us/articles/39555758072717-Button-basics" :contentReference[oaicite:7]{index=7}

  - type: "control"
    canonicalName: "Control (component)"
    description: "Interactive control element (select list, checkbox, date-range, etc.)."
    source: "https://help.coda.io/hc/en-us/articles/39555865536013-Canvas-control-basics" :contentReference[oaicite:8]{index=8}

  - type: "formulaChip"
    canonicalName: "Formula chip"
    description: "Inline formula object placed on canvas (shows result of formula)."
    source: "https://help.coda.io/hc/en-us/articles/39555858394637-Basics-of-Coda-formulas" :contentReference[oaicite:9]{index=9}

  - type: "imageIcon"
    canonicalName: "Icon/Image (icon picker)"
    description: "Icon or small image used as embellishment or graphical block."
    source: "https://coda.io/%40simpladocs/icons/all-icons-1" :contentReference[oaicite:10]{index=10}

  - type: "canvasColumn"
    canonicalName: "Canvas Column"
    description: "Special column type where each row may render a full mini-canvas."
    source: "https://help.coda.io/hc/en-us/articles/39555806187917-Canvas-column-type" :contentReference[oaicite:11]{index=11}

---

## Normalized Record Schema (`pages/page-content.ndjson`)

- `pageId` — `canvas-…` identifier owning the element.
- `elementType` — canonical type from the list above (`heading`, `view`, `image`, `embed`, `link`, `control`, etc.).
- `ordinal` — zero-based position of the element as encountered in the HTML export.
- `text` — optional human-readable label/title when present (heading text, caption, button label).
- `codaId` — raw identifier surfaced by the export (e.g., `grid-…` for tables/views, `ctrl-…` for controls).
- `viewId` — populated for table views when matched to metadata exports (`views/<viewId>/view.json`).
- `attributes` — compact dictionary of element-specific details:
  - `displayColumnId`, `sorts`, `viewConfig` for table views.
  - `baseTableId` for view → table lineage.
  - `src`, `alt`, `title` for images/embeds.
  - `href`, `target` for prominent links.
  - `controlType`, `value` for controls sourced from the controls export.

The parser emits one JSON object per element so downstream LLM pipelines can filter/slice by `pageId`, `elementType`, or any of the enriched attributes without reparsing the raw HTML.
