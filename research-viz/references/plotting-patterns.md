# Plotting patterns (matplotlib + seaborn)

Recipes for plots that come up repeatedly in research contexts. The bundled `plot_gen.py` handles a small grammar (scatter/violin/box/hist/line/heatmap); for anything richer, write a small custom function inside (or alongside) `plot_gen.py` and call `set_research_theme()` from `helpers.utils` at the top.

## Theme defaults

`helpers.utils.set_research_theme()` sets:

- seaborn `"paper"` context, `"whitegrid"` style, `"colorblind"` palette
- 300dpi savefig
- Top/right spines off
- Legend frames off

This is a sensible starting point for figures intended for papers or slides. Override per-figure as needed.

## Faceted small multiples

```python
g = sns.relplot(
    data=df, x="x", y="y",
    hue="condition", col="experiment", row="cohort",
    kind="scatter", height=3, aspect=1.1, alpha=0.8, s=18,
)
g.set_axis_labels("X (units)", "Y (units)")
g.set_titles("{col_name} | {row_name}")
g.tight_layout()
g.savefig(out_dir / "figure.png", dpi=300, bbox_inches="tight")
```

## Log-scale with proper minor ticks

```python
ax.set_yscale("log")
ax.yaxis.set_major_formatter(plt.LogFormatterSciNotation())
ax.grid(True, which="both", linewidth=0.4, alpha=0.5)
```

## Error bars with seaborn

`sns.lineplot` + `errorbar=("ci", 95)` gives a translucent CI ribbon; use `errorbar="sd"` for ±1σ ribbons or `errorbar=("se", 1)` for SEM.

## Heatmap with cluster ordering

```python
import scipy.cluster.hierarchy as sch
order = sch.leaves_list(sch.linkage(df.corr().abs(), method="average"))
sns.heatmap(df.corr().iloc[order, order], cmap="vlag", center=0, annot=True, fmt=".2f")
```

## Categorical strip + box overlay

Useful for showing both raw points and summary stats on the same axes.

```python
sns.boxplot(data=df, x="group", y="value", showfliers=False, color="lightgray")
sns.stripplot(data=df, x="group", y="value", color="black", size=2.5, alpha=0.6)
```

## Saving

Always save both PNG (300dpi) and PDF; PDFs render crisp in LaTeX and editors. Save the underlying tidy dataset as `data.csv` next to the figure so the plot is reproducible from the workspace alone.

## Colors

- `palette="colorblind"` (default) is good for most cases.
- For diverging encodings (correlations, signed effects), use `cmap="vlag"` or `cmap="coolwarm"` and explicitly center at zero with `center=0`.
- For ordered/sequential encodings (e.g. dose, time), use `cmap="viridis"` or `cmap="rocket"`.
- Avoid `jet` and `rainbow`.

## Slug naming

Subfolder names under `plots/` are derived from the user's prompt via `slugify()`. Keep them short and meaningful — something a future reader would recognize. If the auto-slug is gibberish, pass `--slug myname`.

## When you need something this script doesn't do

Write the plot logic inline as you would normally — `pd.read_csv(parsed_csv)`, build the figure, `fig.savefig(out_dir / "figure.png", dpi=300, bbox_inches="tight")`. Don't try to shoehorn an unusual chart into the simple grammar in `plot_gen.py`.
