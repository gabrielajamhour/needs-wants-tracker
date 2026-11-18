---
version: 1.0
name: Livro-caixa
description: The visual identity of Needs/Wants Tracker — a calm cash-book on paper. Teal ink on an off-white page, numbers set in a monospaced face like columns in a ledger, and exactly three colours (Needs, Wants, Savings) that carry all the meaning. Nothing decorative; the money is the design.

colors:
  # Page and surfaces
  paper: "#f7f9f8"          # page background
  surface: "#ebf0ee"        # hover fills, selected rows, inline-edit row
  surface-row: "#eef3f1"    # table row hover
  field: "#ffffff"          # inputs, selects, emoji button
  # Ink
  ink: "#06525c"            # all text, primary button fill, strong rules
  ink-strong: "#03383f"     # hover/pressed state of ink-coloured things
  muted: "#2f737d"          # secondary text, labels, hints, inactive nav
  on-ink: "#f7f9f8"         # text on an ink fill
  # Lines
  border: "#9fb9b4"         # control outlines (inputs, ghost buttons, segmented)
  hairline: "#cfdcd8"       # header bottom, section rules, column dividers
  hairline-soft: "#e1e9e6"  # table rows, ledger rows, empty progress track
  # The three buckets: the only chroma in the interface
  needs: "#2b59c3"
  wants: "#c4532f"
  wants-text: "#b4482a"     # Wants as text (fill colour is 4.6:1, text uses the darker shade)
  savings: "#b8861c"
  savings-text: "#8a6410"   # Savings as text (fill colour is not text-safe)
  # Destructive confirmation only (never in lists)
  danger: "#b42318"

typography:
  font-text: '"Instrument Sans", system-ui, sans-serif'
  font-mono: '"DM Mono", ui-monospace, "SFMono-Regular", Menlo, Consolas, monospace'
  figure-hero:      { font: mono, size: 76px, weight: 500, lineHeight: 1.0, letterSpacing: -0.04em }
  figure-hero-sm:   { font: mono, size: 52px, weight: 500, lineHeight: 1.05, letterSpacing: -0.04em }
  figure-input:     { font: mono, size: 44px, weight: 400, lineHeight: 1.1, letterSpacing: -0.04em }
  figure-lg:        { font: mono, size: 30px, weight: 400, lineHeight: 1.1, letterSpacing: -0.03em }
  page-title:       { font: text, size: 30px, weight: 500, lineHeight: 1.2, letterSpacing: -0.03em }
  month-title:      { font: text, size: 22px, weight: 500, lineHeight: 1.2, letterSpacing: -0.02em }
  bucket-title:     { font: text, size: 20px, weight: 600, lineHeight: 1.3, letterSpacing: -0.015em }
  body:             { font: text, size: 15px, weight: 400, lineHeight: 1.5 }
  body-sm:          { font: text, size: 14px, weight: 400, lineHeight: 1.45 }
  label:            { font: text, size: 13px, weight: 400, lineHeight: 1.4 }
  eyebrow:          { font: text, size: 12px, weight: 500, lineHeight: 1.3, letterSpacing: 0.08em, transform: uppercase }
  amount:           { font: mono, size: 15px, weight: 400, numeric: tabular-nums }
  brand:            { font: text, size: 17px, weight: 600, letterSpacing: -0.01em }

rounded:
  sm: 2px     # bars, legend swatches, logo segments
  md: 4px     # buttons, inputs, segmented controls, menus
  full: 50%   # bucket dots only

spacing:      # 4px base; prefer these steps
  1: 4px
  2: 8px
  3: 12px
  4: 16px
  5: 24px
  6: 32px
  7: 48px
  8: 72px

layout:
  container: 1080px
  gutter-desktop: 40px
  gutter-phone: 16px
  header-height: 68px
  control-height: 44px
  control-height-small: 36px

