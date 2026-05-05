# style_infer subskill

Infer a project-wide visualization style from a reference paper (PDF) or example figure (image) and/or explicit user preferences, then **fill in `visualizations/info/style_guide.md`** so every subsequent plot_gen and interactive run inherits the same look.

`style_guide.md` is **always present** (the scaffold ships a placeholder with the Status line set to 🟡 *Placeholder*). This subskill's job is to flip that to 🟢 *Active*, populate the sections from the references / user notes, and re-render the affected plots. `info/style_refs/` is also always present (ships with a README explaining what goes there) — you drop the verbatim reference files into it.

Use when the user:

- uploads a paper, a figure from a paper, a screenshot of a chart, a brand style guide, or any image/PDF and says "match this style", "make my plots look like these", "use this paper's color scheme", "follow our lab's figure style", or similar
- tells you in plain text what they want — colors, fonts, plot type preferences, journal-specific guidelines (e.g. "Nature figures", "single-column NeurIPS"), or hex codes lifted from a brand kit
- gives a **plot-specific** styling instruction during a plot_gen run ("for the petal-scatter plot, use square markers", "log y on the concentration plot only") — these still belong in the style_guide as per-plot overrides
- both of the above (a reference + overrides)

Read this together with `../../SKILL.md` for the top-level rules.

## What the guide is and isn't

`info/style_guide.md` is **a guide, not a strict standard**. New plots and pages should follow it; existing scripts don't need to be audited for compliance, and you don't need to refactor old code unless the user asks. But the guide must always reflect the *latest* user intent — when the user requests a style change mid-project, update `style_guide.md` first, then update `PROJECT_PALETTE` / `helpers/utils.py` / the affected recipes, then re-render the impacted plots.

---

## Where everything lives

```
visualizations/
├── info/
│   ├── style_refs/         (reference materials — read-only after intake)
│   │   ├── nature-fig3.png
│   │   └── lab-style-guide.pdf
│   ├── style_guide.md      (the inferred + user-specified style; the source of truth)
│   ├── context.md          (gets a "Style guide active" callout when style_guide.md exists)
│   └── how_to_use.md
└── ...
```

The `info/style_refs/` folder is the *only* place reference uploads live. Don't scatter copies elsewhere.

---

## Step 1 — Intake the references

For each reference the user provides:

1. Copy the file verbatim into `visualizations/info/style_refs/<original_filename>`. Don't rename, don't transcode, don't pre-process. Future agents may want to look at the original. **Do this even if you can't see the image yourself** — the file still belongs in `style_refs/` for later sessions or models that *can* read it.
2. Note the type:
   - **Image** (`.png`, `.jpg`, `.svg`, `.webp`): a single figure to mimic.
   - **PDF**: typically a paper or a brand guide. May contain multiple figures.
3. **Check whether you can actually read the file.** If the running model has multi-modal vision and the file is an image / PDF you can decode, proceed to Step 2. If you can't read the image (no vision capability, or unsupported format), be honest with the user: "I've saved the reference at `info/style_refs/<file>` but I can't read it directly. Could you describe the style — palette / fonts / plot kinds — or shall I exit and you can come back with a model that can see images?" Do **not** invent style features you didn't actually observe.
4. If the user gave plain-text preferences instead of (or alongside) a file, just record those — the reference set may be empty.

The `info/style_refs/` folder always exists (the scaffold ships it with a `README.md`). Just drop the file in — don't recreate the folder.

## Step 2 — Extract style features

The deliverable is `info/style_guide.md`. Decide each of the following from the references + user notes; mark anything you couldn't infer as "not specified — follow plot_gen defaults".

**Color palette.** Pick out a small set of categorical colors (3–8) and any sequential / diverging scales used. Record as hex codes whenever possible. For images, sample dominant non-axis colors; for PDFs, look at figure captions for any explicit palette callouts and at the rendered figures themselves.

