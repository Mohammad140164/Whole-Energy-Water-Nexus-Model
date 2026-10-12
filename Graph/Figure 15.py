import matplotlib.pyplot as plt
plt.rcParams["font.family"] = "serif"

# داده‌های محور افقی
x = [20, 40, 60, 80, 100]

# داده‌های مربوط به سه شاخص
y_carbon = [0, 30, 43, 55, 73]
y_installation = [0, 8, 24, 34, 48]
y_gas = [705, 850, 961, 1150, 1405]

# ساخت تصویر و محور اصلی سمت چپ
fig, ax1 = plt.subplots(figsize=(10, 6), dpi=200)

# تنظیم فاصله سمت راست برای جا شدن محور سوم
fig.subplots_adjust(right=0.75)

# ایجاد محورهای دوم و سوم سمت راست
ax2 = ax1.twinx()
ax3 = ax1.twinx()

# جابه‌جایی محور سوم به سمت راست
ax3.spines['right'].set_position(('axes', 1.2))

# رنگ‌ها و نمادهای متمایز برای هر شاخص
color1 = 'tab:blue'
color2 = 'tab:green'
color3 = 'tab:red'

# رسم خط اول مربوط به Carbon Capture روی محور سمت چپ
line1 = ax1.plot(
    x,
    y_carbon,
    color=color1,
    marker='o',
    linewidth=2,
    label='Carbon Capture',
)
ax1.set_xlabel('Heat recovery factor(%)', fontsize=12)
ax1.set_ylabel('Carbon Capture (Mton CO₂-eq)', color=color1, fontsize=12)
ax1.tick_params(axis='y', labelcolor=color1)
ax1.set_xticks(x)
ax1.set_xticklabels(['20%', '40%', '60%', '80%', '100%'])

# رسم خط دوم مربوط به Avoided New Installation روی محور دوم سمت راست
line2 = ax2.plot(
    x,
    y_installation,
    color=color2,
    marker='^',
    linewidth=2,
    label='Avoid New Installation',
)
ax2.set_ylabel('Avoid New Installation (GW)', color=color2, fontsize=12)
ax2.tick_params(axis='y', labelcolor=color2)

# رسم خط سوم مربوط به Gas Consumption روی محور سوم سمت راست
line3 = ax3.plot(
    x, y_gas, color=color3, marker='s', linewidth=2, label='Gas Consumption'
)
ax3.set_ylabel('Gas Consumption (PJ)', color=color3, fontsize=12)
ax3.tick_params(axis='y', labelcolor=color3)

# فعال‌سازی خطوط راهنما برای خوانایی بهتر
ax1.grid(True, linestyle='--', alpha=0.5)

# افزودن راهنمای نمودار
lines = line1 + line2 + line3
labels = [l.get_label() for l in lines]
ax1.legend(lines, labels, loc='upper left')

plt.show()