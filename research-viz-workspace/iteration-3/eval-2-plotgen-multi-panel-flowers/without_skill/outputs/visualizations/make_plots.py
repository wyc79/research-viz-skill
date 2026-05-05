"""Generate flowers visualizations.

Plots:
1. Scatter of petal_length vs petal_width colored by species.
2. Violin plot of sepal_length per species.
"""

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

HERE = Path(__file__).resolve().parent
DATA_PATH = HERE.parent / "data" / "flowers.csv"
OUT_DIR = HERE


def main() -> None:
    df = pd.read_csv(DATA_PATH)
    sns.set_theme(style="whitegrid", context="talk")

    # 1) Scatter: petal_length vs petal_width by species
    fig, ax = plt.subplots(figsize=(8, 6))
    sns.scatterplot(
        data=df,
        x="petal_length",
        y="petal_width",
        hue="species",
        palette="deep",
        s=70,
        edgecolor="white",
        ax=ax,
    )
    ax.set_title("Petal length vs petal width by species")
    ax.set_xlabel("Petal length (cm)")
    ax.set_ylabel("Petal width (cm)")
    ax.legend(title="Species", loc="best")
    fig.tight_layout()
    fig.savefig(OUT_DIR / "scatter_petal_length_vs_width.png", dpi=150)
    plt.close(fig)

    # 2) Violin: sepal_length per species
    fig, ax = plt.subplots(figsize=(8, 6))
    sns.violinplot(
        data=df,
        x="species",
        y="sepal_length",
        hue="species",
        palette="deep",
        inner="box",
        legend=False,
        ax=ax,
    )
    ax.set_title("Sepal length distribution by species")
    ax.set_xlabel("Species")
    ax.set_ylabel("Sepal length (cm)")
    fig.tight_layout()
    fig.savefig(OUT_DIR / "violin_sepal_length.png", dpi=150)
    plt.close(fig)


if __name__ == "__main__":
    main()
