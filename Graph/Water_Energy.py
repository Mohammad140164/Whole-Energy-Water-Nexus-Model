import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec

# -----------------------------
# Global Style
# -----------------------------
plt.rcParams.update({
    "font.family": "serif",
    "font.size": 14,
    "mathtext.default": "regular"
})

# -----------------------------
# Data
# -----------------------------
regions = ['EA', 'EM', 'NE', 'NO', 'NT', 'NW',
           'SC', 'SE', 'SO', 'SW', 'WM', 'WN', 'WS']

# Structure:
# water  = [Base, Air, Water, Direct to Chip]
# elec   = [Base, Air, Water, Direct to Chip]
# carb   = [Base, Air, Water, Direct to Chip]

data = {
    'EA': {
        'water': [45, 62, 60, 60],
        'elec':  [57, 70, 71, 63],
        'carb':  [49, 57, 59, 51],
        'base':0,
        'air': 2669,
        'water_cap': 2770,
        'Direct to Chip': 1847
    },

    'EM': {
        'water': [12, 12.7, 12.6, 14.5],
        'elec':  [54, 52, 55, 53],
        'carb':  [398, 398, 398, 398],
        'base': 0,
        'air': 21,
        'water_cap': 22,
        'Direct to Chip': 21
    },

    'NE': {
        'water': [21, 25.6, 31, 16.4],
        'elec':  [36, 38, 33, 36],
        'carb':  [297, 305, 269, 292],
        'base': 0,
        'air': 15,
        'water_cap': 15,
        'Direct to Chip': 17
    },

    'NO': {
        'water': [44, 45, 47, 40],
        'elec':  [32, 31, 32, 31],
        'carb':  [10, 10, 10, 10],
        'base': 0,
        'air': 16,
        'water_cap': 17,
        'Direct to Chip': 20
    },

    'NT': {
        'water': [150, 217, 220, 205],
        'elec':  [58, 82, 90, 77],
        'carb':  [72, 46, 56, 65],
        'base': 0,
        'air': 4359,
        'water_cap': 5209,
        'Direct to Chip': 4167
    },

    'NW': {
        'water': [100, 106, 92, 135],
        'elec':  [67, 73, 73, 73],
        'carb':  [65, 54, 57, 56],
        'base': 0,
        'air': 57,
        'water_cap': 58,
        'Direct to Chip': 60
    },

    'SC': {
        'water': [30, 27, 29, 32],
        'elec':  [56, 59, 57, 60],
        'carb':  [67, 23, 84, 46],
        'base': 0,
        'air': 178,
        'water_cap': 20,
        'Direct to Chip': 407
    },

    'SE': {
        'water': [1.5, 1.4, 1.6, 1.8],
        'elec':  [40, 42, 42, 41],
        'carb':  [373, 326, 375, 377],
        'base': 0,
        'air': 270,
        'water_cap': 270,
        'Direct to Chip': 280
    },

    'SO': {
        'water': [40, 136, 89, 125],
        'elec':  [50, 85, 73, 81],
        'carb':  [108, 22, 38, 47],
        'base': 0,
        'air': 5309,
        'water_cap': 4450,
        'Direct to Chip': 5501
    },

    'SW': {
        'water': [84, 102, 105, 104],
        'elec':  [46, 75, 75, 77],
        'carb':  [10, 60, 20, 20],
        'base': 0,
        'air': 4762,
        'water_cap': 4937,
        'Direct to Chip': 5396
    },

    'WM': {
        'water': [115, 91, 103, 101],
        'elec':  [38, 36, 44, 36],
        'carb':  [54, 74, 10, 41],
        'base': 0,
        'air': 21,
        'water_cap': 22,
        'Direct to Chip': 22
    },

    'WN': {
        'water': [0.7, 7.7, 7.7, 8],
        'elec':  [9.3, 11.6, 11, 11.2],
        'carb':  [10, 10, 10, 10],
        'base': 0,
        'air': 394,
        'water_cap': 287,
        'Direct to Chip': 354
    },

    'WS': {
        'water': [1.8, 15.7, 54, 5.7],
        'elec':  [28, 27, 25, 29],
        'carb':  [398, 197, 300, 300],
        'base': 0,
        'air': 298,
        'water_cap': 300,
        'Direct to Chip': 310
    }
}

# -----------------------------
# Bubble scaling
# -----------------------------
bubble_scale = 4

# -----------------------------
# Figure & Layout
# -----------------------------
fig = plt.figure(figsize=(18, 10))

