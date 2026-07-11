import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Patch

# تنظیم فونت
plt.rcParams['font.family'] = 'serif'

# رنگ‌ها
tech_colors = {
    "Solar": "#FFFF00", "Wind Onshore": "#00FF00", "Wind Offshore": "#228b22",
    "Battery": "#00FFFF", "CCGT": "#8b0000", "Nuclear": "#0000FF",
    "H2CCGT": "#8000FF", "FC": "#FF00FF", "BECCS": "#FF0080",
    "CCGTCCS": "#FF0000", "Biomass": "#ffa54f",
    "SMRCCS": "#6c7b8b", "ATRCCS": "#9fb6cd", "BGCCS": "#96cdcd", "WE": "#afeeee",
    "HyBoiler": "#8b5a00", "ASHP": "#cd8500", "Gas Boiler": "#5d4037"
}

# =====================================================
# Air-Cooled
# =====================================================

water_air = {
    "Elec": {
        "Nuclear": 10,
        "CCGT": -5,
        "CCGTCCS": 15,
        "H2CCGT": 10,
        "BECCS": 5,
        "Biomass": 7
    },
    "H2": {
        "SMRCCS": 7,
        "ATRCCS": 5,
        "BGCCS": 7,
        "WE": 12
    },
    "Direct": {
        "Biomass": 16
    }
}

energy_air = {
    "Elec": {
        "Solar": 5,
        "WindOn": -2,
        "WindOff": 5,
        "Nuclear": -2,
        "H2CCGT": 5,
        "Biomass": -2,
        "FC": -2,
        "BECCS": 5,
        "CCGT": -2,
        "CCGTCCS": -2
    },
    "H2": {
        "ATRCCS": 7,
        "SMRCCS": 4,
        "BGCCS": -2,
        "WE": -2
    },
    "Heating": {
        "ASHP": 10,
        "HyBoiler": -3
    }
}

# =====================================================
# Water-Cooled
# =====================================================

water_water = {
    "Elec": {
        "Nuclear": 10,
        "CCGT": -5,
        "CCGTCCS": 15,
        "H2CCGT": 10,
        "BECCS": 5,
        "Biomass": 7
    },
    "H2": {
        "SMRCCS": 7,
        "ATRCCS": 5,
        "BGCCS": 7,
        "WE": 12
    },
    "Direct": {
        "Biomass": 16
    }
}

energy_water = {
    "Elec": {
        "Solar": 5,
        "WindOn": -2,
        "WindOff": 5,
        "Nuclear": -2,
        "H2CCGT": 5,
        "Biomass": -2,
        "FC": -2,
        "BECCS": 5,
        "CCGT": -2,
        "CCGTCCS": -2
    },
    "H2": {
        "ATRCCS": 7,
        "SMRCCS": 4,
        "BGCCS": -2,
        "WE": -2
    },
    "Heating": {
        "ASHP": 10,
        "HyBoiler": -3
    }
}

# =====================================================
# Direct-to-Chip
# =====================================================

water_d2c = {
    "Elec": {
        "Nuclear": 10,
        "CCGT": -5,
        "CCGTCCS": 15,
        "H2CCGT": 10,
        "BECCS": 5,
        "Biomass": 7
    },
    "H2": {
        "SMRCCS": 7,
        "ATRCCS": 5,
        "BGCCS": 7,
        "WE": 12
    },
    "Direct": {
        "Biomass": 16
    }
}

energy_d2c = {
    "Elec": {
        "Solar": 5,
        "WindOn": -2,
        "WindOff": 5,
        "Nuclear": -2,
        "H2CCGT": 5,
        "Biomass": -2,
        "FC": -2,
        "BECCS": 5,
        "CCGT": -2,
        "CCGTCCS": -2
    },
    "H2": {
        "ATRCCS": 7,
        "SMRCCS": 4,
        "BGCCS": -2,
        "WE": -2
    },
    "Heating": {
        "ASHP": 10,
        "HyBoiler": -3
    }
}

# =====================================================
# داده‌های هر پنل
# =====================================================

water_panels = [water_air, water_water, water_d2c]
energy_panels = [energy_air, energy_water, energy_d2c]

panel_titles = [
    "Air-Cooled",
    "Water-Cooled",
    "Direct-to-Chip"
]

# =====================================================
# رسم
# =====================================================

fig, axes = plt.subplots(2, 3, figsize=(15, 10))

def plot_custom_bars(ax, data_dict, title):

    x = np.arange(len(data_dict))
    width = 0.2

    for i, (cat, techs) in enumerate(data_dict.items()):

        bottom_pos = 0
        bottom_neg = 0

        for tech, val in techs.items():

            if val >= 0:
                ax.bar(
                    i, val, width,
                    bottom=bottom_pos,
                    color=tech_colors.get(tech, 'gray'),
                    edgecolor='black'
                )
                bottom_pos += val

            else:
                ax.bar(
                    i, val, width,
                    bottom=bottom_neg,
                    color=tech_colors.get(tech, 'gray'),
                    edgecolor='black'
                )
                bottom_neg += val

    ax.set_xticks(x)
    ax.set_xticklabels(list(data_dict.keys()))
    ax.set_title(title)
    ax.axhline(0, color='black', linewidth=0.8)

for i in range(3):

    plot_custom_bars(
        axes[0, i],
        water_panels[i],
        panel_titles[i]
    )

    axes[0, i].set_ylabel("Additional Water")

    plot_custom_bars(
        axes[1, i],
        energy_panels[i],
        panel_titles[i]
    )

    axes[1, i].set_ylabel("Add. Land & Energy")

legend_elements = [
    Patch(
        facecolor=tech_colors[t],
        edgecolor='black',
        label=t
    )
    for t in tech_colors
]

fig.legend(
    handles=legend_elements,
    loc='center right',
    title="Technologies",
    frameon=False,
    bbox_to_anchor=(1, 0.5)
)

plt.tight_layout(rect=[0, 0, 0.9, 1])
plt.show()