import matplotlib.pyplot as plt
import numpy as np

# -----------------------------
# Electricity
# -----------------------------

labels_power = [
    "Solar","Wind Onshore","Wind Offshore","Battery",
    "Nuclear","H2CCGT","FC","CCGTCCS","CCGT","BECCS"
]

power_values = [89, 104, 290, 46, 89, 6, 1, 75, 12, 6]

power_colors = [
    "#FFFF00","#00FF00","#228b22","#00FFFF",
    "#0000FF","#8000FF","#FF00FF","#FF0080","#FF0000"
]

# -----------------------------
# Hydrogen
# -----------------------------

labels_h2 = [
    "SMRCCS","ATRCCS","BGCCS","WE"
]

h2_values = [9, 150, 27, 0]

h2_colors = [
    "#6c7b8b",
    "#9fb6cd",
    "#afeeee",
    "#66cdaa"
]

# -----------------------------
# Figure
# -----------------------------

fig, ax = plt.subplots(figsize=(2.2, 4))

x_power = 0
x_h2 = 0.3

# Electricity stack
bottom = 0
for v, c in zip(power_values, power_colors):
    ax.bar(
        x_power,
        v,
        bottom=bottom,
        width=0.15,
        color=c,
        edgecolor='none'
    )
    bottom += v

# Hydrogen stack
bottom = 0
for v, c in zip(h2_values, h2_colors):
    ax.bar(
        x_h2,
        v,
        bottom=bottom,
        width=0.15,
        color=c,
        edgecolor='none'
    )
    bottom += v

# -----------------------------
# Formatting
# -----------------------------

ax.set_xticks([x_power, x_h2])
ax.set_xticklabels(["Elec", "H2"])

ax.set_ylabel("TWh", fontsize=12)
ax.tick_params(axis='y', labelsize=10)
ax.tick_params(axis='x', labelsize=10)
# remove top/right box
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)

# optional: cleaner look
#ax.grid(axis="y", alpha=0.25)

plt.tight_layout()
plt.show()


#%%
import matplotlib.pyplot as plt
import numpy as np

# -------------------
# Data
# -------------------

water_availability = np.array([0.70, 0.75, 0.80, 0.85, 0.90, 0.95, 1.00])
costs = np.array([1150, 805, 654, 609, 570, 545, 541])

# -------------------
# Plot style
# -------------------

plt.rcParams["font.family"] = "serif"
plt.rcParams["font.size"] = 14

fig, ax = plt.subplots(figsize=(10, 8))

# Pareto curve
ax.plot(
    water_availability,
    costs,
    marker='o',
    color='black',
    linewidth=2.5,
    markersize=8,
    markerfacecolor='white',
    markeredgecolor='black',
    markeredgewidth=1.8
)

# Dashed projection lines to axes
for x, y in zip(water_availability, costs):
    # Vertical line to x-axis
    ax.vlines(
        x, ymin=min(costs), ymax=y,
        colors='gray',
        linestyles=':',
        linewidth=0.8,
        alpha=0.8
    )

    # Horizontal line to y-axis
    ax.hlines(
        y, xmin=min(water_availability), xmax=x,
        colors='gray',
        linestyles=':',
        linewidth=0.8,
        alpha=0.8
    )

ax.set_xlim(0.68, 1.02)

# Labels
ax.set_xlabel("Water Availability (%)", fontsize=20)
ax.set_ylabel("Total Cost (£ b)", fontsize=20)

# X-axis ticks as percentages
ax.set_xticks(water_availability)
ax.set_xticklabels(
    [f"{int(x*100)}%" for x in water_availability],
    fontsize=16
)

# Remove top and right borders
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)

# Thicker remaining borders
ax.spines['left'].set_linewidth(1.2)
ax.spines['bottom'].set_linewidth(1.2)

# Tick formatting
ax.tick_params(
    axis='both',
    which='major',
    labelsize=16,
    direction='out',
    length=6,
    width=1.2
)

# Optional: add some margin around data
ax.margins(x=0.03)

plt.tight_layout()
plt.show()
