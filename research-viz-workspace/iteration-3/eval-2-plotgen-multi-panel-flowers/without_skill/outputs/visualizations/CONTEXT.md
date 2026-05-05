# Visualizations Workspace

Context for the flowers dataset visualizations.

## Layout

```
outputs/
  data/
    flowers.csv                 # source data (clean)
  visualizations/
    make_plots.py               # script that produces both plots
    scatter_petal_length_vs_width.png
    violin_sepal_length.png
    CONTEXT.md                  # this file
```

## Dataset

`data/flowers.csv` has 150 rows and 5 columns:

- `species` (categorical): setosa, versicolor, virginica
- `sepal_length` (cm)
- `sepal_width` (cm)
- `petal_length` (cm)
- `petal_width` (cm)

## Plots produced

1. `scatter_petal_length_vs_width.png` — scatter plot of `petal_length`
   vs `petal_width`, points colored by `species`. Shows the strong
   per-species clustering in petal dimensions.
2. `violin_sepal_length.png` — violin plot of `sepal_length`
   distributions per species, with inner box summary.

## How to regenerate

```
cd visualizations
python3 make_plots.py
```

Dependencies: `pandas`, `matplotlib`, `seaborn`. Theming uses
`seaborn` `whitegrid` style with the `deep` palette; figures saved at
150 DPI.
