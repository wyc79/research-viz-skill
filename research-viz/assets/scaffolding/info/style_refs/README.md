# style_refs/

Reference materials that drive `info/style_guide.md` — papers, individual figures, brand guides, screenshots — kept here verbatim so a future agent (or a human) can re-read them.

## What goes here

Drop any of the following into this folder when the user provides them:

- A **paper PDF** the user wants their figures to match — `nature-reviews-cancer-2020.pdf`, etc.
- A single **figure image** lifted from a paper or report — `gentle-introduction-fig3.png`, `lab-banner-poster.jpg`.
- A **brand guide PDF** from the user's group / department / publisher — `university-brand-guide-v3.pdf`.
- **Screenshots** of charts the user likes — `dashboard-screenshot.png`.

The convention: keep the original filename when reasonable; if the user uploads `Screenshot 2026-04-12 at 14.01.png` you can rename it to something descriptive like `linked-brushing-screenshot.png` — but **don't transcode, crop, or pre-process**. Future agents may want to look at the originals.

## What doesn't go here

- The agent's own **inferred** style guide → that lives in `info/style_guide.md`.
- The user's **plain-text style preferences** ("colorblind-safe palette, no grids, square markers") → record those directly in `info/style_guide.md` under "References used", no file needed.
- Reference materials that aren't visual style — domain knowledge, cited papers, dataset documentation → those belong somewhere else (`info/project_specific_knowledge.md`, or a project-level `references/` folder).

## How style_guide.md picks this up

When the **style_infer** subskill runs (the user provides a reference or expresses preferences), it:

1. Copies the file verbatim into this folder.
2. Reads it (if the model has multi-modal vision; otherwise asks the user to describe it).
3. Fills in `info/style_guide.md` with the palette / typography / plot-type preferences derived from each entry here.
4. Adds a line under `style_guide.md`'s "References used" section naming this file and what was taken from it.

If this folder is empty and the project has no style preferences, that's fine — `info/style_guide.md` stays as the placeholder template and `plot_gen` falls back to its sensible defaults (seaborn `colorblind` palette, `set_research_theme()` rcParams).
