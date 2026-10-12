import matplotlib.pyplot as plt
import numpy as np

plt.rcParams['font.family'] = 'serif'

scenarios = ['Base Case', 'Case 1', 'Case 2', 'Case 3']
electricity = [22250, 22270, 22290, 22310]  
water = [0, 0, 0, 0]          

avg_temps = ['10.65 °C', '10.96 °C', '11.28 °C', '11.58 °C']
max_temps = ['29.17 °C', '31.03 °C', '33.13 °C', '35.14 °C']

x = np.arange(len(scenarios))
width = 0.35 

fig, ax1 = plt.subplots(figsize=(8, 6), dpi=200)

color_bar = '#999999'
edge_bar = '#000000'
bars = ax1.bar(x, electricity, width, label='Electricity Consumption', 
               color=color_bar, edgecolor=edge_bar, linewidth=1, zorder=3)

ax1.set_ylabel('Annual Electricity Consumption (GWh)', fontsize=12, labelpad=10)
ax1.set_ylim(22200, 22350)
ax1.tick_params(axis='y', labelsize=10)
ax1.set_xticks(x)
ax1.set_xticklabels(scenarios, fontsize=10)

ax2 = ax1.twinx()
color_line = '#0066cc'
line = ax2.plot(x, water, color=color_line, linewidth=2.5, marker='o', 
                markersize=10, markerfacecolor='red', markeredgecolor='red', 
                label='Water Consumption', zorder=4)

ax2.set_ylabel('Annual Water Consumption (million Litre)', color=color_line, fontsize=12, labelpad=10)
ax2.set_ylim(40, 90)
ax2.tick_params(axis='y', labelcolor=color_line, labelsize=10)

for i in range(len(scenarios) - 1):
    ax1.axvline(x=i + 0.5, color='#999999', linestyle='--', linewidth=0.8, zorder=1)

for i in range(len(scenarios)):
    text_str = f'Avg: {avg_temps[i]}\nMax: {max_temps[i]}'
    ax1.text(x[i], 22350, text_str, ha='center', va='bottom', fontsize=10)


lines_1, labels_1 = ax1.get_legend_handles_labels()
lines_2, labels_2 = ax2.get_legend_handles_labels()
ax1.legend(lines_1 + lines_2, labels_1 + labels_2, loc='upper center', 
           bbox_to_anchor=(0.5, -0.04), ncol=2, frameon=False, fontsize=11)

ax1.spines['top'].set_visible(False)
ax2.spines['top'].set_visible(False)
ax1.set_axisbelow(True)
ax1.yaxis.grid(True, linestyle='-', alpha=0.3, color='#cccccc')

#plt.tight_layout()
plt.show()