components:
  button-primary:   { background: "{colors.ink}", text: "{colors.on-ink}", rounded: "{rounded.md}", height: 44px, padding: "0 18px", weight: 500, hover: "{colors.ink-strong}" }
  button-ghost:     { background: transparent, text: "{colors.ink}", border: "inset 1px {colors.border}", rounded: "{rounded.md}", hover: "{colors.surface}" }
  button-quiet:     { background: transparent, text: "{colors.muted}", rounded: "{rounded.md}", hover-background: "{colors.hairline-soft}", hover-text: "{colors.ink}" }
  button-icon:      { size: 44px, variant: ghost, aria-label: required }
  row-action:       { size: 36px, icon: 16px, text: "{colors.muted}", hover-background: "{colors.hairline-soft}" }
  text-input:       { background: "{colors.field}", text: "{colors.ink}", border: "1px {colors.border}", rounded: "{rounded.md}", height: 44px, padding: "0 12px" }
  segmented:        { border: "1px {colors.border}", rounded: "{rounded.md}", divider: "{colors.hairline}", active-background: "{colors.ink}", active-text: "{colors.on-ink}" }
  table-header:     { typography: "{typography.eyebrow}", text: "{colors.muted}", border-bottom: "1px {colors.ink}" }
  table-row:        { border-bottom: "1px {colors.hairline-soft}", padding: "11px 12px", hover: "{colors.surface-row}" }
  progress-bar:     { height: 8px, track: "{colors.hairline-soft}", rounded: "{rounded.sm}" }
  income-bar:       { height: 28px, gap: 3px, rounded: "{rounded.sm}" }
---

## Overview

Needs/Wants Tracker looks like a **cash-book (livro-caixa)**: a clean page, teal ink, figures lined up in a column. The person opens it to answer one question — *how much do I have left this month, and where did the rest go?* — so the design puts that number first and lets everything else stay quiet.

Three ideas carry the whole identity:

1. **Teal ink on paper.** The page is an off-white `{colors.paper}`; all text, rules and the primary button are one teal ink `{colors.ink}`. There is no black and no second brand colour.
2. **Figures in a ledger face.** Every amount, date and count is set in **DM Mono** with tabular figures, right-aligned in tables. Numbers line up like hand-ruled columns; text stays in **Instrument Sans**.
3. **Three colours, three buckets.** Needs (blue), Wants (coral) and Savings (ochre) are the *only* chroma in the interface. They appear as dots, bars and bucket titles — never as button fills or page decoration — so colour always means "which bucket".

The logo is the rule itself: a bar split 50 / 30 / 20 in the three bucket colours, followed by the wordmark **Needs/Wants**.

```
[■■■■■■■■|■■■■|■■]  Needs/Wants
  needs    wants savings
```

**Key characteristics**
- Off-white page, white only inside form fields.
- One ink colour for text, rules and the primary action.
- Monospaced, tabular, right-aligned money everywhere.
- Bucket colours used only to identify Needs / Wants / Savings, always next to their name.
- Separation by hairlines and whitespace; no cards with shadows, no gradients, no glass.
- Square-ish corners (2–4px): a precise, financial feel.

## Colors

### Ink and paper
| Token | Hex | Use | Contrast on paper |
|---|---|---|---|
| `paper` | #f7f9f8 | Page background | — |
| `surface` | #ebf0ee | Hover fill of ghost buttons, selected/inline-edit rows | — |
| `surface-row` | #eef3f1 | Table and list row hover | — |
| `field` | #ffffff | Inputs, selects, emoji button | — |
| `ink` | #06525c | Text, headings, primary button, strong rules (table header line, section top rules) | 8.4:1 |
| `ink-strong` | #03383f | Hover / pressed of anything ink-coloured | 12:1 |
| `muted` | #2f737d | Labels, hints, secondary text, inactive nav links, row-action icons | 5.1:1 |
| `on-ink` | #f7f9f8 | Text on an ink fill | 8.4:1 on ink |

### Lines
| Token | Hex | Use |
|---|---|---|
| `border` | #9fb9b4 | Outlines of inputs, ghost buttons, segmented controls, dotted ledger leaders |
| `hairline` | #cfdcd8 | Header bottom border, rules between sections, vertical dividers between bucket columns |
| `hairline-soft` | #e1e9e6 | Table rows, ledger rows, empty progress track |

### The buckets
| Bucket | Fill / dot / bar | As text | Notes |
|---|---|---|---|
| Needs | `needs` #2b59c3 | #2b59c3 (5.9:1) | Darkest of the three |
| Wants | `wants` #c4532f | `wants-text` #b4482a (5.0:1) | Mid lightness |
| Savings | `savings` #b8861c | `savings-text` #8a6410 (5.0:1) | Lightest fill; never use the fill colour for text |

The three differ in **lightness** as well as hue, so they stay distinguishable with colour-vision deficiency. Even so, a bucket colour is **never the only signal**: it always sits next to the word "Needs", "Wants" or "Savings".

### Status
- **Over the limit** does *not* get a fourth colour. It is shown by: the bar filled to 100% with diagonal white stripes, a small warning-triangle icon, and the text "67,99 € over the limit" in `ink` weight 600.
- **Success / info flash messages** use `ink` text with a `hairline` border; **error** flash messages use `ink` text, a 1px `ink` border and a warning icon. Keep them calm.
- `danger` #b42318 is reserved for the confirm button of a destructive dialog ("Delete expense"). It never appears in a list or table.

