import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Patch

plt.rcParams.update({
    "font.family": "serif",
    "font.size": 11,
    "mathtext.default": "regular"
})
# ======================================================
# COLORS (TECHNOLOGIES ONLY)
# ======================================================

tech_colors = {
    "Solar": "#FFFF00",
    "Wind Onshore": "#00FF00",
    "Wind Offshore": "#228b22",
    "Battery": "#00FFFF",
    "CCGT": "#8b0000",
    "Nuclear": "#0000FF",
    "H2CCGT": "#8000FF",
    "FC": "#FF00FF",
    "BECCS": "#FF0080",
    "CCGTCCS": "#FF0000",
    "Biomass": "#ffa54f",
    "SMRCCS": "#6c7b8b",
    "ATRCCS": "#9fb6cd",
    "BGCCS": "#96cdcd",
    "WE": "#afeeee",
    "HyBoiler": "#8b5a00",
    "ASHP": "#cd8500",
    "CCGT": "#5d4037"
}

# ======================================================
# DATA (CLEAN STRUCTURE)
# ======================================================

water_electricity = {
    "Air-Cooled": {
        "Nuclear": 128,
        "CCGT": -1.7,
        "CCGTCCS": 23,
        "H2CCGT": 1,
        "BECCS": 0.5,
    },
    "Water-Cooled": {
        "Nuclear": 131,
        "CCGT": -1.5,
        "CCGTCCS": 21,
        "H2CCGT": 0,
        "BECCS": 1,
    },
    "Direct-to-Chip": {
        "Nuclear": 120,
        "CCGT": 0,
        "CCGTCCS": 20,
        "H2CCGT": 0,
        "BECCS": 0,
    }
}

water_hydrogen = {
    "Air-Cooled": {
        "SMRCCS": -3,
        "ATRCCS": 53,
        "BGCCS": -2,
        "WE": -5
    },
    "Water-Cooled": {
        "SMRCCS": 7,
        "ATRCCS": 36,
        "BGCCS": 4,
        "WE": 0
    },
    "Direct-to-Chip": {
        "SMRCCS": -3,
        "ATRCCS": 51,
        "BGCCS": 1,
        "WE": 1
    }
}

# ✔ FIXED: scalar values instead of invalid set
water_d2dc = {
    "Air-Cooled": 0.03,
    "Water-Cooled": 2.5,
    "Direct-to-Chip": 0.0
}

energy_electricity = {
    "Air-Cooled": {
        "Solar": 8,
        "Wind Onshore": 3,
        "Wind Offshore": 18,
        "Nuclear": 42,
        "H2CCGT": 1,
        "FC": 1.1,
        "BECCS": 0,
        "CCGT": -2,
        "CCGTCCS": 24
    },
    "Water-Cooled": {"Solar": 4.6,
    "Wind Onshore": 3,
    "Wind Offshore": 22,
    "Nuclear": 42,
    "H2CCGT": 1,
    "FC": 0,
    "BECCS": 1.5,
    "CCGT": -1,
    "CCGTCCS": 26},
    
    
    "Direct-to-Chip": {"Solar": 0,
    "Wind Onshore": 3,
    "Wind Offshore": 16,
    "Nuclear": 42,
    "H2CCGT": 0,
    "FC": 0,
    "BECCS": 0,
    "CCGT": -1,
    "CCGTCCS": 18}
}

energy_hydrogen = {
    "Air-Cooled": {
        "ATRCCS": 39,
        "SMRCCS": -2,
        "BGCCS": -3,
        "WE": -1
    },
    "Water-Cooled": {
    "ATRCCS": 27,
    "SMRCCS": 5,
    "BGCCS": -5,
    "WE": 0},
    "Direct-to-Chip": {
    "ATRCCS": 38,
    "SMRCCS": -2,
    "BGCCS": 2,
    "WE": -1}
}

energy_heating = {
    "Air-Cooled": {
        "ASHP": -19,
        "HyBoiler": 28
    },
    "Water-Cooled": {
    "ASHP": -14,
    "HyBoiler": 22},
    "Direct-to-Chip": {
    "ASHP": -24,
    "HyBoiler": 33}
}

# ======================================================
# PLOT FUNCTION (STACKED OR SIMPLE SAFE)
# ======================================================

