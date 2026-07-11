import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

# List of technologies and their hex colors
# Added a placeholder color for BECCS since it was missing in your original list
tech_data = [
    ("Solar", "#FFFF00"),
    ("Wind Onshore", "#00FF00"),
    ("Wind Offshore", "#228B22"),
    ("Battery", "#00FFFF"),
    ("Nuclear", "#0000FF"),
    ("H2CCGT", "#8000FF"),
    ("FC", "#FF00FF"),
    ("CCGTCCS", "#FF0080"),
    ("CCGT", "#FF0000"),
    ("BECCS", "#ff8c00"),
    ("SMRCCS", "#6C7B8B"),
    ("ATRCCS", "#9FB6CD"),
    ("BGCCS", "#AFEEEE"),
    ("WE", "#66CDAA")
]

fig, ax = plt.subplots(figsize=(2, 6))
ax.axis("off")

# Create handles using the tech_data list
handles = [mpatches.Patch(color=c, label=l) for l, c in tech_data]

# Add the legend with the title
ax.legend(
    handles=handles,
    title="Technology",
    loc="center",
    frameon=False,
    fontsize=12,
    title_fontsize=14
)

plt.tight_layout()
plt.show()