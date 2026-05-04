# Missing-data strategies

Quick reference for choosing a strategy per column. The bundled `parser.py` supports all of these out of the box; pass them via `--strategy '{"col":"<strategy>"}'` or pick interactively.

| Strategy | What it does | Use when | Avoid when |
|---|---|---|---|
| `ignore` | Leave NaN in place | Downstream tools (e.g. seaborn, statsmodels) handle NaN themselves; you want to preserve missingness as signal | A downstream step would silently coerce NaN to 0 or fail |
| `drop_row` | Remove rows where this column is NaN | Missing in this column makes the row meaningless (e.g. the row's primary key) | Doing this on multiple columns would dramatically shrink the dataset |
| `drop_col` | Remove the entire column | The column is mostly empty (>50%) and not load-bearing | Even sparse columns sometimes carry the only signal you have |
| `mean` | Fill NaN with column mean | Numeric, roughly symmetric distribution, missing-at-random | The column is skewed, or missingness is informative (MNAR) |
| `median` | Fill NaN with column median | Numeric, skewed or has outliers — the safer default than mean | Column is categorical or you need a "smart" group-wise fill |
| `mode` | Fill NaN with the most common value | Categorical or low-cardinality columns | Continuous numeric columns (rarely meaningful) |
| `ffill` | Forward-fill from the previous row | Time-series-like data where missing values reasonably copy the prior observation | Rows are not in any meaningful order |
| `bfill` | Backward-fill from the next row | Same as ffill but the *next* observation is the right reference (rare) | — |
| `constant:<v>` | Fill NaN with `<v>` (parsed as int/float if possible, else string) | Domain-specific sentinel ("Unknown", `-1`, `0`) makes more sense than statistical imputation | Numeric column where 0 has actual meaning (then pick a different sentinel) |

## Common pitfalls

- **Imputing the target.** Never apply mean/median imputation to your *outcome* column when training a model — it leaks information and biases results. Drop those rows or model the missingness directly.
- **Mixing imputation with leakage.** If you'll later do train/test splits, compute the mean/median on the training fold only. The bundled `parser.py` doesn't know about your split — handle this in modeling, not in parsing.
- **Hidden missing values.** Many real datasets encode missing as `"N/A"`, `"-"`, `"NA"`, `"."`, `"--"`, `"unknown"`, or even `-9999`/`-1`. Run `df[col].value_counts(dropna=False).head(20)` to spot these, and either replace them with `np.nan` before strategy application or convert via `pd.read_csv(..., na_values=[...])`.
- **Strategy-per-group.** Sometimes the right fill is "median *within group*". Implement that with `df.groupby(key)[col].transform(lambda s: s.fillna(s.median()))` rather than a global median; the bundled parser doesn't do this — extend it for the dataset.
- **Time series.** `ffill`/`bfill` only make sense if the rows are sorted by time. Sort first.

## When the user says "use whatever you think is best"

Default policy:
1. If `pct_missing < 5%` and the column is numeric → `median`.
2. If `pct_missing < 5%` and categorical → `mode`.
3. If `pct_missing` is between 5% and 30%, surface it to the user with a recommendation; don't decide silently.
4. If `pct_missing > 50%` → recommend `drop_col` and ask.

Always log what you did to `info/context.md` so the user (and future agents) can see why the cleaned data looks the way it does.
