import numpy as np
import matplotlib.pyplot as plt
from matplotlib.ticker import MultipleLocator

# ============================================================
# 1. DATA
# ============================================================

years = np.array([2030, 2035, 2040, 2045, 2050])

data = {
    "Air-cooled": {
        "Base":        [15.14254, 56.49105, 70.04890, 76.82783, 84.51061],
        "Pessimistic": [15.14254, 37.51006, 29.37535, 40.67356, 49.71212],
        "Aggressive":  [15.14254, 63.26998, 81.34711, 99.42425, 117.50140],
    },

    "Water-cooled": {
        "Base":        [15.14254, 46.83622, 61.62660, 76.41698, 83.81218],
        "Pessimistic": [15.14254, 30.83622, 26.92006, 40.04583, 44.37115],
        "Aggressive":  [15.14254, 54.83622, 69.02179, 88.74230, 108.46280],
    },

    "D2C": {
        "Base":        [13.92761, 44.10410, 58.03172, 71.95933, 78.92313],
        "Pessimistic": [13.92761, 30.10410, 24.53306, 38.17649, 41.78283],
        "Aggressive":  [13.92761, 49.10410, 64.99552, 83.56567, 98.00000],
    }
}


# ============================================================
# 2. NATURE-STYLE PARAMETERS
# ============================================================

plt.rcParams.update({

    # Serif typography
    "font.family": "serif",
    "font.serif": [
        "Times New Roman",
        "Times",
        "DejaVu Serif"
    ],

    # Font sizes
    "font.size": 12,
    "axes.labelsize": 12,
    "axes.titlesize": 12,
    "xtick.labelsize": 9.5,
    "ytick.labelsize": 9.5,
    "legend.fontsize": 11,

    # Vector text
    "pdf.fonttype": 42,
    "ps.fonttype": 42,
    "svg.fonttype": "none",

    # Axes
    "axes.linewidth": 0.8,

    # Ticks
    "xtick.major.width": 0.8,
    "ytick.major.width": 0.8,

    # Saving
    "savefig.dpi": 600,
})


# ============================================================
# 3. COLORS
# ============================================================

# Muted, publication-friendly palette

colors = {
    "Base":        "#1B4F72",   # deep blue
    "Pessimistic": "#7F8C8D",   # muted gray
    "Aggressive":  "#C0392B",   # dark red
}

markers = {
    "Base": "o",
    "Pessimistic": "s",
    "Aggressive": "^",
}


# ============================================================
# 4. FIGURE
# ============================================================

fig, axes = plt.subplots(
    nrows=1,
    ncols=3,
    figsize=(11.0, 3.8),
    sharex=False,
    sharey=False
)


systems = [
    "Air-cooled",
    "Water-cooled",
    "D2C"
]


# ============================================================
# 5. PLOT EACH PANEL
# ============================================================

for i, (ax, system) in enumerate(zip(axes, systems)):

    for scenario in [
        "Base",
        "Pessimistic",
        "Aggressive"
    ]:

        y = np.asarray(
            data[system][scenario],
            dtype=float
        )

        ax.plot(
            years,
            y,

            # Line
            color=colors[scenario],
            linewidth=2.0,
            linestyle="-",

            # Marker
            marker=markers[scenario],
            markersize=5.5,
            markeredgewidth=0.8,
            markeredgecolor="white",

            # smooth appearance
            solid_capstyle="round",
            solid_joinstyle="round",

            label=scenario,
            zorder=5
        )


    # --------------------------------------------------------
    # Panel title
    # --------------------------------------------------------

    ax.set_title(
        system,
        fontsize=12,
        fontweight="bold",
        pad=10
    )


    # --------------------------------------------------------
    # X axis
    # --------------------------------------------------------

    ax.set_xlim(
        2029,
        2051
    )

    ax.set_xticks(years)

    ax.set_xticklabels(
        years,
        fontsize=11
    )


    # --------------------------------------------------------
    # Y axis
    # --------------------------------------------------------

    ax.set_ylim(
        0,
        125
    )

    ax.yaxis.set_major_locator(
        MultipleLocator(20)
    )


    # --------------------------------------------------------
    # Grid
    # --------------------------------------------------------

    ax.grid(
        axis="y",
        which="major",
        linestyle="--",
        linewidth=0.45,
        alpha=0.25,
        zorder=0
    )

    ax.grid(
        axis="x",
        visible=False
    )


    # --------------------------------------------------------
    # Spines
    # --------------------------------------------------------

    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    ax.spines["left"].set_linewidth(0.8)
    ax.spines["bottom"].set_linewidth(0.8)


    # --------------------------------------------------------
    # Tick appearance
    # --------------------------------------------------------

    ax.tick_params(
        axis="both",
        which="major",
        direction="out",
        length=4,
        width=0.8
    )


# ============================================================
# 6. AXIS LABELS
# ============================================================

axes[0].set_ylabel(
    "Data centre demand (TWh)",
    fontsize=12,
    labelpad=8
)

for ax in axes:
    ax.set_xlabel(
        "Year",
        fontsize=12,
        labelpad=7
    )


# ============================================================
# 7. PANEL LABELS
# ============================================================

panel_labels = ["a", "b", "c"]

for ax, label in zip(axes, panel_labels):

    ax.text(
        0.02,
        0.98,
        label,
        transform=ax.transAxes,
        ha="left",
        va="top",
        fontsize=12,
        fontweight="bold"
    )


# ============================================================
# 8. LEGEND
# ============================================================

handles, labels = axes[0].get_legend_handles_labels()

legend = fig.legend(
    handles,
    labels,
    loc="upper center",
    bbox_to_anchor=(0.5, 1.015),
    ncol=3,
    frameon=False,
    handlelength=2.8,
    handletextpad=0.6,
    columnspacing=2.5
)


# ============================================================
# 9. LAYOUT
# ============================================================

fig.subplots_adjust(
    left=0.075,
    right=0.985,
    bottom=0.18,
    top=0.80,
    wspace=0.12
)


# ============================================================
# 10. EXPORT — PUBLICATION QUALITY
# ============================================================

# Vector PDF
fig.savefig(
    "scenario_trajectories_Nature.pdf",
    bbox_inches="tight",
    pad_inches=0.03
)

# Vector SVG
fig.savefig(
    "scenario_trajectories_Nature.svg",
    bbox_inches="tight",
    pad_inches=0.03
)

# High-resolution TIFF
fig.savefig(
    "scenario_trajectories_Nature.tiff",
    dpi=600,
    bbox_inches="tight",
    pad_inches=0.03
)

# High-resolution PNG
fig.savefig(
    "scenario_trajectories_Nature.png",
    dpi=600,
    bbox_inches="tight",
    pad_inches=0.03
)

plt.show()