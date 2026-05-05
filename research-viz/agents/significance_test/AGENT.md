# significance_test subskill

Run statistical significance tests on parsed data, store results as `.txt` tables in `visualizations/significance/`. Tests are produced **only when the user asks**; this subskill should never run unprompted, but it's often a useful next-step prompt after parsing or a comparative plot lands.

Read this together with `../../SKILL.md` for the top-level rules.

---

## When to run

Trigger phrases: "is this difference significant", "p-value", "t-test of X vs Y", "ANOVA across groups", "Mann-Whitney", "Kruskal-Wallis", "chi-square between …", "test for normality", "is X correlated with Y".

When *not* to run: never as a default companion to a plot. After a parser or comparative plot finishes, you can offer it ("Want me to add a t-test of recovery_time between treatment groups? I'd save the results to `significance/recovery_time-treatment-ttest.txt`."), but only run after the user accepts.

## Where it lives

```
visualizations/
└── significance/
    ├── <slug>.txt            (one human-readable test report per test, paired with…)
    ├── <slug>.json           (…machine-readable: test name, statistic, p-value, n, dof, effect size, etc.)
    └── README.md             (auto-generated index of every test in this folder)
```

The slug is short kebab-case describing the test: `recovery_time-treatment-ttest`, `species-bill_length-anova`, `gene_expression-condition-mannwhitney`. Mirror the conventions used for plot slugs.

If `significance/` doesn't exist yet, create it.

## What to write into each `<slug>.txt`

A short, paste-able report; keep it under ~30 lines. Format:

```
# recovery_time by treatment — Welch's t-test
# data: visualizations/intermediate_data/trial__parsed.csv
# generated: 2026-04-12 14:33

Groups
  treatment_A: n=87, mean=12.41, sd=3.22, median=12.0
  treatment_B: n=92, mean=14.08, sd=3.51, median=14.5

Test
  H0: mean(A) == mean(B)
  Welch's t-test (unequal variances)
  t = -3.21, df = 175.4, p = 0.0016
  95% CI for difference (A − B): [-2.71, -0.63]

Effect size
  Cohen's d = -0.49 (medium)

Notes
  - Shapiro-Wilk on each group: A p=0.21, B p=0.18 → normality OK at α=0.05.
  - Levene's test for equal variances: p=0.04 → unequal variances, Welch's used.
  - If you want non-parametric instead, ask for "mannwhitney recovery_time treatment".
```

The companion `<slug>.json` carries the same numbers in machine-readable form so a downstream tool (or `statannotations`-driven plot annotation, see plot_gen) can reuse them without parsing the txt.

## Test selection — defaults

Pick the appropriate test from the data shape and the user's framing. Common defaults:

- **Two groups, continuous outcome** → Welch's t-test (don't assume equal variances). Run Shapiro-Wilk per group; if normality fails, switch to Mann-Whitney U and note the swap.
- **3+ groups, continuous outcome** → one-way ANOVA + post-hoc Tukey HSD (or Games-Howell when variances differ). Switch to Kruskal-Wallis + Dunn for non-normal data.
- **Paired observations** → paired t-test (or Wilcoxon signed-rank).
- **Two categorical variables** → chi-square independence (Fisher's exact for sparse tables).
- **Two continuous variables, association** → Pearson r if both look roughly normal, Spearman ρ otherwise.
- **Repeated measures** → repeated-measures ANOVA or mixed-effects model (the latter via `statsmodels.formula.api.mixedlm`); flag the model spec to the user.

Always report:

- the test you actually ran (and *why*, if you swapped because of a normality / variance check),
- effect size (Cohen's d, η², r²) — p-values without effect sizes are misleading, especially with large n,
- group-level summary (n, mean/median, sd/IQR) so the user can sanity-check the data going in,
- whether you applied any multiple-comparison correction (Bonferroni / Holm / FDR) and what α threshold was used.

Be conservative with claims. Surface caveats in the "Notes" section: assumption checks, multiple-comparison concerns, "this test answers X but not Y."

## Tools

`scipy.stats` covers most defaults. `statsmodels` for ANOVA tables, mixed models, multiple-comparison corrections. `pingouin` is a nicer surface over both (one-call ANOVA + post-hoc + effect size) — prefer it when the env already has it.

If a test you need isn't in those packages (e.g. a permutation test for a niche statistic), fall back to writing the simulation explicitly — it's better than misapplying a built-in.

## Cross-link with plot_gen

When a plot exists for the same comparison (e.g. a violin plot of recovery_time per treatment), and the user wants the test's significance bracket *on* the plot, hand off to **plot_gen**: it uses `statannotations` to overlay the brackets / asterisks, reading the test results from this subskill's `.json`.

After a test is produced, offer the link explicitly: "Result is in `significance/recovery_time-treatment-ttest.txt`. Want me to overlay the bracket on the matching violin plot?"

## Updating the index

After writing a test, regenerate `significance/README.md` as a small index:

```
# Significance tests in this project

| slug | test | data | p | effect size |
|---|---|---|---|---|
| recovery_time-treatment-ttest | Welch's t | trial__parsed.csv | 0.0016 | d=-0.49 |
| species-bill_length-anova     | one-way ANOVA + Tukey | flowers__parsed.csv | <0.001 | η²=0.41 |
```

Keeps the folder browsable at a glance.

## Closing the loop

Append a one-liner to `info/context.md`: which test, which data, the slug, and the p / effect-size headline. The full numbers stay in `significance/<slug>.txt` — don't duplicate them into `context.md`.
