# Yani UI style

This is how the portals should look and feel, and why. The component library `ui\` (`@yani/ui`) implements it. Rules for agents are the short list in `ui\CLAUDE.md`. This document is the reasoning behind that list.

## One line

Tonal, rounded, icon-led. Hierarchy through shade and space, not borders or color. Accent reserved for identity, primary action and signals.

## Why

Yani is a tool people open every day: MSP staff for hours, customers when something is wrong. Admin consoles tend to shout: uppercase labels, monospace ids, colored active states, borders around everything. That reads as technical and slightly hostile. The reference we chose (a rounded icon-led side panel) reads as calm and friendly instead. The difference is not decoration. It is fewer signals, each one meaning something.

Close cousins: Linear, Notion's sidebar, Apple System Settings. Not Material, not brutalist, not glassmorphism.

## Principles

### 1. Tonal layering, not lines

Depth comes from shades of one neutral. Page, panel, card, control, hover are steps on a ladder. Borders are almost never needed once the steps are right. A hairline is allowed only to split rows in a table or groups in a menu.

Light ladder: page `#f7f8fa`, card `#ffffff`, control `#f1f2f5`, hover `#e7e9ee`. The sidebar sits one step darker than the page (`#eceef2`) because it is chrome, not content.

Dark ladder: page `#0e0e12`, sidebar `#12141a`, card `#1b1c22`, control `#23242c`, hover `#2c2e37`. Same idea, not an inversion. Nothing is pure black or pure white.

No shadows on surfaces. A card that sits on the page does not float. Shadows are for things that actually hover over content: menus, popovers, dialogs.

### 2. Rounded and inset

Big containers use radius 16: cards, tables, the sidebar panel. Interactive elements use radius 8: buttons, inputs, nav rows, tiles. Pills use 999: badges, meters. The sidebar is inset 12px from the window edge so it reads as an object, not a wall.

### 3. Icon first

Every navigation row, stat tile and notice carries an outline icon. Icons come from `lucide-react` (2px round-cap stroke). The label is secondary; the icon is what the eye lands on. Components do not choose domain icons; the portal passes them in, so the same component can show a building for a site and a key for a license.

### 4. Generous rhythm

Rows are 44px. Buttons and inputs 36px. Cards have 20px padding. Groups are split by 8px of air plus a hairline, not by headings shouting in caps. Whitespace does the grouping.

### 5. Sentence case, always

No uppercase labels, no tracking, no monospace outside code blocks and raw identifiers. "Organization" not "ORGANIZATION". Text should read like language, not like a console.

### 6. Accent is rare

One brand color. It appears on: the logo tile, the customer initial tile, the primary button, focus rings, badges, meter fills, icon tiles inside stat tiles and notices. That is the whole list.

The current or selected item is never accent-colored. It is a neutral darker fill with heading-colored text. Color that shows state should be reserved for state that matters: success, warning, danger.

### 7. Status is tinted, not painted

Success, warning and danger appear as colored text on a translucent fill of the same hue (`--success-dim`, `--warn-dim`, `--danger-dim`). Solid status backgrounds are avoided; the one exception is the danger button on hover, where the solid fill is the warning itself.

### 8. Nothing is blank

Missing data renders a muted `-`. Empty lists render an empty state with an icon, a sentence and, when it makes sense, the action that fills it.

## Tokens

All in `ui\src\theme.css`. Portals import it once.

| Token | Light | Dark | Use |
|---|---|---|---|
| `--bg` | `#f7f8fa` | `#0e0e12` | page |
| `--surface` | `#ffffff` | `#1b1c22` | cards, tables, empty states |
| `--surface-subtle` | `#f1f2f5` | `#23242c` | inputs, secondary buttons, icon tiles |
| `--surface-hover` | `#e7e9ee` | `#2c2e37` | hover, selected, neutral badge, meter track |
| `--line` | `rgba(9,30,66,.08)` | `rgba(255,255,255,.08)` | hairlines |
| `--text-h` | `#172b4d` | `#f1f2f4` | headings, values, current item |
| `--text` | `#44546f` | `#b6bac1` | body |
| `--text-muted` | `#6b778c` | `#7d8290` | labels, hints, empty |
| `--accent` / `--accent-hover` / `--accent-dim` | `#0052cc` | `#4c9aff` | see principle 6 |
| `--success` / `--success-dim` | `#1f845a` | `#57d9a3` | ok, compliant, done |
| `--warn` / `--warn-dim` | `#b65c02` | `#ffab00` | waiting, almost full |
| `--danger` / `--danger-dim` | `#c9372c` | `#ff6b5e` | disabled, failed, over limit |
| `--radius-lg` / `--radius` / `--radius-sm` | 16 / 10 / 6 | | 16 for surfaces, 8 (literal) for controls |
| `--shadow-lg` | | | floating layers only |

The sidebar carries its own `--sb-*` ladder because it is one step darker than the page in light and near-black in dark. Everything else uses the shared tokens.

## Scale

| Element | Size |
|---|---|
| Nav row, table row | 44px |
| Button, input | 36px (`sm` 30px) |
| Nav icon | 22px |
| Button icon | 18px (`sm` 16px) |
| Logo and initial tile | 32px, radius 9 |
| Stat icon tile | 38px, radius 11 |
| Empty state icon tile | 48px, radius 14 |
| Page title | 1.35rem / 600 |
| Card title | 0.95rem / 600 |
| Body | 0.88 to 0.9rem |
| Label, table header | 0.78rem / 500 to 600, muted |
| Badge | 0.72rem / 600 |
| Meter | 6px |

## Do and don't

| Do | Don't |
|---|---|
| Split groups with air and a hairline | Add a border around a card |
| Use `--surface-hover` for the current item | Use `--accent-dim` for the current item |
| Write "Support tier" | Write "SUPPORT TIER" |
| Pass a lucide icon into a nav item | Let the library guess an icon from the label |
| Show `-` for a missing value | Leave the cell empty |
| Use a tonal badge for "Waiting" | Use an orange outlined mono badge |
| Give the danger button a tinted fill | Make every destructive button solid red |
| Keep one accent | Introduce a second brand color for the customer portal |

## When a new component is needed

Start from an existing one with the same shape (a row, a tile, a surface, a pill). Reuse its radius, height and text sizes from the table above. If the new thing needs a token that does not exist, add it to `theme.css` for both themes and note it here. If it needs a shadow or a border, ask whether a shade step would do instead. It usually does.