gs = gridspec.GridSpec(
    2, 14,
    height_ratios=[2, 0.6],
    width_ratios=[1]*13 + [1.8],
    hspace=0.30,
    wspace=0.25
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
        color='#e3e3e3',
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
        color='#ffff00',
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
        color='#ffc0cb',
        alpha=0.75,
        edgecolors='black',
        linewidth=0.8,
        zorder=3
    )

    # -------------------------
    # Direct to Chip Cooling
    # -------------------------
    ax.scatter(
        data[region]['water'][3],
        data[region]['elec'][3],
        s=data[region]['carb'][3] * bubble_scale,
        color='#98fb98',
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
        fontsize=14,
        fontweight='bold',
        pad=10
    )

    # -------------------------
    # Limits
    # -------------------------
    ax.set_xlim(-90, 260)
    ax.set_xticks([0, 100, 250])
    for label in ax.get_xticklabels():
        label.set_rotation(90)
        label.set_fontsize(11)
    
    
    ax.set_ylim(0, 100)

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
            fontsize=16,
            fontweight='bold'
        )
    else:
        ax.set_yticklabels([])

    ax.set_xlabel('')

# -----------------------------
# Shared X Label
# -----------------------------
fig.supxlabel(
    'Total Water Consumption ($10^9$ litres)',
    fontsize=16,
    fontweight='bold',
    y=0.28
)

# -----------------------------
# Carbon Bubble Legend
# -----------------------------
ax_legend = fig.add_subplot(gs[0, 13])
ax_legend.axis('off')

legend_sizes = [
    20 * bubble_scale,
    80 * bubble_scale,
    130 * bubble_scale,
    190 * bubble_scale,
    250 * bubble_scale,
    500 * bubble_scale
]

legend_labels = ['0-10','10-50', '50-100', '100-200', '200-300', '>300']

handles = []

for size, label in zip(legend_sizes, legend_labels):

    handle = ax_legend.scatter(
        [],
        [],
        s=size,
        color='white',
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
    title='Carbon Intensity\n(gr CO₂e / kWh)',
    loc='upper center',
    bbox_to_anchor=(0.9, 1.1),
    frameon=False,
    fancybox=True,
    borderpad=1.4,
    labelspacing=2.6,
    handletextpad=1.5,
    scatterpoints=1
)

legend1.get_title().set_fontsize(16)

ax_legend.add_artist(legend1)

# -----------------------------
# Scenario Color Legend
# -----------------------------
scenario_handles = [
    plt.Line2D([0], [0], marker='o', color='w',
               markerfacecolor='#e3e3e3',
               markeredgecolor='black',
               markersize=10,
               label='Base'),

    plt.Line2D([0], [0], marker='o', color='w',
               markerfacecolor='#ffff00',
               markeredgecolor='black',
               markersize=10,
               label='Air-Cooled'),

    plt.Line2D([0], [0], marker='o', color='w',
               markerfacecolor='#ffc0cb',
               markeredgecolor='black',
               markersize=10,
               label='Water-Cooled'),

    plt.Line2D([0], [0], marker='o', color='w',
               markerfacecolor='#98fb98',
               markeredgecolor='black',
               markersize=10,
               label='Direct to Chip')
]

legend2 = ax_legend.legend(
    handles=scenario_handles,
    loc='lower center',
    bbox_to_anchor=(0.9, -0.42),  
    title='Case Study',
    frameon=False,
    fancybox=True,
    borderpad=1.2,
    labelspacing=1.3,
)

legend2.get_title().set_fontsize(16)

# -----------------------------
# Table
# -----------------------------
ax_table = fig.add_subplot(gs[1, 0:13])
ax_table.axis('off')

cell_text = [
    [data[r]['base'] for r in regions],
    [data[r]['air'] for r in regions],
    [data[r]['water_cap'] for r in regions],
    [data[r]['Direct to Chip'] for r in regions]
]

table = ax_table.table(
    cellText=cell_text,
    rowLabels=[
        'Base',
        'Air-Cooled',
        'Water-Cooled',
        'Direct to Chip'
    ],
    colLabels=regions,
    loc='center',
    cellLoc='center'
)
table._bbox = [0, -0.15, 1, 1]
table.auto_set_font_size(False)

ax_table.text(
    0.55, 0.9,   # x, y
    'Data Centre Capacity (MW)',
    transform=ax_table.transAxes,
    fontsize=14,
    fontweight='bold',
    ha='center'
)

table.scale(1, 2.0)

# -----------------------------
# Table Styling
# -----------------------------
row_colors = {
    1: '#000000',
    2: '#000000',
    3: '#000000',
    4: '#000000'
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
#fig.suptitle(
  #  'Regional Water–Electricity–Carbon Nexus',
   # fontsize=18,
   # fontweight='bold',
   # y=0.98
#)

# -----------------------------
# Show Figure
# -----------------------------
plt.show()