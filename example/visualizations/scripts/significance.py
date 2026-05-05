#!/usr/bin/env python3
"""
significance.py — run the Welch's t-test that this project keeps under
`significance/`.

The single test we ship: body_mass_g compared between Adelie and Gentoo
penguins (the two species whose body masses are visibly the most different
in the violin plot). Welch's is used because we don't want to assume equal
variances — see Notes in the .txt report for the assumption checks (Shapiro,
Levene) and the rationale.

Outputs (per the significance_test subskill convention):
  - significance/<slug>.txt   — paste-able human-readable report (~30 lines)
  - significance/<slug>.json  — machine-readable summary, used by plot_gen's
                                violin-with-ttest recipe to draw the bracket.
  - significance/README.md    — auto-generated index of every test in the folder.
"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats


# ---- Project-baked-in test config -------------------------------------------
TEST_SLUG = "body_mass_g-adelie-vs-gentoo-ttest"
TEST_TITLE = "body_mass_g by species — Welch's t-test (Adelie vs Gentoo)"
GROUP_COL = "species"
OUTCOME_COL = "body_mass_g"
GROUP_A = "Adelie"
GROUP_B = "Gentoo"
ALPHA = 0.05


def cohens_d(a: np.ndarray, b: np.ndarray) -> float:
    """Pooled-SD Cohen's d. Sign convention: positive when A > B."""
    na, nb = len(a), len(b)
    var_a, var_b = a.var(ddof=1), b.var(ddof=1)
    pooled = np.sqrt(((na - 1) * var_a + (nb - 1) * var_b) / (na + nb - 2))
    return float((a.mean() - b.mean()) / pooled)


def main() -> int:
    here = Path(__file__).resolve()
    viz_dir = here.parent.parent
    parsed = viz_dir / "intermediate_data" / "penguins__parsed.csv"
    if not parsed.exists():
        raise SystemExit(f"missing {parsed} — run parse_input.sh first")

    df = pd.read_csv(parsed)
    a = df.loc[df[GROUP_COL] == GROUP_A, OUTCOME_COL].dropna().to_numpy()
    b = df.loc[df[GROUP_COL] == GROUP_B, OUTCOME_COL].dropna().to_numpy()
    if len(a) < 3 or len(b) < 3:
        raise SystemExit(f"need ≥3 obs per group; got n_A={len(a)}, n_B={len(b)}")

    # Assumption checks: report only — we use Welch's regardless.
    sw_a = stats.shapiro(a)
    sw_b = stats.shapiro(b)
    levene = stats.levene(a, b, center="median")  # robust Brown–Forsythe variant

    # Welch's two-sample t-test (equal_var=False) + 95% CI for the mean
    # difference using the Welch–Satterthwaite df. scipy returns the t and p;
    # we compute the CI by hand.
    t_res = stats.ttest_ind(a, b, equal_var=False)
    se = np.sqrt(a.var(ddof=1) / len(a) + b.var(ddof=1) / len(b))
    diff = a.mean() - b.mean()
    df_w = (a.var(ddof=1) / len(a) + b.var(ddof=1) / len(b)) ** 2 / (
        (a.var(ddof=1) / len(a)) ** 2 / (len(a) - 1)
        + (b.var(ddof=1) / len(b)) ** 2 / (len(b) - 1)
    )
    tcrit = stats.t.ppf(1 - ALPHA / 2, df_w)
    ci_lo, ci_hi = diff - tcrit * se, diff + tcrit * se

    d = cohens_d(a, b)
    d_label = "small" if abs(d) < 0.5 else ("medium" if abs(d) < 0.8 else "large")

    sig_dir = viz_dir / "significance"
    sig_dir.mkdir(parents=True, exist_ok=True)

    # ---- .txt report (paste-able) -------------------------------------------
    lines = [
        f"# {TEST_TITLE}",
        f"# data: {parsed.relative_to(viz_dir.parent)}",
        f"# generated: {datetime.now().isoformat(timespec='seconds')}",
        "",
        "Groups",
        f"  {GROUP_A}: n={len(a)}, mean={a.mean():.1f}, sd={a.std(ddof=1):.1f}, median={np.median(a):.1f}",
        f"  {GROUP_B}: n={len(b)}, mean={b.mean():.1f}, sd={b.std(ddof=1):.1f}, median={np.median(b):.1f}",
        "",
        "Test",
        f"  H0: mean({GROUP_A}) == mean({GROUP_B})",
        "  Welch's t-test (unequal variances)",
        f"  t = {t_res.statistic:.3f}, df = {df_w:.1f}, p = {t_res.pvalue:.3g}",
        f"  95% CI for difference ({GROUP_A} − {GROUP_B}): [{ci_lo:.1f}, {ci_hi:.1f}] g",
        "",
        "Effect size",
        f"  Cohen's d = {d:.2f} ({d_label})",
        "",
        "Notes",
        f"  - Shapiro-Wilk on each group: {GROUP_A} p={sw_a.pvalue:.3g}, {GROUP_B} p={sw_b.pvalue:.3g}.",
        f"    Normality {'holds' if min(sw_a.pvalue, sw_b.pvalue) >= ALPHA else 'fails'} at α={ALPHA};",
        f"    if you'd rather not assume normality, ask for `mannwhitney {OUTCOME_COL} {GROUP_COL}`.",
        f"  - Levene's test for equal variances (Brown–Forsythe): p={levene.pvalue:.3g} →",
        f"    {'unequal' if levene.pvalue < ALPHA else 'equal'} variances; Welch's is robust to either.",
        "  - No multiple-comparison correction applied — this is a single planned contrast.",
    ]
    txt_path = sig_dir / f"{TEST_SLUG}.txt"
    txt_path.write_text("\n".join(lines) + "\n")

    # ---- .json (machine-readable; consumed by plot_gen's annotated violin) ---
    json_path = sig_dir / f"{TEST_SLUG}.json"
    json_payload = {
        "slug": TEST_SLUG,
        "title": TEST_TITLE,
        "test": "welch_t",
        "group_col": GROUP_COL,
        "outcome_col": OUTCOME_COL,
        "groups": [
            {"name": GROUP_A, "n": int(len(a)), "mean": float(a.mean()), "sd": float(a.std(ddof=1)), "median": float(np.median(a))},
            {"name": GROUP_B, "n": int(len(b)), "mean": float(b.mean()), "sd": float(b.std(ddof=1)), "median": float(np.median(b))},
        ],
        "statistic": float(t_res.statistic),
        "df": float(df_w),
        "p_value": float(t_res.pvalue),
        "mean_diff": float(diff),
        "ci_low": float(ci_lo),
        "ci_high": float(ci_hi),
        "alpha": ALPHA,
        "effect_size": {"name": "cohens_d", "value": float(d), "magnitude": d_label},
        "assumption_checks": {
            "shapiro_wilk": {GROUP_A: float(sw_a.pvalue), GROUP_B: float(sw_b.pvalue)},
            "levene_brown_forsythe": float(levene.pvalue),
        },
    }
    json_path.write_text(json.dumps(json_payload, indent=2))

    # ---- README index --------------------------------------------------------
    index_path = sig_dir / "README.md"
    index_path.write_text(
        "# Significance tests in this project\n\n"
        "| slug | test | data | p | effect size |\n"
        "|---|---|---|---|---|\n"
        f"| {TEST_SLUG} | Welch's t | penguins__parsed.csv | {t_res.pvalue:.3g} | d={d:.2f} |\n"
    )

    print(f"wrote {txt_path}")
    print(f"wrote {json_path}")
    print(f"wrote {index_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
