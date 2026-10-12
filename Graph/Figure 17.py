import numpy as np
import matplotlib.pyplot as plt
from matplotlib.ticker import MultipleLocator

# ============================================================
# DATA
# ============================================================

years = np.array([2030, 2035, 2040, 2045, 2050])

# ------------------------------------------------------------
# Direct water — million liters
# ------------------------------------------------------------

direct_water = {
    "Base": [
        47.805,
        151.3825,
        199.1875,
        246.9925,
        270.895
    ],

    "Pessimistic": [
        47.805,
        139.3825,
        103.2605,
        132.5775,
        143.415
    ],

    "Aggressive": [
        47.805,
        180.3825,
        223.09,
        286.83,
        350.57
    ]
}


# ------------------------------------------------------------
# Indirect water — billion liters
# ------------------------------------------------------------

indirect_water = {
    "Base": [
        235,
        382,
        539,
        732,
        845
    ],

    "Pessimistic": [
        235,
        300,
        400,
        650,
        740
    ],

    "Aggressive": [
        235,
        450,
        845,
        920,
        1030
    ]
}


# ============================================================
# PUBLICATION STYLE
# ============================================================

plt.rcParams.update({

    # Serif font
    "font.family": "serif",
    "font.serif": [
        "Times New Roman",
        "Times",
        "DejaVu Serif"
    ],

    # Typography
    "font.size": 10,
    "axes.labelsize": 11,
    "axes.titlesize": 12,
    "xtick.labelsize": 9.5,
    "ytick.labelsize": 9.5,
    "legend.fontsize": 9.5,

    # Axes
    "axes.linewidth": 0.8,

    # Ticks
    "xtick.major.width": 0.8,
    "ytick.major.width": 0.8,

    # Vector output
    "pdf.fonttype": 42,
    "ps.fonttype": 42,
    "svg.fonttype": "none",

    # High-resolution raster
    "figure.dpi": 150,
    "savefig.dpi": 600,
})


# ============================================================
# COLORS
# ============================================================

colors = {
    "Base": "#1B4F72",
    "Pessimistic": "#7F8C8D",
    "Aggressive": "#C0392B"
}

markers = {
    "Base": "o",
    "Pessimistic": "s",
    "Aggressive": "^"
}


# ============================================================
# FIGURE
# ============================================================

fig, axes = plt.subplots(
    2,
    1,
    figsize=(5.2, 7.0),
    sharex=False
)


# ============================================================
# FUNCTION FOR EACH PANEL
# ============================================================

def plot_panel(
    ax,
    dataset,
    title,
    ylabel,
    y_max,
    y_step
):

    for scenario in [
        "Base",
        "Pessimistic",
        "Aggressive"
    ]:

        y = np.asarray(
            dataset[scenario],
            dtype=float
        )

        ax.plot(
            years,
            y,

            color=colors[scenario],

            linewidth=2.0,

            linestyle="-",

            marker=markers[scenario],

            markersize=5.5,

            markeredgewidth=0.8,

            markeredgecolor="white",

            solid_capstyle="round",

            solid_joinstyle="round",

            label=scenario,

            zorder=5
        )


    # --------------------------------------------------------
    # Title
    # --------------------------------------------------------

    ax.set_title(
        title,
        loc="left",
        fontsize=12,
        fontweight="bold",
        pad=10
    )


    # --------------------------------------------------------
    # Axes limits
    # --------------------------------------------------------

    ax.set_xlim(
        2029,
        2051
    )

    ax.set_ylim(
        0,
        y_max
    )


    # --------------------------------------------------------
    # Ticks
    # --------------------------------------------------------

    ax.set_xticks(years)

    ax.yaxis.set_major_locator(
        MultipleLocator(y_step)
    )


    # --------------------------------------------------------
    # Labels
    # --------------------------------------------------------

    ax.set_ylabel(
        ylabel,
        fontsize=11,
        labelpad=9
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
    # Tick style
    # --------------------------------------------------------

    ax.tick_params(
        axis="both",
        which="major",
        direction="out",
        length=4,
        width=0.8
    )


# ============================================================
# PANEL A — DIRECT WATER
# ============================================================

plot_panel(
    axes[0],
    direct_water,
    title="a ",
    ylabel="Water consumption (million L)",
    y_max=380,
    y_step=50
)


# ============================================================
# PANEL B — INDIRECT WATER
# ============================================================

plot_panel(
    axes[1],
    indirect_water,
    title="b ",
    ylabel="Water consumption (billion L)",
    y_max=1100,
    y_step=200
)


# ============================================================
# X AXIS
# ============================================================

axes[1].set_xlabel(
    "Year",
    fontsize=11,
    labelpad=7
)


# ============================================================
# LEGEND
# ============================================================

handles, labels = axes[0].get_legend_handles_labels()

fig.legend(
    handles,
    labels,
    loc="upper center",
    bbox_to_anchor=(0.5, 0.995),
    ncol=3,
    frameon=False,
    handlelength=2.8,
    handletextpad=0.6,
    columnspacing=2.5
)


# ============================================================
# LAYOUT
# ============================================================

fig.subplots_adjust(
    left=0.13,
    right=0.98,
    bottom=0.09,
    top=0.91,
    hspace=0.30
)


# ============================================================
# EXPORT
# ============================================================

# Vector PDF
fig.savefig(
    "water_consumption_trajectories.pdf",
    bbox_inches="tight",
    pad_inches=0.03
)

# Vector SVG
fig.savefig(
    "water_consumption_trajectories.svg",
    bbox_inches="tight",
    pad_inches=0.03
)

# 600 dpi TIFF
fig.savefig(
    "water_consumption_trajectories.tiff",
    dpi=600,
    bbox_inches="tight",
    pad_inches=0.03
)

# 600 dpi PNG
fig.savefig(
    "water_consumption_trajectories.png",
    dpi=600,
    bbox_inches="tight",
    pad_inches=0.03
)

plt.show()