
import pandas as pd
import matplotlib.pyplot as plt
plt.rcParams["font.family"] = "serif"
df = pd.read_excel('Energy Dispatch.xlsx')

tech_colors = {
    "Nuclear": "#0000FF", "Hydro": "#ADD8E6", "CCGTCCS": "#FF0000",
    "CCGT": "#8b0000", "Biomass": "#FF8C00", "BECCS": "#FF0080",
    "H2CCGT": "#8000FF", "FC": "#FF00FF", "WindOn": "#00FF00",
    "WindOff": "#228b22", "Solar": "#FFFF00", "Battery_Dis": "#eedfcc",
    "Exchange": "#A9A9A9", "Battery_Ch": "#00CED1"
}

pos_layers = ["Nuclear", "Hydro", "CCGTCCS", "CCGT", "Biomass", 
              "BECCS", "H2CCGT", "FC", "WindOn", "WindOff", "Solar", "Battery_Dis"]
neg_layers = ["Battery_Ch", "Exchange"] 

scenarios = ["Without DC", "Air-Cooled", "Water-Cooled", "D2C Cooling"]
seasons = ["Winter", "Summer"]

fig, axes = plt.subplots(2, 4, figsize=(22, 12), sharex=False, sharey=False)

for i, season in enumerate(seasons):
    for j, scenario in enumerate(scenarios):
        ax = axes[i, j]
        subset = df[(df['Season'] == season) & (df['Scenario'] == scenario)].sort_values('Hour').copy()
        
        if subset.empty:
            ax.text(0.5, 0.5, 'No Data', ha='center', va='center')
            continue
            
        subset['Exchange_Pos'] = subset['Exchange'].clip(lower=0)
        subset['Exchange_Neg'] = subset['Exchange'].clip(upper=0)
        
        y_pos = [subset[tech] for tech in pos_layers] + [subset['Exchange_Pos']]
        y_neg = [subset['Battery_Ch'], subset['Exchange_Neg']]
        
        ax.stackplot(subset['Hour'], y_neg, 
                     colors=[tech_colors['Battery_Ch'], tech_colors['Exchange']])
        
        ax.stackplot(subset['Hour'], y_pos, 
                     colors=[tech_colors.get(t, 'gray') for t in pos_layers] + [tech_colors['Exchange']])
        
        ax.plot(subset['Hour'], subset['Demand'], color='black', linewidth=2, label='Demand')
        
        ax.set_title(f"{scenario} - {season}", fontsize=11)
        ax.grid(True, axis='y', linestyle='--', alpha=0.3)
        
        if j == 0: ax.set_ylabel('Energy Dispatch (GWh)', fontsize=16)
        if i == 1: ax.set_xlabel('Hour')

handles = [plt.Rectangle((0,0),1,1, color=tech_colors[t]) for t in pos_layers + neg_layers]
labels = pos_layers + neg_layers
fig.legend(handles, labels, loc='upper center', bbox_to_anchor=(0.5, 0.05), 
           ncol=14, fontsize='small', frameon=False) 

plt.tight_layout(rect=[0, 0.05, 1, 1])
plt.show()