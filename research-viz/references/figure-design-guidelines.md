# Figure design guidelines

A short, opinionated set of *guidelines* (not hard rules) for designing research figures. Use these when helping the user think about a plot, when sanity-checking output, and when prompting the user for design choices that will land in `info/style_guide.md` and `PROJECT_RECIPES`.

These are **defaults to lean on, not gates to enforce**. If the user wants something different, follow the user — but feel free to flag a tension ("you asked for a 3D bar chart; that often hides ordering — do you want me to try a heatmap instead, or proceed?").

## Source

Distilled from:

- Rougier, N. P., Droettboom, M., & Bourne, P. E. (2014). *Ten Simple Rules for Better Figures.* PLOS Computational Biology, 10(9), e1003833. <https://doi.org/10.1371/journal.pcbi.1003833>
- Companion code: <https://github.com/rougier/ten-rules>

Tufte, *The Visual Display of Quantitative Information* (the source of "chartjunk") and the matplotlib / seaborn docs are the secondary references behind several rules below.

---

## The ten rules, condensed

### 1. Know your audience

Who is going to read this figure, and under what conditions? Rougier et al. distinguish five audience strata, each needing different effort: **yourself**, **direct collaborators** (least design overhead — everyone already knows the data), **the broader scientific audience** (a journal figure must stand on its own), **students** (often need extra explanation to grasp the concept), and **the general public** (the hardest — strip to the most salient point; see Figure 1 in the paper, which is a remake of a NYT cancer chart).

*Prompt the user when ambiguous:* "Is this for the paper, a talk, a slide for non-experts, or your own working notebook?" The answer changes font sizes, the appropriate level of detail, and whether legends or in-figure annotations work better.

### 2. Identify your message

Each figure should make one main point. If you can't summarize the figure in one sentence, it probably needs to be split or simplified. The structure of the figure (what's on x, what's on y, what's encoded in color) should serve that one sentence.

*Practical move:* before writing code, restate the user's request as a single message ("the bigger the dose, the lower the response, and this holds across both groups"). Pick the chart type that makes that message land first.

### 3. Adapt the figure to the support medium

Print, screen, slide, and poster all have different constraints — DPI, aspect ratio, expected viewing distance, color reproduction. A figure that's perfect at 7×5 in for a paper will look anaemic on a 16:9 slide and tiny on a poster.

*Defaults the skill uses:* 300 dpi PNG + PDF for paper-grade plots, 7×5 in for single-panel research figures, larger fonts for talks/posters. When the user mentions where the figure will end up, adjust `figsize` / font sizes accordingly and bake into `PROJECT_RECIPES['extra']`.

### 4. Captions are not optional

The figure should be readable without the surrounding text — assume the reader skims figures first. Axes, legends, units, and a clear title carry most of that weight; any context that doesn't fit on the figure goes in a caption.

*Practical move:* always set explicit axis labels with units and a title that states the message (not just the variables). When the user is producing a paper figure, prompt for the intended caption and either render parts of it as a subtitle or save it alongside the figure (e.g. `caption.txt` next to `figure.png`).

### 5. Do not trust the defaults

Library defaults rarely produce a publication-quality figure. Spines, tick density, legend frame, font size, marker size, line width, padding, color cycle — almost all of these need a once-over. The skill's `set_research_theme()` (in `helpers/utils.py`) is one such once-over; treat it as a starting point, not a finish line. (Rougier et al. illustrate this with figure-4-left vs figure-4-right in the companion repo — same data, very different readability.)

*Defaults the skill leans on:* hide top/right spines, drop the legend frame, keep gridlines light, prefer the seaborn `colorblind` palette, render at 300 dpi.

### 6. Use color effectively

Color is one of vision's strongest dimensions — Tufte's "greatest ally or worst enemy". The paper splits colormaps into three categories you should pick consciously:

- **Sequential** — one variation of a single hue, for quantitative data running low → high (e.g. viridis, magma, Purples).
- **Diverging** — two hues meeting at a neutral midpoint, for deviation from a meaningful zero / median (e.g. RdBu, vlag).
- **Qualitative** — distinct hues for discrete / categorical data (e.g. seaborn `colorblind`, Wong 2011: `#0072B2`, `#D55E00`, `#009E73`, `#F0E442`, `#56B4E9`, `#E69F00`, `#CC79A7`, `#000000`).

Avoid rainbow / jet for quantitative scales — perceptually non-uniform, hides high-frequency detail (Figure 5 in the paper makes this concrete), and hostile to colorblind viewers and greyscale printing. Avoid using too many similar colors — colorblindness or poor reproduction can collapse them. Reserve color for things that *need* it; if you have no specific reason for a hue, use grey or black.

