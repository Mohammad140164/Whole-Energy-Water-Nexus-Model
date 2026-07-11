import matplotlib.pyplot as plt
import numpy as np
from matplotlib.ticker import MultipleLocator

# ۱. تعریف داده‌ها
years = np.array([2030, 2035, 2040, 2045, 2050])
n_years = len(years)

scenarios = ['Without DC', 'Air-cooled', 'Water-cooled', 'DTC-cooled']
n_scenarios = len(scenarios)


# داده‌های نمونه (قابل جایگزینی)
# امکان وجود مقدار منفی
power_data = np.array([
    [7.5, 14.7, 15.5, 15],   # 2030
    [8.2, 11.8, 14.3, 13.2],   # 2035
    [6.2, 13, 9.3, 14.6],   # 2040
    [11.2, 12.6, 11.28, 14.1],   # 2045
    [7.7, -3, 1, -4]    # 2050
])


hydrogen_data = np.array([
    [-9.7, -9.2, -7.4, -11],   # 2030
    [-14, -13, -13, -14],   # 2035
    [-14, -13, -12, -15],   # 2040
    [-15, -15, -14, -17],   # 2045
    [-17, -6, -10, -6]    # 2050
])


gas_data = np.array([
    [83, 75, 73, 77],   # 2030
    [41, 36, 34, 36],   # 2035
    [14.6, 6, 9.5, 7],   # 2040
    [8.2, 5.3, 5.8, 6],   # 2045
    [5, 7.3, 6, 8]  
])


# Carbon Intensity
carbon_data = np.array([
    [25, 41, 43, 43.3],   # 2030
    [19.1, 24.2, 29.1, 27.6],   # 2035
    [11.4, 21.2, 15, 24.2],   # 2040
    [13.5, 19, 16.7, 21.4],   # 2045
    [10, 0, 0, 0]    # 2050
])


# ۲. ساخت نمودار
fig, ax1 = plt.subplots(figsize=(15, 8))

ax2 = ax1.twinx()



# تنظیم فاصله ستون‌ها
bar_width = 0.14
scenario_gap = 0.08
group_space = 0.65


year_centers = np.arange(n_years) * (
    n_scenarios * (bar_width + scenario_gap)
    + group_space
)



# ۳. رسم ستون‌های تجمعی با پشتیبانی منفی

for i in range(n_scenarios):

    x_pos = year_centers + (
        i - (n_scenarios - 1) / 2
    ) * (bar_width + scenario_gap)



    # برای stacking مثبت و منفی جداگانه
    positive_bottom = np.zeros(n_years)
    negative_bottom = np.zeros(n_years)



    layers = [
        (power_data[:, i], 'Power', '\\\\'),
        (hydrogen_data[:, i], 'Hydrogen', '...'),
        (gas_data[:, i], 'Gas', None)
    ]



    for values, label, hatch in layers:


        # مقادیر مثبت
        pos_values = np.where(values > 0, values, 0)

        ax1.bar(
            x_pos,
            pos_values,
            bar_width,
            bottom=positive_bottom,
            label=label if i == 0 else "",
            facecolor='white',
            edgecolor='black',
            linewidth=1.2,
            hatch=hatch
        )

        positive_bottom += pos_values



        # مقادیر منفی
        neg_values = np.where(values < 0, values, 0)


        ax1.bar(
            x_pos,
            neg_values,
            bar_width,
            bottom=negative_bottom,
            facecolor='white',
            edgecolor='black',
            linewidth=1.2,
            hatch=hatch
        )


        negative_bottom += neg_values




    # Carbon intensity
    ax2.scatter(
        x_pos,
        carbon_data[:, i],
        marker='*',
        s=170,
        color='red',
        linewidth=0.5,
        zorder=10
    )


all_positive = (
    power_data +
    hydrogen_data +
    gas_data
)

y_min = np.min(all_positive)
y_max = np.max(all_positive)


# کمی حاشیه بالا و پایین
ax1.set_ylim(
    y_min - 15,
    y_max + 20
)


# گام محور Y هر 10 واحد
ax1.yaxis.set_major_locator(
    MultipleLocator(10)
)




# ۴. خطوط مرزی بین سال‌ها

for i in range(1, n_years):

    separator_x = (
        year_centers[i-1]
        +
        year_centers[i]
    ) / 2


    ax1.axvline(
        separator_x,
        color='gray',
        linewidth=0.7,
        alpha=0.6
    )





# ۵. محور X

all_ticks = []

for y in year_centers:

    for i in range(n_scenarios):

        all_ticks.append(
            y +
            (
                i - (n_scenarios-1)/2
            ) *
            (bar_width + scenario_gap)
        )



ax1.set_xticks(all_ticks)

ax1.set_xticklabels(
    scenarios * n_years,
    rotation=90,
    fontsize=10
)



# ۶. نمایش سال‌ها

# پیدا کردن پایین‌ترین مقدار برای فاصله متن سال
y_min = ax1.get_ylim()[0]


for i, year in enumerate(years):

    ax1.text(
        year_centers[i],
        y_min - abs(y_min)*0.15 - 15,
        str(year),
        ha='center',
        fontsize=13,
        fontweight='bold'
    )





# ۷. محورهای Y

ax1.set_ylabel(
    'Emission (Mton CO2eq)',
    fontsize=15,
    fontweight='bold'
)


ax2.set_ylabel(
    'Carbon Intensity of Electricity Generation (gr CO2eq/kWh)',
    fontsize=14,
    color='red',
    fontweight='bold'
)


ax2.set_ylim(-2,50)

ax2.tick_params(
    axis='y',
    labelcolor='red'
)





# خط صفر برای خوانایی مقادیر منفی

ax1.axhline(
    0,
    color='black',
    linewidth=1
)





# Grid ظریف





# حذف قاب بالا

ax1.spines['top'].set_visible(False)
ax2.spines['top'].set_visible(False)




# Legend

ax1.legend(
    loc='upper right',
    frameon=True
)





plt.subplots_adjust(
    bottom=0.28,
    left=0.08,
    right=0.9
)



plt.tight_layout()

plt.show()