**Typography.** Font family for titles, axis labels, tick labels, annotations. Approximate font sizes (or relative weight: "axis labels ~1.1× tick labels").

**Figure dimensions.** Aspect ratio, single-column vs double-column width, target dpi (300 for print, 150 for web).

**Plot type preferences.** What chart kinds the reference uses heavily — e.g. "small multiples over single composite", "horizontal dot plots over bar charts", "violins with overlaid points instead of boxplots". Note any plot kinds the user explicitly *wants to avoid*.

**Axis & grid style.** Frame/spines visible? Which? Gridlines? Tick density? Tick direction (in/out/both)? Are zero lines emphasized?

**Legend & annotation style.** Legend placement, frame on/off, in-figure labels vs external legend, annotation arrow style.

**Marker / line styles.** Marker shape rotation, marker size, line widths, error bar caps.

**Backgrounds.** White / cream / colored panels. Facet header style.

If you genuinely can't infer something from the reference and the user didn't specify, leave it as "not specified" — don't guess.

## Step 3 — Reconcile with explicit user preferences

User-stated preferences **override** anything inferred from the reference. Example: if the reference uses red/blue but the user says "but make it colorblind-safe", switch to a colorblind-safe palette and note the override in style_guide.md ("user requested colorblind-safe; replaced inferred red/blue with Wong palette: #0072B2, #D55E00, …").

## Step 4 — Fill in `info/style_guide.md`

The scaffold ships a placeholder template at `info/style_guide.md` — **edit it in place**, don't recreate. Specifically:

1. Flip the **Status** line from `🟡 Placeholder` to `🟢 Active`.
2. Fill **References used** with one bullet per file in `style_refs/` and one prefixed `(user notes) —` for each plain-text user preference.
3. Fill the per-section bullets below — replace the "_not specified_" placeholders only where you actually have a decision; leave the others as-is so future agents know that area still falls back to defaults.
4. Add a first **Revisions** entry: `YYYY-MM-DD — initial guide built from <refs> + <user notes>`.

The template you're filling in matches the structure below (skip sections that don't apply):

```markdown
# Style guide

> **For agents:** every plot_gen and interactive run in this project must follow this guide. Mirror these choices into `PROJECT_PALETTE` in `plot_gen.py` and the matching helpers in `helpers/utils.py`, and use them in `streamlit/` pages too. Re-render existing plots (`bash generate_plot.sh --all`) when the guide changes.

## References used

- `style_refs/<filename>` — short note on what was taken from it (e.g. "palette + figure aspect ratio").
- _(plain-text user notes, if any)_

## Color palette

- Categorical: `#0072B2` (primary), `#D55E00` (secondary), `#009E73` (tertiary), …
- Sequential: viridis (or named scale + reasoning)
- Diverging: vlag, centered at 0 (or named scale + reasoning)
- Background: `#FFFFFF`
- Notes: _e.g. "colorblind-safe per user request — Wong 2011 palette"_

## Typography

- Family: DejaVu Sans (or whatever)
- Title: 12 pt, regular
- Axis labels: 11 pt
- Tick labels: 9 pt
- Annotations: 9 pt italic

## Figure dimensions

- Default size: 7 × 5 in (single panel), 10 × 4 in (small multiples)
- DPI: 300 (print)
- Aspect-ratio rule of thumb: _…_

## Plot type preferences

- Prefer: small multiples over single composite; dot plots; violins with overlaid points.
- Avoid: 3D plots, dual y-axes, pie charts.

## Axis & grid

- Top + right spines off, bottom + left spines on (1 pt).
- Y gridlines on (light grey, 0.5 pt); x gridlines off.
- Tick direction: out, length 3.

## Legend & annotation

- Legend: top-right inside frame when ≤ 4 entries; below figure otherwise. No frame.
- Direct annotations preferred over legends when possible.

## Marker / line

- Marker rotation: o, s, ^, D
- Default marker size 24 (scatter), line width 1.5.

