import numpy as np
import matplotlib.pyplot as plt

plt.rcParams["font.family"] = "serif"

countries = ['EA', 'EM', 'NE', 'NO', 'NT', 'NW', 'SC', 'SE', 'SO', 'SW', 'WM', 'WN', 'WS']
n = len(countries)

# سناریوهای قبلی
scenario_1 = [0.34, 0.91, 0.67, 0.9, 0.35, 0.68, 1, 1, 0.12, 1, 0.165, 1, 1]
scenario_2 = [0.43, 0.92, 0.77, 0.76, 0.44, 0.76, 1, 1, 0.2, 1, 0.32, 1, 1]
scenario_3 = [0.57, 0.91, 0.29, 0.92, 0.31, 0.92, 1, 1, 0.24, 1, 0.16, 1, 1]

scenario_0 = [0.66, 0.82, 0.57, 0.4, 0.08, 0.7, 1, 1, 0.62, 1, 0,1, 0.44] 

def close(values):
    return np.concatenate([values, [values[0]]])

s0 = close(np.array(scenario_0))
s1 = close(np.array(scenario_1))
s2 = close(np.array(scenario_2))
s3 = close(np.array(scenario_3))

angles = np.linspace(0, 2 * np.pi, n, endpoint=False)
angles = close(angles)

fig = plt.figure(figsize=(8, 8))
ax = fig.add_subplot(111, polar=True)
ax.set_theta_offset(np.pi / 2)
ax.set_theta_direction(-1)
# تغییر رنگ به خاکستری خیلی روشن و کاهش شفافیت برای کمرنگ‌تر شدن
#ax.grid(color="#dddddd", linestyle="-", linewidth=0.5, alpha=1)
# ترتیب رسم برای اینکه رنگ‌ها روی هم تداخل بدی نداشته باشند
# پیشنهاد: سناریوهای بزرگتر را اول رسم کنید یا از alpha پایین استفاده کنید
ax.fill(angles, s3, color="#00ff00", alpha=0.2, label="Availability 70%")
ax.plot(angles, s3, color="#00ff00", linewidth=2)

ax.fill(angles, s2, color="#838b8b", alpha=0.2, label="Availability 80%")
ax.plot(angles, s2, color="#838b8b", linewidth=2)

ax.fill(angles, s1, color="#0000ff", alpha=0.2, label="Availability 90%")
ax.plot(angles, s1, color="#0000ff", linewidth=2)

# اضافه کردن سناریوی جدید با رنگ قرمز (مثلا)
ax.fill(angles, s0, color="#d62728", alpha=0.3, label="Availability 100%")
ax.plot(angles, s0, color="#d62728", linewidth=2)

ax.set_xticks(angles[:-1])
ax.set_xticklabels(countries, fontsize=14)
ax.set_ylim(0, 1.1)

#plt.legend(loc="upper right", bbox_to_anchor=(1.3, 1.1), frameon=False)
plt.tight_layout()
plt.show()


#%%
import numpy as np
import matplotlib.pyplot as plt

plt.rcParams["font.family"] = "serif"

countries = ['EA', 'EM', 'NE', 'NO', 'NT', 'NW', 'SC', 'SE', 'SO', 'SW', 'WM', 'WN', 'WS']
n = len(countries)

# سناریوهای قبلی
scenario_1 = [0.65, 0.08, 0.32, 0.09, 0.65, 0.31, 0, 0, 0.87, 0, 0.83, 0, 0]
scenario_2 = [0.56,0.08, 0.23, 0.23, 0.55, 0.23, 0, 0, 0.8, 0, 0.67, 0, 0]
scenario_3 = [0.42, 0.08, 0.7, 0.08, 0.68, 0.08, 0, 0, 0.53, 0, 0.83, 0, 0]

scenario_0 = [0.33, 0.17, 0.43, 0.6, 0.92, 0.3, 0, 0, 0.37,0, 1, 0,  0.55] 

def close(values):
    return np.concatenate([values, [values[0]]])

s0 = close(np.array(scenario_0))
s1 = close(np.array(scenario_1))
s2 = close(np.array(scenario_2))
s3 = close(np.array(scenario_3))

angles = np.linspace(0, 2 * np.pi, n, endpoint=False)
angles = close(angles)

fig = plt.figure(figsize=(8, 8))
ax = fig.add_subplot(111, polar=True)
ax.set_theta_offset(np.pi / 2)
ax.set_theta_direction(-1)
# تغییر رنگ به خاکستری خیلی روشن و کاهش شفافیت برای کمرنگ‌تر شدن
#ax.grid(color="#dddddd", linestyle="-", linewidth=0.5, alpha=1)
# ترتیب رسم برای اینکه رنگ‌ها روی هم تداخل بدی نداشته باشند
# پیشنهاد: سناریوهای بزرگتر را اول رسم کنید یا از alpha پایین استفاده کنید
ax.fill(angles, s3, color="#00ff00", alpha=0.2, label="Availability 70%")
ax.plot(angles, s3, color="#00ff00", linewidth=2)

ax.fill(angles, s2, color="#838b8b", alpha=0.2, label="Availability 80%")
ax.plot(angles, s2, color="#838b8b", linewidth=2)

ax.fill(angles, s1, color="#0000ff", alpha=0.2, label="Availability 90%")
ax.plot(angles, s1, color="#0000ff", linewidth=2)

# اضافه کردن سناریوی جدید با رنگ قرمز (مثلا)
ax.fill(angles, s0, color="#d62728", alpha=0.3, label="Availability 100%")
ax.plot(angles, s0, color="#d62728", linewidth=2)

ax.set_xticks(angles[:-1])
ax.set_xticklabels(countries, fontsize=14)
ax.set_ylim(0, 1.1)

plt.legend(loc="upper right", bbox_to_anchor=(1.3, 1.1), frameon=False, ncol=4)
plt.tight_layout()
plt.show()