import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from matplotlib.colors import TwoSlopeNorm, LinearSegmentedColormap
import matplotlib as mpl
from matplotlib.ticker import FormatStrFormatter
plt.rcParams["font.family"] = "serif"

# ===============================
# CONFIG
# ===============================
EXCEL_FILE = "data_PUE.xlsx"
SHEET_NAME = "Sheet1"
COL_INDEX = 0

MONTH_LABELS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", 
                "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
DAYS_IN_MONTH = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
# Calculate cumulative days for tick positions
MONTH_TICKS = np.cumsum(DAYS_IN_MONTH) - np.array(DAYS_IN_MONTH) / 2

# ===============================
# LOAD DATA
# ===============================
df = pd.read_excel(EXCEL_FILE, sheet_name=SHEET_NAME, header=None)
series = pd.to_numeric(df.iloc[:, COL_INDEX], errors="coerce").dropna().values

if len(series) < 8760:
    raise ValueError(f"Expected 8760 values, got {len(series)}")

series = series[:8760]

# ===============================
# CALCULATION
# ===============================
Z = series.reshape(365, 24).T

# ===============================
# NORMALIZATION
# ===============================
vmin = np.nanmin(Z)
vmax = np.nanmax(Z)
vcenter = np.nanmean(Z)

norm = TwoSlopeNorm(vmin=vmin, vcenter=vcenter, vmax=vmax)

cmap = LinearSegmentedColormap.from_list(
    "light_to_dark_red",
    ["#fff5f0",   # almost white red (very low)
     "#fee0d2",
     "#fcbba1",
     "#fc9272",
     "#fb6a4a",
     "#ef3b2c",
     "#cb181d",
     "#99000d"],  # darkest red (max)
    N=256
)

# ===============================
# PLOT
# ===============================
fig, ax = plt.subplots(figsize=(12, 5))

days = np.arange(366)
hours = np.arange(1, 26)
X, Y = np.meshgrid(days, hours)

cf = ax.contourf(
    X[:-1, :-1],
    Y[:-1, :-1],
    Z,
    levels=200,
    cmap=cmap,
    norm=norm,
    extend="both"
)

cs = ax.contour(
    X[:-1, :-1],
    Y[:-1, :-1],
    Z,
    levels=7,
    colors="black",
    linewidths=0.2,
    alpha=0.3
)

# ===============================
# AXES AND LABELS
# ===============================
ax.set_ylabel("Hour of Day", fontsize=11)
ax.set_xlabel("Month", fontsize=11)
ax.set_xticks(MONTH_TICKS)
ax.set_xticklabels(MONTH_LABELS)
ax.set_title("Daily Hourly Heatmap (Full Year)", fontsize=12, fontweight="bold")

cbar = fig.colorbar(cf, ax=ax, fraction=0.02, pad=0.02)
cbar.set_label("Hourly Value", fontsize=11)
cbar.ax.yaxis.set_major_formatter(
    FormatStrFormatter('%.2f')
)
plt.tight_layout()
plt.savefig("heatmap_daily_hourly.png", dpi=300, bbox_inches="tight")
plt.show()

#%%
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

from matplotlib.colors import TwoSlopeNorm, LinearSegmentedColormap
from matplotlib.ticker import FormatStrFormatter

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
        None,   # Empty panel
        None    # Empty panel
    ]
}

MONTH_LABELS = ["J", "F", "M", "A", "M", "J",
                "J", "A", "S", "O", "N", "D"]

DAYS_IN_MONTH = [31, 28, 31, 30, 31, 30,
                 31, 31, 30, 31, 30, 31]

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
        # Blank panels for removed WUE Direct plots
        # ---------------------------------------------
        if col_name is None:
            ax.axis("off")
            continue

        # ---------------------------------------------
        # Load series
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

        n = min(len(raw_series), 8760)
        series[:n] = raw_series[:n]

        Z = series.reshape(365, 24).T

        # ---------------------------------------------
        # Colormap
        # ---------------------------------------------
        if "WUE" in col_name:

            cmap = LinearSegmentedColormap.from_list(
                "blue_map",
                ["#f7fbff", "#08306b"]
            )

        else:

            cmap = LinearSegmentedColormap.from_list(
                "red_map",
                ["#fff5f0", "#99000d"]
            )

        norm = TwoSlopeNorm(
            vmin=np.nanmin(Z),
            vcenter=np.nanmean(Z),
            vmax=np.nanmax(Z)
        )

        # ---------------------------------------------
        # Filled contour
        # ---------------------------------------------
        cf = ax.contourf(
            X[:-1, :-1],
            Y[:-1, :-1],
            Z,
            levels=50,
            cmap=cmap,
            norm=norm
        )

        # ---------------------------------------------
        # Thin contour lines
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

        metric = parts[0]      # PUE or WUE
        location = parts[-1]   # London or Scotland

        title = f"{metric}-{location}"

        ax.set_title(
            title,
            fontsize=13,
            fontweight="bold"
        )
        
        # ---------------------------------------------
        # Axes formatting
        # ---------------------------------------------
        if i == 0:
            ax.set_ylabel(
                "Hour",
                fontsize=13, fontweight="bold"
            )

        ax.set_xlabel("Month", fontsize=13, fontweight="bold")

        ax.set_xticks(MONTH_TICKS)
        ax.set_xticklabels(MONTH_LABELS)

        ax.set_yticks([1, 6, 12, 18, 24])

        ax.tick_params(
            labelsize=12
        )


        from matplotlib.ticker import ScalarFormatter
        
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

        # Create 6 clean ticks
        ticks = np.linspace(
            np.nanmin(Z),
            np.nanmax(Z),
            6
        )

        cbar.set_ticks(ticks)

        # Force fixed decimal labels
        cbar.set_ticklabels(
            [f"{t:.3f}" for t in ticks]
        )

        cbar.ax.tick_params(
            labelsize=12
        )
        
        #cbar.ax.yaxis.offsetText.set_visible(False)


        

# =====================================================
# SAVE
# =====================================================
plt.savefig(
    "heatmap_organized.png",
    dpi=600,
    bbox_inches="tight"
)

plt.show()