import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec

# -----------------------------
# Global Style
# -----------------------------
plt.rcParams.update({
    "font.family": "serif",
    "font.size": 11
})

# -----------------------------
# Data
# -----------------------------
regions = ['EA', 'EM', 'NE', 'NO', 'NT', 'NW',
           'SC', 'SE', 'SO', 'SW', 'WM', 'WN', 'WS']

# Structure:
# water  = [Base, Air, Water, Liquid]
# elec   = [Base, Air, Water, Liquid]
# carb   = [Base, Air, Water, Liquid]

data = {
    r: {
        'water': [30, 50, 150, 180],
        'elec':  [80, 100, 150, 210],
        'carb':  [80, 100, 300, 220],

        'base': 35,
        'air': 50,
        'water_cap': 40,
        'liquid': 25
    }
    for r in regions
}

# -----------------------------
# Bubble scaling
# -----------------------------
bubble_scale = 3.5

# -----------------------------
# Figure & Layout
# -----------------------------
fig = plt.figure(figsize=(20, 9))

gs = gridspec.GridSpec(
    2, 14,
    height_ratios=[5, 1.2],
    width_ratios=[1]*13 + [1.8],
    hspace=0.30,
    wspace=0.12
)

# -----------------------------
# Bubble Charts
# -----------------------------
for i, region in enumerate(regions):

    ax = fig.add_subplot(gs[0, i])

    # -------------------------
    # Base Scenario
    # -------------------------
    ax.scatter(
        data[region]['water'][0],
        data[region]['elec'][0],
        s=data[region]['carb'][0] * bubble_scale,
        color='gray',
        alpha=0.75,
        edgecolors='black',
        linewidth=0.8,
        zorder=3
    )

    # -------------------------
    # Air-Cooled
    # -------------------------
    ax.scatter(
        data[region]['water'][1],
        data[region]['elec'][1],
        s=data[region]['carb'][1] * bubble_scale,
        color='#5DA5DA',
        alpha=0.75,
        edgecolors='black',
        linewidth=0.8,
        zorder=3
    )

    # -------------------------
    # Water-Cooled
    # -------------------------
    ax.scatter(
        data[region]['water'][2],
        data[region]['elec'][2],
        s=data[region]['carb'][2] * bubble_scale,
        color='#F15854',
        alpha=0.75,
        edgecolors='black',
        linewidth=0.8,
        zorder=3
    )

    # -------------------------
    # Liquid Cooling
    # -------------------------
    ax.scatter(
        data[region]['water'][3],
        data[region]['elec'][3],
        s=data[region]['carb'][3] * bubble_scale,
        color='#60BD68',
        alpha=0.75,
        edgecolors='black',
        linewidth=0.8,
        zorder=3
    )

    # -------------------------
    # Titles
    # -------------------------
    ax.set_title(
        region,
        fontsize=12,
        fontweight='bold',
        pad=10
    )

    # -------------------------
    # Limits
    # -------------------------
    ax.set_xlim(0, 400)
    ax.set_ylim(0, 260)

    # -------------------------
    # Grid
    # -------------------------
    

    # -------------------------
    # Clean Spines
    # -------------------------
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)

    # -------------------------
    # Labels
    # -------------------------
    if i == 0:
        ax.set_ylabel(
            'Total Electricity Demand (TWh)',
            fontsize=12,
            fontweight='bold'
        )
    else:
        ax.set_yticklabels([])

    ax.set_xlabel('')

# -----------------------------
# Shared X Label
# -----------------------------
fig.supxlabel(
    'Water Consumption (ML)',
    fontsize=14,
    fontweight='bold',
    y=0.28
)

# -----------------------------
# Carbon Bubble Legend
# -----------------------------
ax_legend = fig.add_subplot(gs[0, 13])
ax_legend.axis('off')

legend_sizes = [
    100 * bubble_scale,
    200 * bubble_scale,
    300 * bubble_scale
]

legend_labels = ['100', '200', '300']

handles = []

for size, label in zip(legend_sizes, legend_labels):

    handle = ax_legend.scatter(
        [],
        [],
        s=size,
        color='gray',
        alpha=0.5,
        edgecolors='black',
        linewidth=0.8,
        label=label
    )

    handles.append(handle)

# Bubble size legend
legend1 = ax_legend.legend(
    handles=handles,
    labels=legend_labels,
    title='Carbon Intensity\n(g CO₂e / kWh)',
    loc='upper center',
    frameon=False,
    fancybox=True,
    borderpad=1.4,
    labelspacing=2.6,
    handletextpad=1.5,
    scatterpoints=1
)

legend1.get_title().set_fontsize(15)

ax_legend.add_artist(legend1)

# -----------------------------
# Scenario Color Legend
# -----------------------------
scenario_handles = [
    plt.Line2D([0], [0], marker='o', color='w',
               markerfacecolor='gray',
               markeredgecolor='black',
               markersize=10,
               label='Base'),

    plt.Line2D([0], [0], marker='o', color='w',
               markerfacecolor='#5DA5DA',
               markeredgecolor='black',
               markersize=10,
               label='Air-Cooled'),

    plt.Line2D([0], [0], marker='o', color='w',
               markerfacecolor='#F15854',
               markeredgecolor='black',
               markersize=10,
               label='Water-Cooled'),

    plt.Line2D([0], [0], marker='o', color='w',
               markerfacecolor='#60BD68',
               markeredgecolor='black',
               markersize=10,
               label='Liquid')
]

legend2 = ax_legend.legend(
    handles=scenario_handles,
    loc='lower center',
    title='Case Study',
    frameon=False,
    fancybox=True,
    borderpad=1.2,
    labelspacing=1.3,
    
)

legend2.get_title().set_fontsize(15)

# -----------------------------
# Table
# -----------------------------
ax_table = fig.add_subplot(gs[1, 0:13])
ax_table.axis('off')

cell_text = [
    [data[r]['base'] for r in regions],
    [data[r]['air'] for r in regions],
    [data[r]['water_cap'] for r in regions],
    [data[r]['liquid'] for r in regions]
]

table = ax_table.table(
    cellText=cell_text,
    rowLabels=[
        'Base',
        'Air-Cooled',
        'Water-Cooled',
        'Direct-to-Chip'
    ],
    colLabels=regions,
    loc='center',
    cellLoc='center'
)

table.auto_set_font_size(False)
table.set_fontsize(10)

table.scale(1, 2.0)

# -----------------------------
# Table Styling
# -----------------------------
row_colors = {
    1: 'gray',
    2: '#2E6F9E',
    3: '#C0392B',
    4: '#2E8B57'
}

for i in range(len(regions)):

    table[1, i].get_text().set_color(row_colors[1])
    table[2, i].get_text().set_color(row_colors[2])
    table[3, i].get_text().set_color(row_colors[3])
    table[4, i].get_text().set_color(row_colors[4])

# Style all cells
for key, cell in table.get_celld().items():

    cell.set_linewidth(0.5)

    # Header row
    if key[0] == 0:
        cell.set_facecolor('#F4F4F4')
        cell.set_text_props(weight='bold')

# -----------------------------
# Figure Title
# -----------------------------
fig.suptitle(
    'Regional Water–Electricity–Carbon Nexus',
    fontsize=18,
    fontweight='bold',
    y=0.98
)

# -----------------------------
# Show Figure
# -----------------------------
plt.show()