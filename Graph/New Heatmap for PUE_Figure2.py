import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

from matplotlib.colors import BoundaryNorm, LinearSegmentedColormap

plt.rcParams["font.family"] = "serif"


# =====================================================
# CONFIG
# =====================================================

EXCEL_FILE = "data_PUE.xlsx"
SHEET_NAME = "Sheet1"


COLUMNS_BY_TYPE = {

    "Air-Cooled": [
        "PUE_Air_London",
        "PUE_Air_Scotland",
        "WUE_Air_London",
        "WUE_Air_Scotland",
    ],

    "Water-Cooled": [
        "PUE_Water_London",
        "PUE_Water_Scotland",
        "WUE_Water_London",
        "WUE_Water_Scotland",
    ],

    "Direct-to-Chip": [
        "PUE_Direct_London",
        "PUE_Direct_Scotland",
        None,
        None
    ]
}



MONTH_LABELS = [
    "J", "F", "M", "A", "M", "J",
    "J", "A", "S", "O", "N", "D"
]


DAYS_IN_MONTH = [
    31, 28, 31, 30, 31, 30,
    31, 31, 30, 31, 30, 31
]


MONTH_TICKS = (
    np.cumsum(DAYS_IN_MONTH)
    - np.array(DAYS_IN_MONTH) / 2
)



# =====================================================
# LOAD DATA
# =====================================================

df = pd.read_excel(
    EXCEL_FILE,
    sheet_name=SHEET_NAME
)



# =====================================================
# FIGURE
# =====================================================

fig = plt.figure(
    figsize=(18, 14),
    constrained_layout=True
)


subfigs = fig.subfigures(
    nrows=3,
    ncols=1,
    hspace=0.08
)


days = np.arange(366)
hours = np.arange(1, 26)

X, Y = np.meshgrid(days, hours)



# =====================================================
# PLOTTING
# =====================================================

for idx, (group_name, cols) in enumerate(COLUMNS_BY_TYPE.items()):


    subfig = subfigs[idx]


    subfig.suptitle(
        group_name,
        fontsize=16,
        fontweight="bold"
    )


    axs = subfig.subplots(
        1,
        4,
        squeeze=False
    )[0]



    for i, col_name in enumerate(cols):


        ax = axs[i]


        # ---------------------------------------------
        # Empty panels
        # ---------------------------------------------

        if col_name is None:

            ax.axis("off")

            continue



        # ---------------------------------------------
        # Load data
        # ---------------------------------------------

        raw_series = (

            pd.to_numeric(
                df[col_name],
                errors="coerce"
            )

            .dropna()
            .values
        )


        series = np.zeros(8760)


        n = min(
            len(raw_series),
            8760
        )


        series[:n] = raw_series[:n]


        Z = series.reshape(
            365,
            24
        ).T



        # ---------------------------------------------
        # Colormap + fixed levels
        # ---------------------------------------------

        if "WUE" in col_name:


            cmap = LinearSegmentedColormap.from_list(
                "WUE_blue_black",
                [
                    "#f7fbff",
                    "#9ecae1",
                    "#4292c6",
                    "#08519c",
                    "#000000"
                ]
            )


            levels = [
                0.0,
                0.5,
                1.0,
                1.5,
                2.0,
                2.5,
                3.0,
                3.4
            ]



        else:


            cmap = LinearSegmentedColormap.from_list(
                "PUE_red_black",
                [
                    "#fff5f0",
                    "#fcae91",
                    "#fb6a4a",
                    "#cb181d",
                    "#000000"
                ]
            )


            levels = [
                1.00,
                1.05,
                1.10,
                1.20,
                1.30,
                1.40
            ]



        norm = BoundaryNorm(
            levels,
            ncolors=cmap.N,
            clip=True
        )



        # ---------------------------------------------
        # Heatmap
        # ---------------------------------------------

        cf = ax.contourf(
            X[:-1, :-1],
            Y[:-1, :-1],
            Z,
            levels=levels,
            cmap=cmap,
            norm=norm,
            extend="both"
        )



        # ---------------------------------------------
        # Contour lines
        # ---------------------------------------------

        ax.contour(
            X[:-1, :-1],
            Y[:-1, :-1],
            Z,
            levels=8,
            colors="k",
            linewidths=0.1,
            alpha=0.1
        )
        # ---------------------------------------------
        # Title
        # ---------------------------------------------

        parts = col_name.split("_")

        metric = parts[0]
        location = parts[-1]

        title = f"{metric}-{location}"


        ax.set_title(
            title,
            fontsize=13,
            fontweight="bold"
        )



        # ---------------------------------------------
        # Axis formatting
        # ---------------------------------------------

        if i == 0:

            ax.set_ylabel(
                "Hour",
                fontsize=13,
                fontweight="bold"
            )


        ax.set_xlabel(
            "Month",
            fontsize=13,
            fontweight="bold"
        )


        ax.set_xticks(
            MONTH_TICKS
        )


        ax.set_xticklabels(
            MONTH_LABELS
        )


        ax.set_yticks(
            [1, 6, 12, 18, 24]
        )


        ax.tick_params(
            labelsize=12
        )



        # ---------------------------------------------
        # Colorbar
        # ---------------------------------------------

        cbar = fig.colorbar(
            cf,
            ax=ax,
            shrink=0.85,
            pad=0.02,
            aspect=25
        )


        cbar.set_ticks(
            levels
        )


        cbar.set_ticklabels(
            [
                f"{x:.2f}"
                for x in levels
            ]
        )


        cbar.ax.tick_params(
            labelsize=12
        )



# =====================================================
# SAVE
# =====================================================

plt.savefig(
    "heatmap_organized_fixed_scale.png",
    dpi=600,
    bbox_inches="tight"
)


plt.show()