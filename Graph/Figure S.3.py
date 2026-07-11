import matplotlib.pyplot as plt
import numpy as np

plt.rcParams['font.family'] = 'serif'

years = ['2030','2035', '2040','2045', '2050']
categories = ['Electricity', 'H2', 'Heating']

# ======================
# دیتای واقعی (ساختار درست)
# ======================
data = {
    '2030': {
        'Electricity': {
            'Solar': 16,
            'Wind Onshore': 19,
            'Wind Offshore': 28,
            'Battery': 10,
            'Nuclear': 10,
            'H2CCGT': 2.5,
            'CCGT': 33,
            'CCGTCCS': 2,
            'FC': 0,
            'BECCS': 0,
            'Biomass': 3.5,
        },
        'H2': {
            'WE': 0,
            'SMRCCS': 5,
            'ATRCCS': 2,
            'BGCCS': 4
        },
        'Heating': {
            'ASHP': 26,
            'HyBoiler': 13,
            'Gas Boiler': 140
        }
    },
    
    '2035':{
        'Electricity': {
            'Solar': 31,
            'Wind Onshore': 24,
            'Wind Offshore': 43,
            'Battery': 25,
            'Nuclear': 13,
            'H2CCGT': 12,
            'FC': 5,
            'CCGT': 33,
            'CCGTCCS': 7,
            'BECCS': 0,
            'Biomass': 3.5,
        },
        'H2': {
            'WE': 3,
            'SMRCCS': 15,
            'ATRCCS': 12,
            'BGCCS': 12
        },
        'Heating': {
            'ASHP': 86,
            'HyBoiler': 37,
            'Gas Boiler': 67}
        },

    '2040':{
        'Electricity': {
            'Solar': 46,
            'Wind Onshore': 29,
            'Wind Offshore': 58,
            'Battery': 40,
            'Nuclear': 14,
            'H2CCGT': 22,
            'FC': 5,
            'CCGT': 25,
            'CCGTCCS': 18,
            'BECCS': 1,
            'Biomass': 3.5,
        },
        'H2': {
            'WE': 3,
            'SMRCCS': 25,
            'ATRCCS': 22,
            'BGCCS': 22
        },
        'Heating': {
            'ASHP': 127,
            'HyBoiler': 63,
            'Gas Boiler': 22}
        },
    
    
    
    '2045': {
        'Electricity': {
            'Solar': 52,
            'Wind Onshore': 34,
            'Wind Offshore': 58,
            'Battery': 55,
            'Nuclear': 19,
            'H2CCGT': 20,
            'FC': 17,
            'CCGT': 10,
            'CCGTCCS': 20,
           
            'BECCS': 1,
            'Biomass': 3.5,
        },
        'H2': {
            'WE': 3,
            'SMRCCS': 35,
            'ATRCCS': 30,
            'BGCCS': 23
        },
        'Heating': {
            'ASHP': 160,
            'HyBoiler': 80,
            'Gas Boiler': 0
        }
        },

    '2050': {
        'Electricity': {
            'Solar': 65,
            'Wind Onshore': 34,
            'Wind Offshore': 68,
            'Battery': 61,
            'Nuclear': 22,
            'H2CCGT': 30,
            'FC': 17,
            'CCGT': 5,
            'CCGTCCS': 30,
           
            'BECCS': 1,
            'Biomass': 3.5,
        },
        'H2': {
            'WE': 3,
            'SMRCCS': 40,
            'ATRCCS': 45,
            'BGCCS': 25
        },
        'Heating': {
            'ASHP': 182,
            'HyBoiler': 93,
            'Gas Boiler': 0
        }
        }
}



labels_e = ["Solar","Wind Onshore","Wind Offshore","Battery","CCGT","Nuclear","H2CCGT","FC","BECCS","CCGTCCS","Biomass"]
colors_e = ["#FFFF00","#00FF00","#228b22","#00FFFF","#8b0000","#0000FF","#8000FF","#FF00FF","#FF0080","#FF0000","#ffa54f"]

labels_h2 = ["SMRCCS","ATRCCS","BGCCS","WE"]
colors_h2 = ["#6c7b8b", "#9fb6cd", "#96cdcd","#afeeee"]

labels_ht = ["HyBoiler", "ASHP", "Gas Boiler"]
colors_ht = ["#8b5a00", "#cd8500", "#5d4037"] 

colors = {}
colors.update(dict(zip(labels_e, colors_e)))
colors.update(dict(zip(labels_h2, colors_h2)))
colors.update(dict(zip(labels_ht, colors_ht)))


x = np.arange(len(years)) * 2.5
width = 0.4

fig, ax = plt.subplots(figsize=(10,9))

# برای legend جدا
legend_e = {}
legend_h2 = {}
legend_ht = {}


for i, year in enumerate(years):
    for j, cat in enumerate(categories):
        xpos = x[i] + (j - 1) * width * 1.2

        bottom = 0
        for tech, value in data[year][cat].items():
            bar = ax.bar(
                xpos,
                value,
                width,
                bottom=bottom,
                color=colors[tech],
                edgecolor='black',
                linewidth=0.3
            )

            if cat == 'Electricity' and tech not in legend_e:
                legend_e[tech] = bar
            elif cat == 'H2' and tech not in legend_h2:
                legend_h2[tech] = bar
            elif cat == 'Heating' and tech not in legend_ht:
                legend_ht[tech] = bar

            bottom += value


all_positions = []
all_labels = []

for i, year in enumerate(years):
    for j, cat in enumerate(categories):
        xpos = x[i] + (j - 1) * width * 1.3
        all_positions.append(xpos)
        all_labels.append(cat)

ax.set_xticks(all_positions)
ax.set_xticklabels(all_labels, rotation=90,  fontsize=14)

# سال‌ها
for i, year in enumerate(years):
    ax.text(
        x[i],
        -0.2 * ax.get_ylim()[1],
        
        year,
        ha='center',
        va='top',
        fontsize=16,
        fontweight='bold'
    )


leg1 = ax.legend(
    [legend_e[k][0] for k in legend_e],
    legend_e.keys(),
    title='Electricity',
    loc='upper right',
    bbox_to_anchor=(1.28, 0.8),
    fontsize=11,
    frameon=False
)
leg1.get_title().set_fontweight('bold')
leg2 = ax.legend(
    [legend_h2[k][0] for k in legend_h2],
    legend_h2.keys(),
    title='H2', 
    loc='upper right',
    bbox_to_anchor=(1.24, 0.35),
    fontsize=11,
    frameon=False
)
leg2.get_title().set_fontweight('bold')
leg3 = ax.legend(
    [legend_ht[k][0] for k in legend_ht],
    legend_ht.keys(),
    title='Heating',
    loc='upper right',
    bbox_to_anchor=(1.25, 0.15),
    fontsize=11,
    frameon=False
)
leg3.get_title().set_fontweight('bold')
ax.add_artist(leg1)
ax.add_artist(leg2)


ax.set_ylabel('Installed capacity (GW)', fontsize=18,fontweight='bold')

ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)

plt.tight_layout()
plt.show()