## User overrides (project-wide)

- _e.g. "user requested colorblind-safe — applied"_
- _e.g. "user wants log y by default for any concentration plot — applied"_

## Per-plot / per-page overrides

_Specific styling decisions that apply only to one named recipe (PROJECT_RECIPES key) or one streamlit page. Newly-generated plots/pages should respect these; existing ones should be re-rendered when the corresponding entry is added or changed._

- **`petal-length-vs-width-by-species` (plot_gen recipe):** square markers (`marker="s"`) instead of circles, per user preference 2026-04-12.
- **`pages/2_species_explorer.py` (streamlit):** use Wong palette regardless of project default; user wants direct comparison with their published figure.

## Revisions

_Append a line here whenever the guide changes. Format: `YYYY-MM-DD — what changed — why`._

- _2026-04-10 — initial guide built from `style_refs/nature-fig3.png` and user notes._
```

## Step 5 — Wire it into the project

After writing style_guide.md:

1. **Update `info/context.md`.** Add (or update) a callout near the top so every future session sees it before doing any plot work:

   ```markdown
   ## Style guide active

   This project has a visualization style guide at `info/style_guide.md` (built from references in `info/style_refs/`). **Read it before any plot_gen or interactive work and follow it for every new figure / page.** When the user asks for a plot, mirror the palette / typography / plot-type preferences into `PROJECT_PALETTE` and the recipe entries.
   ```

2. **Update `plot_gen.py`'s `PROJECT_PALETTE`** (if `plot_gen.py` already exists) with the hex codes from the guide. Update `set_research_theme()` in `helpers/utils.py` if typography/spines/grid choices differ from the scaffold defaults.

3. **Re-render existing plots** if any `PROJECT_RECIPES` entries already exist, so they pick up the new style: `bash generate_plot.sh --all`. Confirm with the user first if the project is large.

4. **Update `streamlit/` pages** to use the same palette (import `PROJECT_PALETTE` from `plot_gen.py`).

5. **Append a one-line entry to `info/context.md`'s activity log:** "**YYYY-MM-DD HH:MM** — style_infer — built style_guide.md from `style_refs/<filename>`. Re-rendered N existing plots."

## When the style guide already exists

If the user gives you a new reference, a new project-wide override, or a per-plot styling tweak and a `style_guide.md` already exists, treat the existing guide as the baseline:

1. Add any new reference file under `info/style_refs/` (don't replace existing references — keep the history).
2. Update only the sections that change. For a per-plot or per-page tweak, append/update an entry under "Per-plot / per-page overrides" rather than editing the project-wide sections.
3. Add an entry to "Revisions" at the bottom noting what changed and why.
4. Apply the change in code: update `PROJECT_PALETTE` / `helpers/utils.py` / the affected `PROJECT_RECIPES` entry / the streamlit page. Re-render the impacted plots — typically `bash generate_plot.sh --recipe <slug>` for a single recipe, or `--all` if the change is project-wide.

You don't need to audit older scripts for discrepancies with the updated guide. The guide drives forward; you only revisit what the user actually wants regenerated.

## When NOT to use this subskill

- If the user just asks for "a plot" without any style intent, don't run style_infer — let plot_gen use its defaults.
- If the user uploads an image of *data* (a chart they want analyzed for content, not for style), this is not the right subskill.

## Reference

When deciding sensible defaults for anything the reference / user notes don't pin down (e.g. "what kind of palette goes here?", "should I use a sequential or diverging map?", "how many tick marks?"), consult `../../references/figure-design-guidelines.md` — the ten-rules-for-better-figures cheat sheet (Rougier et al. 2014). It's the source for the colormap-category split (sequential / diverging / qualitative), the colorblind-safe palette suggestion, and the chartjunk / message-trumps-beauty framing baked into this subskill. Use it as guidance when filling gaps; cite it inline when explaining a recommendation to the user.
