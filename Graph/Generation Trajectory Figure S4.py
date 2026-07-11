import matplotlib.pyplot as plt
import numpy as np

years = [2030, 2035, 2040, 2045, 2050]

data = {
    "CCGT": [21.42, 12.44, 6.55, 15.72, 0.00],
    "CCGTCCS": [12.27, 40.16, 44.69, 60.23, 78.23],
    "Nuclear": [77.74, 90.97, 92.77, 103.01, 125.01],
    "Biomass": [0.01, 0.03, 0.02, 0.03, 0.03],
    "Hydro": [5.80, 5.80, 5.80, 5.80, 5.80],
    "BECCS": [1.97, 0.69, 0.80, 0.91, 0.71],
    "FC": [0.00, 4.07, 12.59, 0.00, 1.59],
    "H2CCGT": [0.03, 0.41, 8.59, 1.87, 0.87],
    "Wind Offshore": [100.56, 157.35, 214.47, 214.47, 260.47],
    "Wind Onshore": [58.78, 73.41, 89.34, 101.74, 101.74],
    "Solar": [22.82, 43.01, 63.44, 70.47, 78.47]
}

labels_e = [
    "CCGT", "CCGTCCS", "Nuclear", "Biomass", "Hydro", 
    "BECCS", "FC", "H2CCGT", "Wind Offshore", "Wind Onshore", "Solar"
]

colors_e = [
    "#8b0000", "#FF0000", "#00008B", "#ffa54f", "#1E90FF", 
    "#FF0080", "#FF00FF", "#8000FF", "#228b22", "#00FF00", "#FFFF00"
]

y_data = np.array([data[label] for label in labels_e])

fig, ax = plt.subplots(figsize=(12, 8))

ax.stackplot(years, y_data, labels=labels_e, colors=colors_e, edgecolor='black', linewidth=0.5)

# تنظیم دقیق سال‌ها در محور ایکس
ax.set_xticks(years)

# افزایش اندازه فونت اعداد محورها
ax.tick_params(axis='both', which='major', labelsize=14)

ax.set_xlabel("Year", fontsize=16)
ax.set_ylabel("Generation (TWh)", fontsize=16)
ax.legend(loc='upper left', bbox_to_anchor=(1, 1))
ax.margins(x=0)

plt.tight_layout()
plt.show()