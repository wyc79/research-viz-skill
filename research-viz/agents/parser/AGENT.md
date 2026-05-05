# parser subskill

Read raw tabular files from a read-only `data/` directory, run quality checks, handle missing data, and write `<dataset>__parsed.csv` outputs into `intermediate_data/`.

Use this subskill when the user says "parse / clean / load / read this", or when any other subskill is requested but `intermediate_data/` is empty.

This file documents the project-time behavior — read it together with the top-level rules in `../../SKILL.md` (data/ read-only, naming convention, bake-in & trim & comment).

---

## What the script does

The bundled `assets/scaffolding/scripts/parser.py` is a working starting point. Adapt — don't rewrite from scratch — for the specific dataset.

- Auto-detects file format by extension (`.csv`, `.tsv`, `.txt` with sniffed delimiter, `.xlsx`/`.xls`).
- Runs three quality checks and writes a short report to stdout: per-column dtype consistency (does any cell deviate from the column's modal type?), missing-value counts, and obvious format anomalies (mixed date formats, stray strings in numeric columns).
- Missing-data handling is **interactive by default**. The script prints the missing-value summary, then asks the user per column (or globally) which strategy to apply: `ignore` (leave NaN), `drop_row`, `drop_col`, `mean`, `median`, `mode`, `ffill`, `bfill`, `constant:<value>`, or `custom` (the user supplies a small Python expression).
- For a non-interactive run, the script accepts `--strategy '{"col_a":"mean","col_b":"drop_row"}'` as JSON, layered on top of the project-baked-in defaults.

## Output layout (controlled by `--combine`)

- **Single input file**: writes `intermediate_data/<dataset>__parsed.csv` plus `<dataset>__parsed.meta.json`, where `<dataset>` is the source file's stem.
- **Multiple input files** with the default `--combine per_file` (recommended for research data where each file is a session / patient / client / run and should *not* be aggregated): the parser writes one `<dataset>__parsed.csv` per input file. By default it **mirrors the `data/` directory structure inside `intermediate_data/`**; if `data/` is laid out poorly, pick a cleaner layout for `intermediate_data/` and encode it in `project_reorganize()`. There is **no** combined CSV in per-file mode — that's deliberate, to avoid pretending sessions are interchangeable.
- `--combine concat`: stack all inputs into `intermediate_data/combined__parsed.csv` with a `__source__` column tagging each row's origin.
- `--combine both`: write per-file outputs *and* `combined__parsed.csv`.

A `parsed_index.json` is **always** written, listing every per-file output (with row counts, dtypes, strategies applied), the canonical CSV downstream tools should default to, and whether a combined CSV exists.

**Subsequent transforms** (reshape, imputation pass, normalization, filtering, etc.) write *new* files alongside the parsed outputs using the suffix convention (`<dataset>__long.csv`, `<dataset>__imputated.csv`, `<dataset>__zscored.csv`, …) and are appended to `parsed_index.json`. **Never overwrite `__parsed.csv`** — keep each transform stage as its own file so the lineage is inspectable. The extension stays CSV for the standard tabular parser; **domain_viz** may write non-CSV intermediates (`.fif`, `.nii.gz`, `.h5ad`, …) following the same `<dataset>__<stage>.<ext>` pattern — see `agents/domain_viz/AGENT.md` and the SKILL.md naming-convention section.

## What to bake in (project-time)

Once the user has agreed on cleaning rules, write them into the anchors at the top of `parser.py`:

- `PROJECT_STRATEGIES` — per-column missing-data strategies (used as the default for `--strategy`).
- `PROJECT_NONINTERACTIVE_DEFAULT` — set to `True` so `bash parse_input.sh` runs unattended.
- `apply_project_specific_cleaning(df, source_path)` — custom dtype coercions, datetime parsing, drop-row rules, column renames, sentinel replacements.
- `project_reorganize(source_relative)` — layout mapping when `data/` is awkward and `intermediate_data/` should look different.

The end-state: `bash parse_input.sh` (zero arguments) reproduces the cleaned outputs the user just approved, without re-prompting.

After parsing once successfully, append the strategies and any data quirks to `info/context.md`.

**If the user is running on pilot data**, note that in `context.md` (e.g. "parser ran against `pilot_data/` — 12 of 240 sessions"). Then surface a next-step prompt after the matching plot or dashboard finishes: "Pilot looks good. Want me to re-run on the full dataset? `DATA_DIR=$(pwd)/data bash visualizations/parse_input.sh` will reuse the same `PROJECT_STRATEGIES` you just baked in." Don't switch to full data unprompted — the user might want to iterate on the pilot first.

## Trim before delivering

Per the SKILL.md trim rule: delete unused branches in `apply_strategy()`, the multi-file `--combine` plumbing if the project is single-file, and any imports that fall out. Keep concise comments on the surviving steps.

## Reference

For the menu of missing-data strategies and the rationale behind each, see `../../references/missing-data-strategies.md`.