*Practical move:* when the user provides no palette, default to seaborn `colorblind`. Mention colorblindness when proposing a palette, especially if the audience is general. When `style_infer` writes `info/style_guide.md`, record a categorical palette **and** a sequential and diverging choice — different plots in the project will need different ones.

### 7. Do not mislead the reader

The visual encoding should be honest. Watch out for two failure modes the paper highlights:

- **Implicit defaults that mislead.** Auto-rescaled bars or marker sizes that look correct because the title and axis labels are right, but where the perceived difference is wildly off the actual ratio (Figure 6 — top bars use *full* y-range, bottom use a narrow range; the data is identical, the visual story isn't).
- **Explicitly bad chart kinds.** Pie charts and 3-D bars to compare quantities — both are known to induce incorrect perception. Use the simplest plot type that delivers the message.

Other classics: linear scales unless log is justified, never truncate axes to exaggerate differences without saying so, areas/widths/radii that scale with the *value* (not its square root or square — circle radius vs disc area is a common bug, Figure 6 left).

*Practical move:* when truncating an axis, force-show zero or call it out in the caption. Avoid 3-D effects on 2-D data. If the user asks for something that's likely to mislead, gently flag it before drawing. Rougier et al. close Rule 7 with a sanity check that's worth offering to the user too: *"ask colleagues about their interpretation of your figures."*

### 8. Avoid chartjunk

Strip ink that doesn't carry information: heavy gridlines, shadowed bars, gradient fills, redundant legends, decorative borders. Tufte's "data-ink ratio" — maximize the ink that encodes data, minimize everything else. (Figure-7 in the companion repo contrasts a chartjunk-heavy plot with a clean one.)

*Defaults the skill uses:* spines off where they don't help, no panel backgrounds, light gridlines (or none on the axis where they don't aid reading), one tasteful legend.

### 9. Message trumps beauty

A beautiful figure that obscures the message is a failed figure. Conversely, a plain figure that lands the point clearly is a success — even if it's not what wins design awards. (The paper's Figure 8 makes the point with an xkcd-style hand-drawn "uncanny valley" curve — visually rough on purpose, but the message lands instantly.)

The paper also flags a related pitfall: when looking for inspiration, **don't copy figures from other papers** — image copyright matters, and "the frontiers between data visualization, information graphics, design, and art are becoming thinner and thinner". Use other figures as design inspiration, then build your own. The skill's **style_infer** subskill works this way: it reads a reference and *infers* a style guide, it doesn't reproduce the figure.

*Practical move:* before iterating on aesthetics, confirm the figure lands the message (Rule 2). Polish is the *last* pass, not the first.

### 10. Get the right tool

Match the tool to the job. The paper lists a useful starter set:

- **Matplotlib** — Python 2-D plots (with limited 3-D), huge gallery, the foundation of this skill's plot_gen.
- **R** — statistical computing + ggplot2 / lattice for highly extensible plotting.
- **Inkscape** — vector editor; great for hand-finishing a script-generated PDF/SVG.
- **TikZ / PGF** — programmatic graphics in TeX; high quality but high effort.
- **GIMP / ImageMagick** — bitmap editing / conversion.
- **D3.js** — interactive web visualizations (where the *interaction* is the point).
- **Cytoscape** / **Circos** — for network and genomic / circular relational data, where general plotters fall over.

You can always export data and finish in another tool. Don't fight a tool past its sweet spot.

*Defaults this skill uses:* matplotlib + seaborn for plot_gen, streamlit + altair for interactive. If the user asks for something matplotlib won't do well (linked-brushing, dense interactivity, non-tabular network/graph layouts), say so and suggest the better tool.

---

## How to use these guidelines in this skill

- When **plot_gen** runs and the user's request is ambiguous about audience or medium, ask one short question (Rule 1 / Rule 3) before generating.
- When **style_infer** writes `info/style_guide.md`, the palette / typography / axis-spine / legend / marker decisions should reflect Rules 5, 6, and 8 unless the reference figure deliberately departs from them.
- When the user asks for a chart kind that's prone to misleading (Rule 7) or piles on chartjunk (Rule 8), don't refuse — note the tradeoff and offer an alternative, then proceed with whatever the user chooses.
- When the user iterates ("make this prettier"), make sure the message still lands (Rule 9) before chasing polish.
- These rules belong in user-facing chat too: when the user asks "what's a good way to show X?", a one-line tie-back ("for ordered categories I'd use a sequential palette so the order is visible — see Rougier et al. 2014, Rule 6") is more useful than a generic recommendation.

Don't quote the paper at length; one-line tie-backs are enough.
