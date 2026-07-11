import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.ticker import ScalarFormatter

plt.rcParams["font.family"] = "serif"

df = pd.read_excel('Flex and non Flex.xlsx')

tech_colors = {
    "Nuclear": "#0000FF",
    "CCGTCCS": "#FF0000",
    "CCGT": "#8b0000",
    "H2CCGT": "#8000FF",
    "FC": "#FF00FF",
    "WindOn": "#00FF00",
    "Solar": "#FFFF00",
    "Battery_Dis": "#eedfcc",
    "Battery_Ch": "#00CED1"
}

pos_layers = [
    "Nuclear", "CCGTCCS", "CCGT",
    "H2CCGT", "FC", "WindOn",
    "Solar", "Battery_Dis"
]

neg_layers = ["Battery_Ch"]

scenarios = ["Without Flex", "With Flex"]

# -----------------------------
# محاسبه بازه مشترک محور Y
# -----------------------------
ymax = max(
    df[pos_layers].sum(axis=1).max(),
    df["Demand"].max()
)

ymin = min(
    0,
    df["Battery_Ch"].min()
)

# -----------------------------
# رسم نمودارها
# -----------------------------
fig, axes = plt.subplots(
    1, 2,
    figsize=(12, 6),
    sharex=False,
    sharey=False
)

for j, scenario in enumerate(scenarios):

    ax = axes[j]

    subset = (
        df[df["Scenario"] == scenario]
        .sort_values("Hour")
        .copy()
    )

    if subset.empty:
        ax.text(
            0.5, 0.5,
            "No Data",
            ha="center",
            va="center"
        )
        continue

    y_pos = [subset[tech] for tech in pos_layers]
    y_neg = [subset["Battery_Ch"]]

    # لایه منفی
    ax.stackplot(
        subset["Hour"],
        y_neg,
        colors=[tech_colors["Battery_Ch"]]
    )

    # لایه‌های مثبت
    ax.stackplot(
        subset["Hour"],
        y_pos,
        colors=[tech_colors.get(t, "gray") for t in pos_layers]
    )

    # تقاضا
    ax.plot(
        subset["Hour"],
        subset["Demand"],
        color="black",
        linewidth=2.5,
        label="Demand"
    )

    ax.set_title(scenario, fontsize=14)

    ax.set_ylabel(
        "Energy Dispatch (MWh)",
        fontsize=16
    )

    # محور X
    ax.set_xlim(1, 24)
    ax.set_xticks(range(1, 25,2))
    ax.xaxis.set_major_formatter(
        ScalarFormatter(useOffset=False)
    )

    ax.set_xlabel("Hour", fontsize=14)

    # محور Y یکسان برای هر دو نمودار
    ax.set_ylim(ymin * 1.05, ymax * 1.05)

    ax.grid(
        True,
        axis='y',
        linestyle='--',
        alpha=0.3
    )
fig.suptitle(
    "Energy dispatch in London on 17 February 2040, with and without flexibility of data centres",
    fontsize=16
)
# -----------------------------
# Legend
# -----------------------------
from matplotlib.lines import Line2D

handles = [
    plt.Rectangle((0, 0), 1, 1,
                  color=tech_colors[t])
    for t in pos_layers + neg_layers
]

# اضافه کردن Demand
handles.append(
    Line2D(
        [0], [0],
        color='black',
        linewidth=2.5
    )
)

labels = pos_layers + neg_layers + ["Demand"]

fig.legend(
    handles,
    labels,
    loc='upper center',
    bbox_to_anchor=(0.5, 0.05),
    ncol=14,
    fontsize=12,
    frameon=False
)
plt.tight_layout(rect=[0, 0.10, 1, 1])

plt.show()