"""Violin plot of sepal_length per species."""
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data" / "flowers.csv"
OUT = ROOT / "visualizations" / "sepal_length_violin.png"

df = pd.read_csv(DATA)

sns.set_theme(style="whitegrid", context="talk")
fig, ax = plt.subplots(figsize=(9, 6))
sns.violinplot(
    data=df,
    x="species",
    y="sepal_length",
    hue="species",
    palette="deep",
    inner="box",
    cut=0,
    legend=False,
    ax=ax,
)
ax.set_title("Sepal length distribution by species")
ax.set_xlabel("Species")
ax.set_ylabel("Sepal length (cm)")

fig.tight_layout()
fig.savefig(OUT, dpi=150, bbox_inches="tight")
print(f"Wrote {OUT}")
