import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import warnings

warnings.filterwarnings('ignore')


# ============================================================
# 1. GLOBAL PLOT SETTINGS
# ============================================================

plt.rcParams.update({
    'font.family':       'serif',
    'font.size':         8,
    'axes.titlesize':    8,
    'axes.labelsize':    7,
    'xtick.labelsize':   6.0,
    'ytick.labelsize':   6.0,
    'legend.fontsize':   6.0,

    'axes.linewidth':    0.6,

    'xtick.major.width': 0.1,
    'ytick.major.width': 0.1,
    'xtick.minor.width': 0.4,
    'ytick.minor.width': 0.4,

    'xtick.major.size':  3,
    'ytick.major.size':  1,
    'xtick.minor.size':  3,
    'ytick.minor.size':  1,

    'xtick.direction':   'out',
    'ytick.direction':   'out',

    'axes.spines.top':   False,
    'axes.spines.right': False,

    'pdf.fonttype':      42,
    'ps.fonttype':       42,

    'lines.linewidth':   1.0,

    'figure.facecolor':  'white',
    'axes.facecolor':    'white',
})


# ============================================================
# 2. READ EXCEL FILE
# ============================================================

filepath = 'UK_Load.xlsx'

df = pd.read_excel(filepath)

# Convert column names to strings
df.columns = [str(col).strip() for col in df.columns]


# ============================================================
# 3. READ THE FOUR LDC COLUMNS
# ============================================================

days = [6, 12, 24, 365]

column_names = [
    '6 days',
    '12 days',
    '24 days',
    '365 days'
]

ldcs = {}

for d, col in zip(days, column_names):

    # Read column
    vals = pd.to_numeric(df[col], errors='coerce').dropna().values

    # Check number of observations
    if len(vals) != 8760:
        print(
            f'Warning: column "{col}" contains '
            f'{len(vals)} valid values instead of 8760.'
        )

    # Sort from highest to lowest
    ldcs[d] = np.sort(vals)[::-1] / 1e6


# ============================================================
# 4. COMMON X-AXIS
# ============================================================

N_GRID = 8760

x_hours = np.arange(1, N_GRID + 1)


# ============================================================
# 5. COLORS AND LINE SETTINGS
# ============================================================

PALETTE = {
    365:   '#000000',   # Black
    6:  '#C0392B',   # Red
    24:  '#2980B9',   # Blue
    12: '#F1C40F'    # Yellow
}

LSTYLE = {
    6:   (0, (3, 1.2, 1, 1.2)),
    12:  (0, (4, 1.8)),
    24:  (0, (2, 1, 1, 1, 1, 1)),
    365: '-'
}

LWIDTH = {
    6:   0.6,
    12:  0.6,
    24:  0.6,
    365: 0.8
}

ALPHA = {
    6:   0.85,
    12:  0.85,
    24:  0.85,
    365: 1.0
}

LABEL = {
    6:   '6 days',
    12:  '12 days',
    24:  '24 days',
    365: '365 days (ref.)'
}


# ============================================================
# 6. CREATE FIGURE
# ============================================================

fig, ax = plt.subplots(
    figsize=(3.4, 2.5),
    dpi=300
)

fig.subplots_adjust(
    left=0.14,
    right=0.97,
    top=0.92,
    bottom=0.17
)


# ============================================================
# 7. REFERENCE BAND: ±10% AROUND 365-DAY LDC
# ============================================================

ref = ldcs[365]

lo = np.where(
    ref >= 0,
    ref * 0.90,
    ref * 1.10
)

hi = np.where(
    ref >= 0,
    ref * 1.10,
    ref * 0.90
)

ax.fill_between(
    x_hours,
    lo,
    hi,
    color='#1A252C',
    alpha=0.09,
    lw=0,
    label='±10% ref. band',
    zorder=1
)


# ============================================================
# 8. ZERO LINE
# ============================================================

ax.axhline(
    0,
    color='#7F8C8D',
    lw=0.1,
    ls='-',
    zorder=1
)


# ============================================================
# 9. PLOT FOUR LDC CURVES
# ============================================================

for d in [6, 12, 24, 365]:

    ax.plot(
        x_hours,
        ldcs[d],
        color=PALETTE[d],
        lw=LWIDTH[d],
        ls=LSTYLE[d],
        alpha=ALPHA[d],
        label=LABEL[d],
        zorder=4
    )


# ============================================================
# 10. MARK THE FIRST POINT OF EACH CURVE
# ============================================================

for d in [6, 12, 24, 365]:

    ax.scatter(
        [1],
        [ldcs[d][0]],
        s=7,
        color=PALETTE[d],
        zorder=6,
        clip_on=False
    )


# ============================================================
# 11. AXIS LIMITS
# ============================================================

ax.set_xlim(
    0,
    8760
)


# ============================================================
# 12. AXIS LABELS
# ============================================================

ax.set_xlabel(
    'Hour',
    labelpad=2
)

ax.set_ylabel(
    'Load duration curve (TWh)',
    labelpad=2
)


# ============================================================
# 13. X-AXIS TICKS
# ============================================================

ax.xaxis.set_major_locator(
    mticker.MultipleLocator(2000)
)

ax.xaxis.set_minor_locator(
    mticker.MultipleLocator(1000)
)


# ============================================================
# 14. Y-AXIS FORMAT
# ============================================================

ax.yaxis.set_major_formatter(
    mticker.ScalarFormatter(useMathText=True)
)

ax.ticklabel_format(
    style='sci',
    axis='y',
    scilimits=(0, 0)
)


# ============================================================
# 15. TICK SETTINGS
# ============================================================

ax.tick_params(
    axis='both',
    which='major',
    labelsize=6,
    length=3,
    width=0.4
)

ax.tick_params(
    axis='both',
    which='minor',
    length=3,
    width=0.4
)


# ============================================================
# 16. LEGEND
# ============================================================

leg = ax.legend(
    loc='upper right',
    frameon=False,
    edgecolor='#D5D8DC',
    fancybox=False,
    handlelength=1.8,
    labelspacing=0.25
)

leg.get_frame().set_linewidth(0.4)


# ============================================================
# 17. FINAL LAYOUT
# ============================================================

plt.tight_layout()


# ============================================================
# 18. SAVE OUTPUT
# ============================================================

plt.savefig(
    'final_twh_ldc.png',
    dpi=300,
    bbox_inches='tight'
)

plt.savefig(
    'final_twh_ldc.pdf',
    dpi=300,
    bbox_inches='tight'
)


# ============================================================
# 19. SHOW
# ============================================================

plt.show()