def plot_sector(ax, data, title, is_scalar=False):

    x = np.arange(len(data))
    width = 0.35

    for i, (_, values) in enumerate(data.items()):

        # -------------------------
        # CASE 1: scalar subplot (D2C)
        # -------------------------
        if is_scalar:
            ax.bar(x[i], values, width, color="#1e90ff", edgecolor="black")
            continue

        # -------------------------
        # CASE 2: stacked subplot
        # -------------------------
        techs = values

        pos_base = 0
        neg_base = 0

        if len(techs) == 0:
            ax.bar(x[i], 0, width, color="lightgray", edgecolor="black")
            continue

        for tech, value in techs.items():

            color = tech_colors.get(tech, "gray")

            if value >= 0:
                ax.bar(x[i], value, width,
                       bottom=pos_base,
                       color=color,
                       edgecolor="black",
                       linewidth=0.8)
                pos_base += value
            else:
                ax.bar(x[i], value, width,
                       bottom=neg_base,
                       color=color,
                       edgecolor="black",
                       linewidth=0.8)
                neg_base += value

    ax.set_xticks(x)
    ax.set_xticklabels(list(data.keys()))
    ax.axhline(0, color="black", linewidth=1)
    ax.set_title(title)
    ax.margins(x=0.12)

# ======================================================
# FIGURE
# ======================================================

fig, axes = plt.subplots(2, 3, figsize=(18, 11))

# ---------------- TOP ----------------
plot_sector(axes[0,0], water_electricity, "Electricity Sector")
plot_sector(axes[0,1], water_hydrogen, "Hydrogen Sector")

# ✔ scalar plot (FIXED)
plot_sector(axes[0,2], water_d2dc, "Direct Water to Data Centre", is_scalar=True)

# ---------------- BOTTOM ----------------
plot_sector(axes[1,0], energy_electricity, "Electricity Sector")
plot_sector(axes[1,1], energy_hydrogen, "Hydrogen Sector")
plot_sector(axes[1,2], energy_heating, "Heating Sector")

# ---------------- LABELS ----------------
axes[0,0].set_ylabel("Deviation in Water Consumption ($10^9$ litres)", fontweight='bold')
axes[0,1].set_ylabel("Deviation in Water Consumption ($10^9$ litres)", fontweight='bold')

axes[0,2].set_ylabel("Total Data Centre Water Consumption ($10^9$ litres)", fontweight='bold')

for ax in axes[1,:]:
    ax.set_ylabel("Deviation in Energy Generation (TWh)", fontweight='bold')

# ======================================================
# SEPARATED LEGENDS
# ======================================================

# -------- Electricity --------

elec_techs = [
    "Solar",
    "Wind Onshore",
    "Wind Offshore",
    "Nuclear",
    "H2CCGT",
    "FC",
    "CCGT",
    "CCGTCCS",
    "BECCS",
]

elec_handles = [
    Patch(
        facecolor=tech_colors[t],
        edgecolor="black",
        label=t
    )
    for t in elec_techs
]

leg1 = fig.legend(
    handles=elec_handles,
    title="Electricity",
    loc="center left",
    bbox_to_anchor=(0.85, 0.75),
    frameon=False
)

# -------- Hydrogen --------

h2_techs = [
    "SMRCCS",
    "ATRCCS",
    "BGCCS",
    "WE"
]

h2_handles = [
    Patch(
        facecolor=tech_colors[t],
        edgecolor="black",
        label=t
    )
    for t in h2_techs
]

leg2 = fig.legend(
    handles=h2_handles,
    title="Hydrogen",
    loc="center left",
    bbox_to_anchor=(0.85, 0.48),
    frameon=False
)

# -------- Heating --------

heat_techs = [
    "ASHP",
    "HyBoiler"
]

heat_handles = [
    Patch(
        facecolor=tech_colors[t],
        edgecolor="black",
        label=t
    )
    for t in heat_techs
]

leg3 = fig.legend(
    handles=heat_handles,
    title="Heating",
    loc="center left",
    bbox_to_anchor=(0.85, 0.25),
    frameon=False
)

fig.add_artist(leg1)
fig.add_artist(leg2)
# ======================================================
# LAYOUT
# ======================================================

plt.subplots_adjust(
    hspace=0.3,
    wspace=0.37,
    right=0.8,
    left=0.05,
    top=0.92,
    bottom=0.08
)

plt.show()