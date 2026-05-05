# Visualizations Context

Workspace context for the flowers (iris-like) dataset visualizations.

## Dataset

- Source: `data/flowers.csv`
- Rows: 150 (50 per species)
- Columns: `species`, `sepal_length`, `sepal_width`, `petal_length`, `petal_width`
- Species: `setosa`, `versicolor`, `virginica`
- All measurements are in centimeters. Data is already clean (one minor anomaly: a single negative `petal_width` value of -0.02 in `setosa`, treated as measurement noise; no cleaning applied per task spec).

### Per-species summary (mean +/- std)

| species    | sepal_length | sepal_width | petal_length | petal_width |
|------------|--------------|-------------|--------------|-------------|
| setosa     | 5.06 +/- 0.46 | (see data) | (see data)   | 0.25 +/- 0.12 |
| versicolor | 5.89 +/- 0.44 | (see data) | (see data)   | 1.26 +/- 0.22 |
| virginica  | 6.75 +/- 0.63 | (see data) | (see data)   | 1.93 +/- 0.29 |

## Workspace layout

```
outputs/
  data/
    flowers.csv
  visualizations/
    CONTEXT.md                  <- this file
    petal_scatter.png           <- plot 1
    sepal_length_violin.png     <- plot 2
    scripts/
      plot_petal_scatter.py
      plot_sepal_violin.py
  SUMMARY.txt
```

## Plots

### 1. `petal_scatter.png`
- Type: scatter
- x: `petal_length`, y: `petal_width`
- Color: `species` (seaborn `deep` palette)
- Script: `visualizations/scripts/plot_petal_scatter.py`
- Notes: setosa forms a tight cluster at low petal dimensions; versicolor and virginica are roughly linearly separable along the petal axes.

### 2. `sepal_length_violin.png`
- Type: violin (one violin per species, with inner box)
- x: `species`, y: `sepal_length`
- Script: `visualizations/scripts/plot_sepal_violin.py`
- Notes: clear ordering setosa < versicolor < virginica in median sepal length; virginica has the widest spread.

## Conventions

- Theme: `seaborn` `whitegrid` style, `talk` context.
- Palette: seaborn `deep` for species (consistent across plots).
- Output format: PNG @ 150 dpi, `bbox_inches="tight"`.
- Each plot lives in its own self-contained script under `visualizations/scripts/` and writes its PNG to `visualizations/`.
- Re-run any plot with `python3 visualizations/scripts/<name>.py` from the `outputs/` directory.

## Reproduce

```bash
cd outputs
python3 visualizations/scripts/plot_petal_scatter.py
python3 visualizations/scripts/plot_sepal_violin.py
```
