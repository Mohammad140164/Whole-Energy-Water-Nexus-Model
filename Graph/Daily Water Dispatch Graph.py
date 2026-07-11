
import pandas as pd
import matplotlib.pyplot as plt

plt.rcParams["font.family"] = "serif"

# Load data
df = pd.read_excel('Water Dispatch.xlsx')


# Colors
tech_colors = {
    "Nuclear": "#0000FF",
    "CCGTCCS": "#FF0000",
    "CCGT": "#8b0000",
    "Biomass": "#FF8C00",
    "BECCS": "#FF0080",
    "H2CCGT": "#8000FF",
    "SMRCCS": "#6c7b8b",
    "ATRCCS": "#9fb6cd",
    "BGCCS": "#96cdcd",
    "WE": "#afeeee"
}


# Stack order
pos_layers = [
    "Nuclear",
    "CCGTCCS",
    "CCGT",
    "Biomass",
    "BECCS",
    "H2CCGT",
    "SMRCCS",
    "ATRCCS",
    "BGCCS",
    "WE"
]


scenarios = [
    "Without DC",
    "Air-Cooled",
    "Water-Cooled",
    "D2C Cooling"
]

seasons = [
    "Winter",
    "Summer"
]


# Create figure
# Create figure
fig, axes = plt.subplots(
    2,
    4,
    figsize=(16,10),
    sharex=False,
    sharey='row' # تنظیم مقیاس یکسان برای هر ردیف به صورت جداگانه
)

for i, season in enumerate(seasons):
    for j, scenario in enumerate(scenarios):
        ax = axes[i,j]

        # Filter data
        subset = df[
            (df["Season"] == season) &
            (df["Scenario"] == scenario)
        ].sort_values("Hour")

        if subset.empty:
            ax.text(0.5, 0.5, "No Data", ha="center", va="center", fontsize=14)
            ax.set_title(f"{scenario} - {season}")
            continue

        bottom = None
        for tech in pos_layers:
            if tech in subset.columns:
                values = subset[tech].fillna(0)
                ax.bar(
                    subset["Hour"],
                    values,
                    bottom=bottom,
                    label=tech,
                    color=tech_colors[tech],
                    width=0.8
                )
                if bottom is None:
                    bottom = values.copy()
                else:
                    bottom += values

        # اعمال شرط برای سقف محور Y
        if i == 0:
            ax.set_ylim(0, 1e9)
        
        # Formatting
        ax.set_title(f"{scenario} - {season}", fontsize=12)
        ax.grid(True, axis="y", linestyle="--", alpha=0.3)
        
        if j == 0:
            ax.set_ylabel("Water Consumption (Litter)", fontsize=15)
        if i == 1:
            ax.set_xlabel("Hour")
        ax.tick_params(axis='x', rotation=90)



# Legend
handles = [
    plt.Rectangle(
        (0,0),
        1,
        1,
        color=tech_colors[t]
    )
    for t in pos_layers
]


fig.legend(
    handles,
    pos_layers,
    loc="lower center",
    bbox_to_anchor=(0.5, -0.00),
    ncol=10,
    fontsize=11,
    frameon=False
)


plt.tight_layout(
    rect=[0,0.05,1,1]
)

plt.show()