## Typography

### Families
- **Instrument Sans** (Google Fonts, variable `wdth,wght@75..100,400..700`) for all text.
- **DM Mono** (Google Fonts, weights 400 and 500) for every figure: amounts, dates, counts, percentages, the month's income.

```html
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Instrument+Sans:wdth,wght@75..100,400..700&family=DM+Mono:wght@400;500&display=swap" rel="stylesheet">
```

Every mono figure also gets `font-variant-numeric: tabular-nums`.

### Scale
| Token | Face | Size / weight | Use |
|---|---|---|---|
| `figure-hero` | Mono | 76 / 500, −0.04em | "Left to spend" on the Summary (desktop) |
| `figure-hero-sm` | Mono | 52 / 500 | Same number on a phone |
| `figure-input` | Mono | 44 / 400 | The amount field of the expense form |
| `figure-lg` | Mono | 30 / 400 | Spent per bucket on the Summary |
| `page-title` | Sans | 30 / 500, −0.03em | "Categories", "New expense" |
| `month-title` | Sans | 22 / 500 | "October 2026" between the month arrows |
| `bucket-title` | Sans | 20 / 600 | "Needs", "Wants", "Savings" (in the bucket's text colour) |
| `body` | Sans | 15 / 400, line-height 1.5 | Default |
| `body-sm` | Sans | 14 / 400 | Secondary lines, small buttons |
| `label` | Sans | 13 / 400 | Form labels, hints (`muted`) |
| `eyebrow` | Sans | 12 / 500, uppercase, +0.08em | Table headers, "Left to spend", group headings |

### Principles
- Headings are 500–600, never 700+. Emphasis comes from **size and the mono figures**, not from weight.
- Text is sentence case. Buttons are a verb + an object: "Save expense", "Add category", "Edit income", "Use Groceries" — not "Save", "Add", "OK".
- Use the real ellipsis character (…) in placeholders: "Name, e.g. supermarket…".

## Layout

### Container and spacing
- Content sits in a centred container of **1080px** max, with **40px** side padding on desktop and **16px** on phones.
- Spacing uses a 4px base: 4, 8, 12, 16, 24, 32, 48, 72. Typical: 8 between buttons, 16 between form fields in a row, 24 between field groups, 32–48 between page blocks, 72 at the bottom of a page.
- Content is **left-aligned**. Page titles are not centred; the only centred element is the month title between its arrows.

### Header
- Full-width, `paper` background, 1px `hairline` bottom border, 68px tall.
- Left: logo (bucket bar + "Needs/Wants"). Then the main nav: **Summary · Expenses · Categories** (Categories moves out of the ☰ menu; the menu is no longer needed).
- Active nav link: `ink`, weight 600, 2px `ink` underline that sits on the header's bottom border. Inactive: `muted`, hover `ink`.
- Right: primary button "+ New expense". On phones it becomes a 44px icon button with `aria-label="New expense"`.

### Responsive
| Width | Changes |
|---|---|
| ≥ 900px | Summary: hero number and income bar side by side; buckets in 3 columns. Categories: form column + list column. |
| 600–900px | Hero and income bar stack; buckets stay 3 columns if they fit, otherwise stack. Categories form above the list. |
| < 600px | One column everywhere. Header: logo mark only, three nav tabs, icon "+" button. Tables become stacked rows (date + name on one line, category and type below, amount right). Buttons in forms full width. |

Every tap target is at least 44×44px (row-action icons are 36px on desktop and grow to 44px under `@media (pointer: coarse)`).

## Elevation and depth

There is **no shadow** in the system, except a single soft shadow on popovers (the emoji picker dialog, a dropdown): `0 6px 20px rgba(6, 82, 92, 0.14)`. Hierarchy comes from:
- **Hairlines** (`hairline`, `hairline-soft`) between rows and sections.
- A stronger **1px `ink` rule** above important blocks: the table header, the categories form, the expense form, each category group heading, the table total.
- **Whitespace.**

No cards with borders on the Summary: the three buckets are ledger columns separated by vertical hairlines.

## Shapes

| Token | Value | Use |
|---|---|---|
| `rounded.sm` | 2px | Progress bars, income bar segments, legend swatches, logo segments |
| `rounded.md` | 4px | Buttons, inputs, selects, segmented controls, dialog |
| `rounded.full` | 50% | The 8px bucket dots only |

No pills. The old rounded "chips" and the "Active" status pill go away.

## Components

### Buttons
- **Primary** — `ink` fill, `on-ink` text, 44px tall, 18px side padding, 4px radius, weight 500. Hover `ink-strong`. One primary button per area.
- **Ghost** — transparent, `ink` text, 1px `border` outline (as `box-shadow: inset 0 0 0 1px`). Hover `surface`. For Cancel, Edit income, month arrows.
- **Quiet** — transparent, `muted` text, no outline. Hover `hairline-soft` fill and `ink` text. For repeated row actions: Rename, Archive, Restore.
- **Icon button** — ghost, 44×44, 18px stroke icon, `aria-label` required (month arrows, "+" on phones).
- **Row action** — 36×36 transparent icon button, 16px stroke icon in `muted`, hover `hairline-soft`. Used for Edit (pencil) and Delete (trash) in the expenses table, each with `aria-label="Edit Supermarket"` / `"Delete Supermarket"`.
- Small size: 36px tall, 12px padding, 14px text (44px on coarse pointers).

Icons are simple 24-unit stroke SVGs (stroke 1.9–2.4, round caps) in `currentColor`. No emoji as UI icons — emoji appear only as **category emojis**, which are user content.

### Form controls
- **Text input / select** — `field` background, 1px `border`, 4px radius, 44px tall, 12px padding, `ink` text. Label above (13px `muted`, 6px gap). Hints below (13px `muted`).
- **Search** — the only input with an icon: a 16px magnifier inside, left, `muted`.
- **Amount field** (expense form) — no box: a 2px `ink` bottom line, the figure in `figure-input` (DM Mono 44px), a `muted` "€" on the right.
- **Segmented control** — a row of options inside one 1px `border` outline, 4px radius, `hairline` dividers. Active option: `ink` fill, `on-ink` text. Used for the Type filter (All / Needs / Wants / Savings, each with its dot), the Categories filter (with counts in mono) and the bucket choice when adding a category.
- **Emoji button** — 44×44 white square with 1px `border`, the category emoji at 20px; opens the emoji picker dialog.
- **Focus** — every control shows `outline: 3px solid {colors.ink}; outline-offset: 2px` (ink, not a bucket colour, so focus never reads as "Needs") on `:focus-visible`.

### Month navigation
`[‹]  October 2026  [›]` — two ghost icon buttons around the `month-title`. On Summary the income sits on the same row at the right: "Income  1.800,00 €  [Edit income]". On Expenses the right side shows "18 expenses · 1.695,49 €" and an "All months" link sits after the arrows (replaces the old Month select).

### Summary: hero
- Left: eyebrow "LEFT TO SPEND", the figure in `figure-hero`, then "1.695,49 € of 1.800,00 € used this month" in `muted`.
- Right: eyebrow "WHERE THE INCOME WENT" and the **income bar**: one 28px bar with segments sized by amount spent — Needs, Wants, Savings in their colours, and the remainder as a hatched outline (`hairline` diagonal stripes). Below, a legend: swatch + "Needs 49%" … "Left 6%". The bar has `role="img"` and an `aria-label` with the percentages.

### Summary: bucket columns
Three equal columns, divided by vertical `hairline`s, under a `hairline` rule. Each column:
1. Bucket title in its text colour + "50% of income" (mono, `muted`) on the right.
2. Spent in `figure-lg`.
3. "Limit 900,00 €" (Savings: "Goal 360,00 €") in `body-sm` `muted`.
4. **Progress bar**: 8px, `hairline-soft` track, bucket-colour fill, 2px radius.
5. Status line: "12,50 € left" / "160,00 € to reach the goal" in `muted`; over the limit: triangle icon + "67,99 € over the limit" in `ink` 600, and the bar striped.
6. **Ledger rows**: emoji · category name · dotted leader (`border`, dotted) · amount (mono, right). Rows separated by `hairline-soft`.

### Tables (Expenses)
- No vertical borders, no grid. Header: `eyebrow` style, `muted`, with a 1px `ink` line under it.
- Rows: 1px `hairline-soft` bottom, 11px × 12px padding, hover `surface-row`.
- Columns: Date (mono, `muted`, "29 Oct") · Name (500) · Category (emoji + name) · Type (dot + name in bucket text colour) · Amount (mono, right-aligned) · actions (two row-action icons, right).
- Footer row: 1px `ink` top line, "Total of 18 expenses" in `muted`, total in mono 18px 500.
- Delete always asks for confirmation (a dialog naming the expense: "Delete “Supermarket, 49,00 €”?", buttons "Delete expense" in `danger` and "Cancel").

### Category list
- Left column: page title, one sentence of explanation, then the "Add a category" form under an `ink` rule: emoji button + name input, the bucket as a segmented control, "Add category" primary button.
- Right column: the filter segmented control, then one group per bucket. Group heading: bucket swatch + bucket name in `eyebrow` style and bucket text colour + "8 categories" (mono, right), with a 1px `ink` line under it.
- Each row (56px): emoji · name (500) · "Archived" (if archived) · usage count in mono `muted` ("12 expenses", "No expenses") · quiet "Rename" · quiet "Archive" / "Restore".
- **Rename inline**: the row turns into a form on `surface` — emoji button · name input · "Save name" (primary small) · "Cancel" (ghost small). Only one row is in edit mode at a time; the row keeps its height (no layout jump).
- **Archived rows**: `muted` text and a faint diagonal hatch background; no opacity (keeps contrast).

### Expense form
- Narrow column, 520px max, left-aligned inside the centred container.
- "← Back to expenses" link (`muted`), page title, then the form under an `ink` rule.
- Order: **Amount** (big) → **Name** (with the category suggestion line: "Suggested category: 🛒 Groceries · Needs [Use Groceries]", `aria-live="polite"`) → **Date** and **Category** side by side → "Missing a category? Manage categories" link *below* the select (never inside it) → "Save expense" + "Cancel".

### Flash messages
A full-width line under the header, inside the container: 12px × 16px padding, 4px radius, `paper` background, 1px border (`hairline` for success/info, `ink` for errors), `ink` text, a 16px icon on the left. `role="status"` (errors: `role="alert"`).

### Empty states
Plain text and one action, no illustration:
- Summary, no income: "Set this month's income to see your limits." + "Add income" button.
- Expenses, nothing recorded: "No expenses in October yet." + "Add the first expense".
- Expenses, filters with no match: "No expenses match these filters." + "Clear filters" link.

## Do's and Don'ts

### Do
- Set every amount, date, count and percentage in DM Mono with tabular figures; right-align amounts in tables.
- Use bucket colours only to say "this is Needs / Wants / Savings", always next to the word.
- Use the dark text shades (`wants-text`, `savings-text`) for bucket-coloured text.
- Separate with hairlines and space; put a 1px `ink` rule above the important blocks.
- Keep one primary (ink) button per area; use quiet buttons for repeated row actions.
- Give every icon-only button an `aria-label` that names its object ("Delete Supermarket").

### Don't
- Don't paint a button, header band or table header with a bucket colour (the old full-colour table headers go away).
- Don't add a fourth colour for "over the limit"; use stripes, icon and text.
- Don't centre page titles, filter rows or table cells.
- Don't use shadows, gradients (except the functional hatch/stripes), glass effects or pills.
- Don't use violet or purple anywhere (the old Wants purple `#6b4fa3` is retired).
- Don't use emoji as interface icons; emoji are category content only.
- Don't put links or other elements inside a `<select>`.

## Implementation notes (for the commits)

Suggested order, one commit each:
1. **Tokens** — replace the `:root` block in `static/styles.css` with the colours, type, radius and spacing above; load the two Google Fonts in `templates/layout.html`; set `body` to `paper` / `ink` / Instrument Sans.
2. **Logo and header** — new `static/logo.svg` (the 50/30/20 bar), wordmark, three nav links with the underline indicator, remove the ☰ menu (`menu.js` no longer needed).
3. **Buttons and form controls** — primary / ghost / quiet / icon / row-action; inputs, selects, segmented control, focus ring.
4. **Summary** — hero number + income bar, bucket columns with ledger rows (replaces `.cards` and the coloured breakdown tables).
5. **Expenses** — month row with count and total, filter bar with segmented Type (drop the Month select), clean table with mono amounts and icon actions, total row.
6. **Categories** — two-column layout, grouped list, inline rename, archived style (drop the duplicate Edit column and the status pill).
7. **Expense form** — narrow column, big amount field, suggestion line, fix the "Manage categories" link that is currently inside the `<select>` in `templates/expense_form.html`.
8. **Phone layout** — header at < 600px, stacked tables, full-width form buttons; check 375px for horizontal overflow.

Mapping from current CSS:
| Current | Becomes |
|---|---|
| `--color-primary` #1f6f6b | `ink` #06525c |
| `--color-text` #1f2328 | `ink` #06525c |
| `--color-muted` #5b6470 | `muted` #2f737d |
| `--color-border` / `--color-border-strong` | `hairline` / `border` |
| Needs #1f6f6b, Wants #6b4fa3, Savings #1f5fa8 | `needs` #2b59c3, `wants` #c4532f, `savings` #b8861c |
| `.chip`, `.status-badge` | segmented control; plain "Archived" text |
| `.card`, `.cards` | bucket columns |
| `.table-cards` full-grid desktop style | hairline rows, left-aligned, amounts right |
