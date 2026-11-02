"""
Make_Figure_Data.py - prints the data arrays of Figure 11 (emission trajectories and electricity carbon intensity) and the regional
electricity demand / carbon intensity of Figure 6 directly from the 'Detail_Long' sheet of the result workbooks, in the format of your
Figure_11.py / Figure_6.py, so that nothing has to be typed by hand.

'Detail_Long' is written by the updated model scripts (per-year, per-region capacity, generation, heat, demand and emissions). It is created
when the last rolling-horizon step of each case is solved again (delete the .pkl result files of the cache, keep the ckpt_*.pkl files).

Usage:  python Make_Figure_Data.py
"""
import pandas as pd, numpy as np

WORKBOOKS = ["Water_Pareto_Results.xlsx", "Water_Pareto_Results1.xlsx"]        # <- workbooks that contain the four cases (edit)
CASES = {"Without DC": "Base_none", "Air-cooled": "Pareto_air_f100", "Water-cooled": "Pareto_water_f100", "D2C-cooled": "Base_liquid"}
YEARS = [2030, 2035, 2040, 2045, 2050]
H2_TECHS = {"SMRCCS", "ATRCCS", "BGCCS", "WE"}                                  # hydrogen producers (excluded from electricity generation)
REGIONS = ['EA', 'EM', 'NE', 'NO', 'NT', 'NW', 'SC', 'SE', 'SO', 'SW', 'WM', 'WN', 'WS']

D = pd.concat([pd.read_excel(w, sheet_name="Detail_Long") for w in WORKBOOKS if w], ignore_index=True)
D = D.drop_duplicates(subset=["case", "year", "region", "metric", "technology"])

def get(case, year, metric, technology=None, region=None):
    q = D[(D.case == case) & (D.year == year) & (D.metric == metric)]
    if technology is not None: q = q[q.technology == technology]
    if region is not None: q = q[q.region == region]
    return q["value"].sum()

power, hydrogen, gas, carbon, total = [], [], [], [], []
for y in YEARS:
    rp, rh, rg, rc, rt = [], [], [], [], []
    for sc, c in CASES.items():
        ee = get(c, y, "sector_emissions_MtCO2", "Ee", "GB"); eh = get(c, y, "sector_emissions_MtCO2", "Eh", "GB"); eg = get(c, y, "sector_emissions_MtCO2", "Eg", "GB")
        gen = D[(D.case == c) & (D.year == y) & (D.metric == "generation_TWh") & (~D.technology.isin(H2_TECHS))]["value"].sum()
        em = get(c, y, "power_emissions_MtCO2")
        rp.append(ee); rh.append(eh); rg.append(eg); rc.append(max(1000.0 * em / gen, 0.0) if gen > 0 else 0.0); rt.append(get(c, y, "total_net_emissions_MtCO2"))
    power.append(rp); hydrogen.append(rh); gas.append(rg); carbon.append(rc); total.append(rt)

def block(name, rows, nd=1):
    print("%s = np.array([" % name)
    for y, r in zip(YEARS, rows): print("    [%s],   # %d" % (", ".join("%.*f" % (nd, v) for v in r), y))
    print("])\n")
print("# ---------- paste into Figure_11.py (scenario order: %s) ----------" % ", ".join(CASES))
block("power_data", power); block("hydrogen_data", hydrogen); block("gas_data", gas); block("carbon_data", carbon)
print("# check: power + hydrogen + gas should equal the net emissions of the run (DAC excluded):")
for y, p, h, g, t_ in zip(YEARS, power, hydrogen, gas, total): print("#", y, ["%.2f" % (a + b + c) for a, b, c in zip(p, h, g)], "vs", ["%.2f" % v for v in t_])

# ---------- Figure 6: regional electricity demand and carbon intensity in 2050 (order: Base, Air, Water, D2C) ----------
print("\n# ---------- Figure 6 (2050): 'elec' = regional electricity demand (TWh), 'carb' = regional carbon intensity (g CO2/kWh) ----------")
for r in REGIONS:
    e = [get(c, 2050, "electricity_demand_TWh", "total", r) for c in CASES.values()]
    k = [get(c, 2050, "carbon_intensity_gCO2_per_kWh", "power", r) for c in CASES.values()]
    print("    '%s': {'elec': %s, 'carb': %s}," % (r, [round(float(v), 1) for v in e], [round(float(v), 1) for v in k]))
