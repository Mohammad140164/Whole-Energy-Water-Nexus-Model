import matplotlib.pyplot as plt
import numpy as np
from scipy.interpolate import interp1d

# تنظیم رنگ‌های دلخواه برای هر سناریو
scenario_colors = {
    'Without DC': '#bfbfbf',
    'DC with Air-Cooled': '#e6e600',
    'DC with Water-Cooled': '#ff8fb3',
    'DC with D2C': '#66cc66'
}

years = np.arange(2025, 2051, 5) 
data = {
    'Without DC': [5, 16, 45, 60, 66, 67],
    'DC with Air-Cooled': [5, 18.2, 42, 63.9, 62.7, 63],
    'DC with Water-Cooled': [5, 21, 48.3, 61.5, 63.6, 62.8],
    'DC with D2C': [5, 15, 44, 62.7, 62.5, 60],
}

fig, ax = plt.subplots(figsize=(10, 6))

plt.rcParams["font.family"] = "serif"
plt.rcParams['font.size'] = 12

for scenario, values in data.items():
    years_new = np.linspace(2025, 2050, 100) 
    
    f = interp1d(years, values, kind='cubic')
    values_smooth = f(years_new)

    # استفاده از رنگ دلخواه و ضخامت تعیین شده (بدون تغییر در LineStyle)
    ax.plot(years_new, values_smooth, label=scenario, linewidth=3, color=scenario_colors[scenario])

    # ترسیم نقاط با همان رنگ
    ax.scatter(years, values, s=100, color=scenario_colors[scenario])

ax.set_xlabel('Year', fontsize=15)
ax.set_ylabel('Level of Heat Electrification (%)', fontsize=16)

ax.set_xticks(years)
ax.set_xticklabels(years)

ax.set_yticks(np.arange(0, 81, 20))
ax.set_yticklabels(np.arange(0, 81, 20))

ax.legend(title='Scenario', loc='upper left')

plt.savefig('electrification_scenarios.png')
plt.show()

#%%
import matplotlib.pyplot as plt
import numpy as np
from scipy.interpolate import interp1d

# تنظیمات رنگ
scenario_colors = {
    'Without DC': '#999999',
    'DC with Air-Cooled': '#cccc00',
    'DC with Water-Cooled': '#ff6699',
    'DC with D2C': '#33aa33'
}

years = np.arange(2025, 2051, 5)

# داده‌های شما
data_list = [
    {'Without DC': [5, 16, 45, 60, 66, 67], 'DC with Air-Cooled': [5, 18.2, 42, 63.9, 62.7, 63], 'DC with Water-Cooled': [5, 21, 48.3, 61.5, 63.6, 62.8], 'DC with D2C': [5, 15, 44, 62.7, 62.5, 60]},
    {'Without DC': [0, 7.6, 20, 30, 33, 32], 'DC with Air-Cooled': [0, 11, 29, 37, 39, 37], 'DC with Water-Cooled': [0, 14, 25.7, 34.5, 37, 37], 'DC with D2C': [0, 15, 27.6, 37, 48, 40]},
    {'Without DC': [95, 76, 35, 9.8, 0, 0], 'DC with Air-Cooled': [95, 71, 29, 0, 0, 0], 'DC with Water-Cooled': [95, 65, 26, 4, 0, 0], 'DC with D2C': [95, 70, 28, 0, 0, 0]}
]

y_labels = [
    'Level of Heat Electrification (%)',
    'Level of Heat meet by H2 (%)',
    'Level of Heat meet by Natural Gas (%)'
]

plt.rcParams["font.family"] = "serif"
plt.rcParams['font.size'] = 12

# ایجاد فضای اضافه در بالا با استفاده از subplots_adjust
fig, axes = plt.subplots(3, 1, figsize=(10, 22))
fig.subplots_adjust(top=0.92) 

for i, ax in enumerate(axes):
    data = data_list[i]
    
    ax.grid(True, linestyle='-', which='major', color='gray', alpha=0.2)
    
    for scenario, values in data.items():
        years_new = np.linspace(2025, 2050, 100) 
        f = interp1d(years, values, kind='cubic')
        values_smooth = f(years_new)

        # رسم نمودارها
        ax.plot(years_new, values_smooth, label=scenario, linewidth=3, color=scenario_colors[scenario])
        ax.scatter(years, values, s=100, color=scenario_colors[scenario])

    ax.set_xlabel('Year', fontsize=15)
    ax.set_ylabel(y_labels[i], fontsize=14)
    ax.set_xticks(years)
    ax.set_yticks(np.arange(0, 90, 20))

# اضافه کردن لجند به صورت افقی در بالای اولین نمودار
axes[0].legend(loc='upper center', 
               bbox_to_anchor=(0.5, 1.15), 
               ncol=4, 
               frameon=False, 
               fontsize=12)

plt.tight_layout(rect=[0, 0, 1, 0.99])
plt.savefig('electrification_scenarios_3in1.png', bbox_inches='tight')
plt.show()