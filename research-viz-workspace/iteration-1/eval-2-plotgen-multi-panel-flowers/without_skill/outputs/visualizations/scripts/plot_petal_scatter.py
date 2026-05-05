"""Scatter: petal_length vs petal_width, colored by species."""
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data" / "flowers.csv"
OUT = ROOT / "visualizations" / "petal_scatter.png"

df = pd.read_csv(DATA)

sns.set_theme(style="whitegrid", context="talk")
fig, ax = plt.subplots(figsize=(9, 6))
sns.scatterplot(
    data=df,
    x="petal_length",
    y="petal_width",
    hue="species",
    palette="deep",
    s=70,
    edgecolor="white",
    linewidth=0.5,
    alpha=0.9,
    ax=ax,
)
ax.set_title("Petal length vs petal width by species")
ax.set_xlabel("Petal length (cm)")
ax.set_ylabel("Petal width (cm)")
ax.legend(title="Species", frameon=True)

fig.tight_layout()
fig.savefig(OUT, dpi=150, bbox_inches="tight")
print(f"Wrote {OUT}")
