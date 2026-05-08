---
name: bancolombia-report
description: Use this skill when the user asks to generate, update, or extend a Bancolombia-branded analytical report — HTML interactive page, LaTeX/PDF executive document, or Markdown summary — for the DICAGI 2022 Modelo de Capacidad project (or similar analytical deliverables). The skill provides templates with the corporate palette (#FDDA24, #2C2A29, #ABA59D), section conventions (problem → data → bottleneck → approaches → physics mapping → results → honest conclusions), embedded SVG diagrams, Plotly charts, KaTeX math, and three-layer pedagogical structure (👥 simple · 🔬 técnico · ⚛️ físico).
---

# Bancolombia analytical-report skill

Generates polished, brand-consistent reports for Bancolombia analytical deliverables. The skill knows the corporate palette, the typical section structure, and how to embed self-contained visualizations (SVG + Plotly + KaTeX) so the resulting HTML works offline (with CDN dependencies for the libraries).

## When to use this skill

Trigger this skill when the user asks for:
- An interactive HTML report explaining a Bancolombia analytical project.
- A LaTeX or PDF executive document with corporate branding.
- An update or section addition to an existing report in `docs/informe_*` of this project.
- A new analytical deliverable that should follow the same visual identity.

Do NOT use this skill for general documentation that has no corporate branding need (use the user's CLAUDE.md or simple Markdown files instead).

## Corporate palette

```css
--amarillo:        #FDDA24   /* Candlelight — primary accent */
--amarillo-claro:  #FFE970   /* highlight, hover */
--amarillo-oscuro: #E5BD00   /* emphasis, links */
--negro:           #2C2A29   /* Dune — text, dark sections */
--gris:            #ABA59D   /* Cloudy — neutral */
--gris-claro:      #D9D5CF   /* dividers, subtle bg */
--gris-oscuro:     #6B6863   /* secondary text */
--blanco:          #FFFFFF
--rojo:            #D62828   /* warnings only */
--verde:           #2D8F4E   /* positive only */
```

Use yellow + black as the primary signal. Reserve red and green for status semantics. Never introduce non-corporate hues without explicit user request.

## Visual conventions

### Typography
- **Inter** for UI/body (300 light, 400 regular, 600 semibold, 700 bold, 800 black). Load from Google Fonts CDN.
- **JetBrains Mono** for code, IDs, technical tokens.
- Hero headlines: `clamp(2.4rem, 6vw, 4.5rem)` with letter-spacing `-0.03em`.
- Section h2: `clamp(1.8rem, 3.5vw, 2.6rem)` with letter-spacing `-0.02em`.

### Layout patterns
- Sticky top nav with backdrop blur.
- Alternating section backgrounds: white → `#FAFAFA` → `dark` (negro). Never two consecutive `dark`.
- Hero: black background with radial yellow accent + thin yellow band at the bottom.
- Section padding: `80px 32px`.
- Container max-width: `1200px`.

### Reusable components
- **`.card`**: white card with yellow top-bar that animates on hover.
- **`.kpi`**: large number + label, optionally `.kpi.featured` with black bg.
- **`.insight`**: gradient yellow box with `.insight-tag` tagline.
- **`.honesty`**: black box with yellow border + accents — for hard truths and diagnostics.
- **`.decision`**: gray box with black border — for justified modeling decisions.
- **`.pipeline`**: 5-step horizontal flow with arrow connectors (CSS `::after`).
- **`.roadmap`**: vertical timeline with circular yellow markers.

## Standard section structure for analytical reports

Follow this 8-section template unless user requests otherwise:

1. **Hero / Portada** — title, subtitle, 4 hero metrics (KPIs en gradient yellow stripe).
2. **El problema** — what the test/project asks. Include an SVG diagram of the entity hierarchy.
3. **Los datos** — inventory of source tables as cards with row counts.
4. **El hallazgo / cuello de botella** — the non-obvious insight discovered in EDA. Use `.honesty` box.
5. **Los caminos / enfoques** — how the problem was solved. Use `.approach-grid` with levels lvl1–lvl4.
6. **Mapeo a física** (optional) — Hamiltonian formulation, Ising mapping, MCMC. Use `dark` section.
7. **Resultados** — KPIs grid + comparison charts (Plotly).
8. **Conclusiones críticas** — 5-7 lessons that go beyond the obvious + roadmap.

## Three-layer pedagogy

Where appropriate, explain key concepts in three layers:
- 👥 **Simple** (analogía cotidiana, sin jargon)
- 🔬 **Técnico** (fórmulas, código, estadística)
- ⚛️ **Físico** (mapeo a sistema físico — Ising, Boltzmann, mean-field)

Each layer is a paragraph or short section. Don't force all three when one suffices.

## Charts (Plotly via CDN)

Use `https://cdn.plot.ly/plotly-2.35.2.min.js`. Default chart layout:

```javascript
const baseLayout = {
    paper_bgcolor: 'white', plot_bgcolor: 'white',
    font: { family: 'Inter, sans-serif', color: '#2C2A29', size: 12 },
    margin: { l: 60, r: 30, t: 40, b: 60 },
    xaxis: { gridcolor: '#D9D5CF', linecolor: '#ABA59D', ticks: 'outside' },
    yaxis: { gridcolor: '#D9D5CF', linecolor: '#ABA59D', ticks: 'outside' }
};
```

Categorical color order: `[negro, amarillo, gris, amarilloOscuro, verde, rojo]`. Sequential colorscale: white → amarillo-claro → amarillo → amarillo-oscuro → negro.

Suppress modebar (`{ displayModeBar: false, responsive: true }`) for embed-quality output.

## Math (KaTeX)

Include KaTeX CSS + auto-render via CDN. Wrap displayed equations in `<div class="formula">$$ ... $$</div>` so they render with the black box / yellow text treatment.

## SVG diagrams

Prefer inline SVGs with `viewBox` for the main conceptual diagrams (entity hierarchies, Ising spins, flow). They scale, print well, and avoid external assets. Use the corporate palette for fills/strokes; never bring in random colors.

## File outputs

Place outputs under `docs/`:
- `docs/informe_interactivo.html` — single-page HTML with embedded CSS + Plotly via CDN.
- `docs/informe_ejecutivo.tex` — LaTeX source for executive PDF.
- `docs/informe_ejecutivo.pdf` — generated by `src/modelo_capacidad/generate_report.py` (reportlab) or by compiling the .tex.

## When extending an existing report

1. Read the current `docs/informe_interactivo.html` first.
2. Match the existing CSS variables and components — don't reintroduce styles.
3. Add new sections following the 8-section template (skip or merge as needed).
4. Validate that the HTML renders correctly (open in browser to confirm).
5. Update the `.tex` file in parallel if it exists.
6. Update `src/modelo_capacidad/generate_report.py` if the user wants the PDF synced.

## Constraints

- HTML files must be self-contained (no local assets, all dependencies via CDN).
- Don't modify the corporate palette; if a new color is needed, add it as a CSS variable derived from the existing palette.
- Tables go inside `.tabla-wrap` for horizontal scroll on mobile.
- Test responsive breakpoints at 768px (single column for grids).
- Keep first paint fast: defer non-critical scripts, minimize initial DOM.
