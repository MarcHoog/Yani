# ui

`@yani/ui`. React component library shared by staff portal and customer portal.

## Stack

React 19, Vite 8, TypeScript strict, plain CSS with theme vars (`src\theme.css`), oxlint.
Tests: Vitest 4 browser mode, real Chromium via Playwright. No jsdom.

## Run

Once: `pnpm install` at repo root, then `pnpm exec playwright install chromium` here.

| command | does |
|---|---|
| `pnpm dev` | gallery on http://localhost:5173. Every story, light and dark side by side |
| `pnpm test` | behaviour tests + screenshot compare, headless Chromium |
| `pnpm test:update` | accept changed screenshots. Look at the diff PNGs first |
| `pnpm test:ui` | Vitest UI, watch mode, live browser preview |
| `pnpm typecheck` | tsc |
| `pnpm lint` | oxlint |

## Layout

```
src\theme.css                 vars, fonts, resets. Consumer imports once.
src\index.ts                  public exports
src\<Name>\<Name>.tsx         component
src\<Name>\<Name>.css         styles, classes prefixed y-
src\<Name>\<Name>.stories.tsx states worth looking at
src\<Name>\<Name>.test.tsx    behaviour tests + screenshotStories(stories)
src\test\                     setup (theme import) and screenshotStories helper
gallery\                      dev page, discovers *.stories.tsx
```

## Rules

- Story file: `export default { title }`, every named export is one state, takes no props. Gallery and screenshot tests both read them.
- Every component ships all four files. New component = copy the layout above, register in `src\index.ts`.
- Only components used by more than one portal live here. A component with a single consumer stays in that portal until a second one needs it, then moves.
- Props in, callbacks out. No router, no fetch, no API types, no global state. Navigation is `href` plus `onNavigate` callback. Portals wire the router and the data.
- Screenshot baselines live in `__screenshots__` next to the test and are committed. Rendered on Windows. Regenerate on the same OS.
- Themes switch on `[data-theme]`, on any element, not only `html`. Gallery uses this to show both at once.
- Theme preference is three-state: `system` (default, follows OS, nothing stored), `light`, `dark` (stored in `localStorage.theme`). `useTheme()` owns this. Portals copy the head script from `index.html` so the attribute is set before first paint.
- Code must read without comments. If a component needs a comment block, split it.

## Style

Tonal, rounded, icon-led. Hierarchy through shade and space, not borders or color. Accent only for identity, primary action and signals. Long form with rationale: `docs\style.md`. Every new component follows these or does not merge.

- Neutral ladder from `theme.css`: `--bg` page, `--surface` card, `--surface-subtle` control, `--surface-hover` hover. Sidebar has its own darker ladder (`--sb-*`). No other grays.
- No borders on surfaces or controls. Hairline `--line` only to split rows or groups. No `box-shadow` on surfaces. `--shadow-lg` only on things that float (popovers, menus).
- Radius: 16 (`--radius-lg`) for cards, panels, tables. 8 for buttons, inputs, rows, tiles. 999 for badges and meters. Nothing else.
- Rows are 44px. Buttons and inputs 36px (`sm` 30px). Icons 20-22px in rows, 18px in buttons, 16px `sm`.
- Text is sentence case everywhere. No `text-transform: uppercase`, no `letter-spacing` tracking on labels, no `--mono` outside code and ids.
- Labels and table headers: 0.78rem, weight 500-600, `--text-muted`. Body 0.88-0.9rem. Card titles 0.95rem/600 `--text-h`. Page title 1.35rem/600.
- Active and selected states are neutral fills (`--surface-hover` or `--sb-active`) with `--text-h`. Never accent background for "current".
- Accent (`--accent`) is allowed on: logo and initial tiles, primary button, focus ring, badges and meters, icon tiles in StatTile and Notice. Nowhere else.
- Status uses `--success` / `--warn` / `--danger` text on their `-dim` fills. Never solid status backgrounds except danger button hover.
- Icons are `lucide-react`, outline, passed in as `ReactNode` by the portal. Components never pick domain icons themselves. Notice picks tone icons.
- Dark theme is the same ladder in dark, not an inversion. Panel `#12141a`, card `--surface`, page `--bg`.
- Empty and missing values render a muted `-`, never blank.
