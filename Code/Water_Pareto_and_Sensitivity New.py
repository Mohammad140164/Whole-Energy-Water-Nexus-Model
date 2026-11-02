#%%
# =====================================================================================
#  GB DATA-CENTRE ENERGY-WATER NEXUS MODEL  -  INTEGRATED SCRIPT (corrected direct DC water)
#
#  What this script does
#   1.  Builds your original Pyomo model (unchanged except where marked  ### PATCH ###).
#   2.  FIXES the direct data-centre water:  Water_DC [L/h] = CapDC [MW IT] x Profile x WUE [L/kWh] x 1000 [kWh/MWh]
#       (the original equation was missing the x1000 MW->kW conversion).
#   3.  Adds a cooling switch ('air' | 'water' | 'liquid') - the original code was hard-wired to 'liquid' (D2C).
#   4.  Adds the regional water-availability constraint  TotalWater[g,t] <= factor x unconstrained TotalWater[g,t]
#       (Pareto / water-scarcity analysis, air-cooled and water-cooled only).
#   5.  Adds the heat-pump / hydrogen-boiler / renewable-build sensitivity (reviewer 1, comment 6).
#   6.  Saves every key number to Excel (one row per run + data sheets to redraw Fig. 8 and Fig. 9).
#
#  How to run:   python Water_Pareto_and_Sensitivity.py
#   - First run with SMOKE_TEST = True (about 15 min) to check that everything works with your Gurobi licence.
#   - Results are cached after every run (folder results_water/cache) so a stopped job RESUMES where it ended.
#   - Put this script, 'Whole UK 5 year.xlsx' and 'Cooling.xlsx' in the same folder (or change DATA_DIR).
# =====================================================================================
import os
import sys
import time
import pickle
import traceback
import pandas as pd
import numpy as np

# ------------------------------------------------------------------------------------
#  USER SETTINGS  (edit here)
# ------------------------------------------------------------------------------------
try:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
except NameError:                       # running in an interactive cell
    BASE_DIR = os.getcwd()

DATA_DIR = BASE_DIR                                  # folder with the Excel input files
OUT_DIR_NAME = "results_water1"                      # <-- folder for ALL outputs (cache, case workbooks, master workbook).
                                                     #     Keep the name of your existing folder to continue/reuse finished runs.
OUT_DIR = os.path.join(BASE_DIR, OUT_DIR_NAME)
os.makedirs(os.path.join(OUT_DIR, "cache"), exist_ok=True)

SMOKE_TEST = False       # True: one short test solve (first planning step only) to check the workflow
ROLLING = True           # True: rolling horizon with look-ahead (see ROLL_STEP / LOOKAHEAD below)
                         # False: monolithic (single solve, hl = 6) as in the uploaded script

RUN_BASELINES = False     # Table-2-style baselines: Without DC, air-cooled, water-cooled, D2C (liquid)
BASE_COOLINGS = ["none", "air", "water", "liquid"]
RUN_PARETO = True        # water-availability Pareto analysis (air-cooled and water-cooled only)
RUN_SENSITIVITY = True   # heat-pump / hydrogen-boiler / renewable sensitivity
RUN_MONOLITHIC = False   # rolling-horizon vs monolithic comparison (each monolithic run can take > 24 h) - optional
MONO_COOLINGS = ["none", "air", "water", "liquid"]

PARETO_COOLINGS = ["air", "water"]                       # <- air and water cooling only
PARETO_FACTORS = [1.00, 0.95, 0.90, 0.85, 0.80, 0.75, 0.70]   # fraction of unconstrained regional water
# NOTE: 100 % = unconstrained run. Lower factors are solved in this order; the loop stops at the first infeasible one.

# Sensitivity (reviewer 1, comment 6).  'none' = scenario without data centres, 'liquid' = D2C.
# Change this line to ["none", "water"] or ["none", "air"] if you prefer another comparison.
SENS_COOLINGS = ["none", "liquid"]
SENS_CASES = {            # name : multipliers applied to the input data
    "Base":                 dict(),
    "ASHP capex -20%":      dict(ashp_mult=0.8),
    "ASHP capex +20%":      dict(ashp_mult=1.2),
    "H2 production capex -25%": dict(h2prod_mult=0.75),
    "H2 production capex +25%": dict(h2prod_mult=1.25),
    "Renewable build-out 100% of build rate": dict(ren_min_frac=1.0),
}

# Solver settings (identical to the uploaded script - keep identical for ALL runs for consistency)
THREADS = 30
MIPGAP = 0.01           # use the SAME value for every run (cost differences between configurations are only meaningful if the gaps are small and equal)
TIME_LIMIT = None        # seconds per solve (None = no limit)
SOLVER_TEE = True        # print the Gurobi log to the screen

COST_DIV = 1e9           # objective is in GBP -> divide by 1e9 for GBP billion.
                         # CHECK: the first run prints 'Objective (raw)'. If it is ~5e11 keep 1e9; if it is ~5e2 set 1.

HL_MAX = 6               # last planning step (t = 6 = 2050)
YEAR_LABEL_OVERRIDE = {}  # e.g. {5: 2050} if you decide to label the last step as 2050 (default labels: t5 = 2045, t6 = 2050)
HL_INIT = 2 if ROLLING else HL_MAX
if SMOKE_TEST:
    HL_MAX = 2
    HL_INIT = 2
    MIPGAP = 0.30
    TIME_LIMIT = 900
    PARETO_FACTORS = [1.00, 0.90]
    PARETO_COOLINGS = ["air"]
    SENS_COOLINGS = ["none"]
    SENS_CASES = {"Base": dict()}

# ---- Rolling-horizon diagnostics / options (added) ----
# Rolling horizon with LOOK-AHEAD (idea taken from RollingHorizon_TSP.gms):
#   at every iteration the next ROLL_STEP periods are FIXED (control periods) while LOOKAHEAD further periods are optimised
#   together with them but NOT fixed (prediction horizon = fixed periods + look-ahead).  In the GAMS file PH = FP + 2, LP = 2.
#   LOOKAHEAD = 0  -> myopic (previous script; step 6 became infeasible because earlier steps could not anticipate 2050)
#   LOOKAHEAD = 1  -> 10-year foresight,  LOOKAHEAD = 2 -> 15-year foresight, 4 -> monolithic.
#   RELAX_LOOKAHEAD_INTEGERS: integer / binary variables of the look-ahead periods are relaxed to continuous (like the
#   relaxed R-variables of the GAMS file) - this makes the look-ahead solves much cheaper; the control periods keep integers.
ROLL_STEP = 1
LOOKAHEAD = 1
RELAX_LOOKAHEAD_INTEGERS = True
ADAPTIVE_LOOKAHEAD = True  # if an iteration is infeasible: go back one checkpoint, widen the look-ahead by one period and retry
MAX_LOOKAHEAD = 4          # (4 = monolithic for periods 2..6). The look-ahead actually used is saved in Solve_Log / Key_Numbers.
                           # All cases should end up with the same look-ahead: check 'Formulation_Check' in the Excel file.
MASTER_XLSX_NAME = "Water_Pareto_Results.xlsx"   # master workbook, rebuilt after EVERY finished run
SOFT_RESERVE_MARGIN = True  # True: the reserve-margin constraint (firm capacity >= 1.088 x peak demand) may be violated at a cost.
                           # Use it to test whether the infeasibility of the data-centre cases comes from capacity adequacy at the
                           # last step; the shortfall is reported (reserve_shortfall_GW in Key_Numbers / Annual_Flows).
                           # If used, use it for ALL cases (it is part of the cache name) and say so in the methods.
RESERVE_PENALTY = 1.0e6    # GBP per MW of shortfall per period (about GBP 1000/kW, comparable to the cost of firm capacity)
RETRY_FAILED = True        # True: a case that is cached as failed/infeasible is tried again (e.g. with a wider look-ahead)
EXCEL_ONLY = False         # True: only rebuild the master workbook from the cached runs and stop (no solving)
DIAGNOSE_RELAXED = False # True: at the LAST step only, relax all integer variables (LP relaxation) and stop.
                         # An LP is proven infeasible in minutes and its IIS (.ilp) is written quickly. Results are NOT saved.
                         # Use this when the last step is infeasible and the MILP search takes hours.
DIAGNOSE_FEASRELAX = False  # True: instead of the normal run, solve ONE feasibility-relaxation LP of the last step
                         # (needs the step-5 checkpoint). It reports which constraints must be violated, and by how much -
                         # much faster than the IIS, which can take days on a model with ~1 million constraints.
DIAGNOSE_COOLING = "air" # cooling case used for the diagnosis ('air' | 'water' | 'liquid')
DIAGNOSE_FIX_STEP = None # periods up to this t are fixed from the checkpoint (None = HL_MAX-1).  0 = nothing fixed:
                         # the whole horizon is checked as one LP -> tells whether the case is infeasible by itself (structural)
WRITE_IIS = False        # True: ask Gurobi for the IIS (.ilp) when a step is infeasible. Leave False for this model:
                         # with ~1 million constraints it can run for days. Use DIAGNOSE_FEASRELAX instead.
SAVE_CHECKPOINTS = True  # saves the fixed decisions after every rolling step -> a stopped/infeasible run can be resumed
                         # (e.g. re-solve only the 2050 step after changing something)

KWH_PER_MWH = 1000.0     ### PATCH ###  unit conversion that was missing in the direct-DC-water equation

DEFAULT_CFG = dict(cooling='liquid',     # 'air' | 'water' | 'liquid'(D2C)
                   dc_scale=1.0,         # 0.0 -> scenario without data centres
                   water_eps=None,       # dict {(region, t): limit in ML/yr} -> regional water-availability constraint
                   ashp_mult=1.0, hyboiler_mult=1.0, h2prod_mult=1.0,   # capex multipliers (sensitivity)
                   ren_min_frac=0.0,     # renewable build-out requirement as a fraction of the build rate (sensitivity)
                   soft_reserve=SOFT_RESERVE_MARGIN, reserve_penalty=RESERVE_PENALTY)
WATER_TECHS = ['FC', 'H2CCGT', 'Nuclear', 'OCGT', 'CCGTCCS', 'BECCS', 'Biomass', 'CCGT',
               'SMRCCS', 'ATRCCS', 'BGCCS', 'WE']      # technologies with a water factor (as in the WaterCon constraint)


def find_file(*names):
    """Return the first existing file among 'names' in DATA_DIR (handles spaces/underscores in file names)."""
    for n in names:
        p = os.path.join(DATA_DIR, n)
        if os.path.exists(p):
            return p
    raise FileNotFoundError("None of these files found in %s: %s" % (DATA_DIR, names))


# ------------------------------------------------------------------------------------
#  DATA LOADING  (same ranges as the uploaded script)
# ------------------------------------------------------------------------------------
file_path = find_file("Whole UK 5 year.xlsx", "Whole_UK_5_year.xlsx")
excel_data = pd.ExcelFile(file_path, engine='openpyxl')

Sets_data = excel_data.parse('Sets')
TechData_data = excel_data.parse('TechData')
HeatTech_data = excel_data.parse('HeatTech')
CostTech_data = excel_data.parse('CostTech')
General_data = excel_data.parse('General')
Regions_data = excel_data.parse('Regions')
Trans_data = excel_data.parse('Trans_Inter')
year_data = excel_data.parse('Calculations')

Distances_data = excel_data.parse('Distances')
General_data = excel_data.parse('General')
Emissions_data = excel_data.parse('Emissions')
Cluster_data = excel_data.parse('ClusteredDataSTOR')
Biomass_data = excel_data.parse('Biomass')
DAC_data = excel_data.parse('DAC')

Reservoir_data = excel_data.parse('CO2Reservoirs')
Pipelines_data = excel_data.parse('Pipelines')

df_eta = excel_data.parse('TechData', header=None, usecols="A:G", skiprows=101, nrows=24)
df_BR = excel_data.parse('TechData', header=None, usecols="A:G", skiprows=153, nrows=29)
df_cc_Heat = excel_data.parse('HeatTech', header=None, usecols="A:G", skiprows=2, nrows=5)
df_eta_Heat = excel_data.parse('HeatTech', header=None, usecols="A:G", skiprows=11, nrows=5)
df_cc_fix = excel_data.parse('CostTech', header=None, usecols="A:G", skiprows=2, nrows=24)
df_oc_fix = excel_data.parse('CostTech', header=None, usecols="L:R", skiprows=2, nrows=24)
df_LandAvailability = excel_data.parse('LandAvailability', header=None, usecols="A:N", skiprows=2, nrows=3)
df_NUint = excel_data.parse('InitCap', header=None, usecols="A:N", skiprows=2, nrows=4)
df_Capinit = excel_data.parse('InitCap', header=None, usecols="A:N", skiprows=10, nrows=7)
df_NUf = excel_data.parse('InitCap', header=None, usecols="A:O", skiprows=21, nrows=2)
df_Capf = excel_data.parse('InitCap', header=None, usecols="A:O", skiprows=27, nrows=2)
df_ICap = excel_data.parse('Trans_Inter', header=None, usecols="A:H", skiprows=6, nrows=12)
df_pim_y = excel_data.parse('Trans_Inter', header=None, usecols="A:G", skiprows=57, nrows=6)
df_ipe = excel_data.parse('ClusteredDataSTOR', header=None, usecols="A:H", skiprows=2, nrows=144)
df_ElecDem = excel_data.parse('ClusteredDataSTOR', header=None, usecols="I:K", skiprows=2, nrows=144)
df_Ind = excel_data.parse('ClusteredDataSTOR', header=None, usecols="AP:BD", skiprows=2, nrows=144)
df_Com = excel_data.parse('ClusteredDataSTOR', header=None, usecols="AA:AO", skiprows=2, nrows=144)
df_Dom = excel_data.parse('ClusteredDataSTOR', header=None, usecols="L:Z", skiprows=2, nrows=144)
df_AV = excel_data.parse('ClusteredDataSTOR', header=None, usecols="BE:CS", skiprows=2, nrows=144)
df_temp = excel_data.parse('ClusteredDataSTOR', header=None, usecols="CT:DH", skiprows=2, nrows=144)
df_fuel = excel_data.parse('Fuels', header=None, usecols="A:G", skiprows=3, nrows=5)

df_DistRes = excel_data.parse('Distances', header=None, usecols="B:D", skiprows=23, nrows=3)
df_DistSt = excel_data.parse('Distances', header=None, usecols="B:D", skiprows=31, nrows=4)
df_Dist = excel_data.parse('Distances', header=None, usecols="B:N", skiprows=4, nrows=13)
df_DistPipe = excel_data.parse('Distances', header=None, usecols="R:AD", skiprows=4, nrows=13)
df_ExT = excel_data.parse('Trans_Inter', header=None, usecols="B:N", skiprows=80, nrows=13)
df_DCProfile = excel_data.parse('DC', header=None, usecols="A:C", skiprows=2, nrows=144)
df_DCCap = excel_data.parse('DC', header=None, usecols="F:S", skiprows=7, nrows=5)
year_data2 = excel_data.parse('DC')
Water_data1 = excel_data.parse('Water')

# ---- Mineral data: only declared in the model, never used in a constraint or in the objective.
#      If 'Mineral.xlsx' is not available, neutral dummy data are created so that the model builds.
try:
    file_path2 = find_file("Mineral.xlsx")
    excel_data2 = pd.ExcelFile(file_path2, engine='openpyxl')
    df_intensity = excel_data2.parse('Intensity', header=None, usecols="A:O", skiprows=2, nrows=29)
    df_MinAV = excel_data2.parse('Availability', header=None, usecols="A:G", skiprows=1, nrows=14)
    Sets_data2 = excel_data2.parse('Sets')
    Recovery_data1 = excel_data2.parse('Recovery')
    Proportion_data1 = excel_data2.parse('Proportion')
    print("Mineral.xlsx found and loaded.")
except FileNotFoundError:
    print("Mineral.xlsx not found -> using neutral dummy mineral data (not used by the model constraints).")
    _mn = ["M%d" % i for i in range(1, 15)]
    _sets2 = pd.DataFrame([["Minerals", "m"] + _mn])
    Sets_data2 = _sets2
    _jn = [str(x).strip() for x in Sets_data.iloc[7, 2:31].values]
    df_intensity = pd.DataFrame([[j] + [0.0]*14 for j in _jn])
    df_MinAV = pd.DataFrame([[m] + [0.0]*6 for m in _mn])
    Recovery_data1 = pd.DataFrame([[m, 0.0] for m in _mn])
    Proportion_data1 = pd.DataFrame([[m, 0.0] for m in _mn])

# ---- Cooling data (PUE / WUE for the three cooling architectures)
file_path3 = find_file("Cooling.xlsx")
excel_data3 = pd.ExcelFile(file_path3, engine='openpyxl')
df_AirCooled = excel_data3.parse('Air_Cooled', header=None, usecols="A:AB", skiprows=2, nrows=144)
df_WaterCooled = excel_data3.parse('Water-Cooled', header=None, usecols="A:AB", skiprows=2, nrows=144)
df_Liquid = excel_data3.parse('Liquid_Cooling', header=None, usecols="A:AB", skiprows=2, nrows=144)


#%%
from pyomo.environ import *
from pyomo.environ import SolverFactory
def build_model(hl_max, cfg=None):
    cfg = dict(DEFAULT_CFG, **(cfg or {}))   ### PATCH ###  scenario switches (cooling, water limit, sensitivities)
    model = ConcreteModel()

    # ---------------------------------Define Main and Additional Sets and Subsets ------------------------------
    #%%SETs
    b_data = Sets_data.iloc[0, 2:7].values
    c_data = Sets_data.iloc[1, 2:8].values 
    d_data = Sets_data.iloc[2, 2:5].values
    f_data = Sets_data.iloc[3, 2:8].values
    g_data = Sets_data.iloc[4, 2:15].values
    h_data = Sets_data.iloc[5, 2:26].values
    i_data = Sets_data.iloc[6, 2:14].values
    j_data = Sets_data.iloc[7, 2:31].values
    k_data = Sets_data.iloc[8, 2:8].values
    r_data = Sets_data.iloc[9, 2:6].values
    t_data = Sets_data.iloc[10, 2:8].values
    jb_data = Sets_data.iloc[11, 2:5].values
    jccs_data = Sets_data.iloc[12, 2:7].values
    je_data = Sets_data.iloc[13, 2:16].values
    jep_data = Sets_data.iloc[14, 2:14].values
    jes_data = Sets_data.iloc[15, 2:4].values
    jh_data = Sets_data.iloc[16, 2:12].values
    jhe_data = Sets_data.iloc[17, 2:7].values
    jhp_data = Sets_data.iloc[18, 2:6].values
    jhs_data = Sets_data.iloc[19, 2:8].values
    jre_data = Sets_data.iloc[20, 2:6].values
    jth_data = Sets_data.iloc[21, 2:10].values
    jlf_data = Sets_data.iloc[22, 2:3].values
    M_data = Sets_data2.iloc[0,2:16].values

    model.b = Set(initialize=b_data)
    model.c = Set(initialize=c_data)
    model.d = Set(initialize=d_data)
    model.d2 = Set(initialize=['d1', 'd2'])
    model.f = Set(initialize=f_data)
    model.g = Set(initialize=g_data)
    model.h = Set(initialize=h_data)
    model.i = Set(initialize=i_data)
    model.j = Set(initialize=j_data)
    model.k = Set(initialize=k_data)
    model.r = Set(initialize=r_data)
    model.t = Set(initialize=[1,2,3,4,5,6])
    model.TT = Set(initialize=[2,3, 4,5, 6], within=model.t)
    model.jb = Set(initialize=jb_data)
    model.jccs = Set(initialize=jccs_data)
    model.je = Set(initialize=je_data)
    model.jep = Set(initialize=jep_data)
    model.jes = Set(initialize=jes_data)
    model.jh = Set(initialize=jh_data)
    model.jhe = Set(initialize=jhe_data)
    model.jhp = Set(initialize=jhp_data)
    model.jhs = Set(initialize=jhs_data)
    model.jre = Set(initialize=jre_data)
    model.jth = Set(initialize=jth_data)
    model.jlf = Set(initialize=jlf_data)
    model.JJHE = Set(initialize=['GasBoiler', 'HyBoiler', 'ASHP'], within=model.jhe)
    model.m= Set(initialize=M_data)
    model.z=Set(initialize=['LND', 'Slough', 'Wales', 'Manchester', 'AI Zone'])
    model.per = Set(initialize=[f"p{i}" for i in range(1, 9)], doc="periods in a year")

    # Define CP as a 2-dimensional set of (c, per) tuples
    model.CP = Set(dimen=2, initialize=[('c3','p1'), 
                                        ('c1','p2'), 
                                        ('c3','p3'), 
                                        ('c2','p4'), 
                                        ('c3','p5'), 
                                        ('c4','p6'), 
                                        ('c5','p7'), 
                                        ('c6','p8')])




    # jf(f,j) set
    model.jf = Set(dimen=2, initialize=[
        ('Gas', 'CCGTCCS'), ('Gas', 'OCGT'), ('Gas', 'SMRCCS'), ('Gas', 'ATRCCS'), ('Gas', 'CCGT'),
        ('Uranium', 'Nuclear'),
        ('Bio', 'BECCS'), ('Bio', 'BGCCS'), ('Bio', 'Biomass'),
        ('GH2', 'FC'), ('GH2', 'H2CCGT'),
        ('Elec', 'WE')
    ])

    # ig(g,i) set
    model.ig = Set(dimen=2, initialize=[
        ('SC', 'MOYLE'), ('SC', 'NorthConnect'),
        ('NO', 'NSN'),
        ('EM', 'VIKINGLINK'),
        ('WS', 'Greenlink'),
        ('SW', 'Fablink'),
        ('SO', 'IFA2'),
        ('SE', 'Ifa'), ('SE', 'Britned'), ('SE', 'NEMO'), ('SE', 'ELECLink'),
        ('WN', 'EWIC')
    ])

    # ik(k,i) set
    model.ik = Set(dimen=2, initialize=[
        ('FR', 'IFA'), ('FR', 'IFA2'), ('FR', 'ELECLINK'), ('FR', 'FABLINK'),
        ('NL', 'BRITNED'),
        ('IR', 'MOYLE'), ('IR', 'EWIC'), ('IR', 'GREENLINK'),
        ('NO', 'NSN'), ('NO', 'NORTHCONNECT'),
        ('DK', 'VIKINGLINK'),
        ('BG', 'NEMO')
    ])

    # jhef(jhe,f) set
    model.jhef = Set(dimen=2, initialize=[
        ('GasBoiler', 'Gas'),
        ('HyBoiler', 'GH2'),
        ('ASHP', 'Elec'),
        ('HyGasBoiler', 'GH2'), ('HyGasBoiler', 'Gas'),
        ('HyASHP', 'Elec'), ('HyASHP', 'GH2')
    ])

    # df(d,f) set
    model.df = Set(dimen=2, initialize=[
        ('d3', 'GH2'), 
        ('d2', 'CO2')
    ])



    region1_data = Regions_data.iloc[2:48, 2].values
    region2_data = Regions_data.iloc[2:48, 3].values
    Neighbourhood_Regions = list(zip(region1_data,region2_data))

    region3_data = Regions_data.iloc[2:34, 8].values
    region4_data = Regions_data.iloc[2:34, 9].values
    Neighbourhood_Regionswithpipline = list(zip(region3_data,region4_data))

    fuel_data = Regions_data.iloc[2:14, 20].values
    interconnection_data = Regions_data.iloc[2:14, 21].values
    region5_data = Regions_data.iloc[2:14, 22].values
    Interconnection_Regions = list(zip(fuel_data,interconnection_data,region5_data))
    fuel2_data = Regions_data.iloc[18:23, 20].values
    region6_data = Regions_data.iloc[18:23, 21].values
    Interconnection_Regions2 = list(zip(fuel2_data,region6_data))

    region7_data = Regions_data.iloc[2:84, 16].values
    region8_data = Regions_data.iloc[2:84, 17].values
    GJh_data=list(zip(region7_data,region8_data))

    region9_data = Trans_data.iloc[2:179, 14].values
    region10_data = Trans_data.iloc[2:179, 15].values
    TransDistance_data=list(zip(region9_data,region10_data))

    ldd_data = Trans_data.iloc[2:179, 16]
    Distance_dict = dict(zip(TransDistance_data, ldd_data))

    GR_data=[(g_data[0], r_data[2]), (g_data[5], r_data[3]), (g_data[6], r_data[0])]
    model.GR = Set(dimen=2, initialize=[(g,r) for g in model.g for r in model.r if (g,r) in GR_data])


    model.N = Set(dimen=2, initialize=[(g,g1) for g in model.g for g1 in model.g if (g,g1) in Neighbourhood_Regions])
    model.GimpE=Set(dimen=3, initialize= Interconnection_Regions)   
       
    model.GimpH=Set(dimen=2, initialize=[(f,g) for f in model.f for g in model.g if (f,g) in Interconnection_Regions2])
    model.TransDis=Set(dimen=2, initialize=[(g,g1) for g in model.g for g1 in model.g if (g,g1) in TransDistance_data])


    region_order = {region: i + 1 for i, region in enumerate(model.g)}
    model.ord_g = Param(model.g, initialize=region_order)


    year_order = {region: i + 1 for i, region in enumerate(model.t)}
    model.ord_t = Param(model.t, initialize=year_order)

    time_order = {time: i + 1 for i, time in enumerate(model.h)}
    model.ord_h = Param(model.h, initialize=time_order)


    tech_order = {tech: i+1 for i, tech in enumerate(model.j)}
    model.ord_j= Param(model.j,initialize=tech_order)


    Hydrostorage_order = {Hydrostorage: i+1 for i, Hydrostorage in enumerate(model.jhs)}
    model.ord_jhs= Param(model.jhs,initialize=Hydrostorage_order)

    #%% Read data
    
    Water_data =Water_data1.iloc[1:30, 1].values
    Water_df=Water_data1.iloc[1:30, [0,1]]
    Water_map={str(k).strip(): v for k, v in zip(Water_df.iloc[:,0], Water_df.iloc[:,1])}
    
    
    Recovery_data =Recovery_data1.iloc[0:15, 1].values
    Recovery_df=Recovery_data1.iloc[0:15, [0,1]]
    Recovery_map={str(k).strip(): v for k, v in zip(Recovery_df.iloc[:,0], Recovery_df.iloc[:,1])}

    Propotion_df=Proportion_data1.iloc[0:15, [0,1]]
    Propotion_map={str(k).strip(): v for k, v in zip(Propotion_df.iloc[:,0], Propotion_df.iloc[:,1])}



    Capunit_data =TechData_data.iloc[1:19, 1].values
    Capunit_df=TechData_data.iloc[1:19, [0,1]]
    Capunit_map={str(k).strip(): v for k, v in zip(Capunit_df.iloc[:,0], Capunit_df.iloc[:,1])}

    CHmax_data =TechData_data.iloc[1:7, 6]
    Chmax_df = TechData_data.iloc[1:7, [5, 6]]  
    Chmax_map={str(k).strip(): v for k, v in zip(Chmax_df.iloc[:,0], Chmax_df.iloc[:,1])}


    DHmax_data =TechData_data.iloc[1:7, 12].values
    DHmax_df=TechData_data.iloc[1:7, [11,12]]
    DHmax_map = {str(k).strip(): v for k, v in zip(DHmax_df.iloc[:, 0], DHmax_df.iloc[:, 1])}


    UT_data =TechData_data.iloc[25:33, 1].values
    UT_df = TechData_data.iloc[25:33, [0, 1]]
    UT_map = {str(k).strip(): v for k, v in zip(UT_df.iloc[:, 0], UT_df.iloc[:, 1])}


    LT_data =TechData_data.iloc[37:61, 1].values
    LT_df = TechData_data.iloc[37:61, [0, 1]]
    LT_map = {str(k).strip(): v for k, v in zip(LT_df.iloc[:, 0], LT_df.iloc[:, 1])}


    Pmin_data =TechData_data.iloc[65:77, 1].values
    Pmin_df = TechData_data.iloc[65:77, [0, 1]]
    Pmin_map = {str(k).strip(): v for k, v in zip(Pmin_df.iloc[:, 0], Pmin_df.iloc[:, 1])}


    Pmax_data =TechData_data.iloc[65:77, 6].values
    Pmax_df = TechData_data.iloc[65:77, [5, 6]]
    Pmax_map = {str(k).strip(): v for k, v in zip(Pmax_df.iloc[:, 0], Pmax_df.iloc[:, 1])}


    Stmin_data =TechData_data.iloc[65:70, 11].values
    Stmin_df = TechData_data.iloc[65:71, [10, 1]]
    Stmin_map = {str(k).strip(): v for k, v in zip(Stmin_df.iloc[:, 0], Stmin_df.iloc[:, 1])}

    Stmax_data =TechData_data.iloc[65:70, 16].values
    Stmax_df = TechData_data.iloc[65:71, [15, 16]]
    Stmax_map = {str(k).strip(): v for k, v in zip(Stmax_df.iloc[:, 0], Stmax_df.iloc[:, 1])}


    RD_data =TechData_data.iloc[83:95, 1].values
    RD_df = TechData_data.iloc[83:95, [0, 1]]
    RD_map = {str(k).strip(): v for k, v in zip(RD_df.iloc[:, 0], RD_df.iloc[:, 1])}


    RU_data =TechData_data.iloc[83:95, 6].values
    RU_df = TechData_data.iloc[83:95, [5, 6]]
    RU_map = {str(k).strip(): v for k, v in zip(RU_df.iloc[:, 0], RU_df.iloc[:, 1])}


    SD_data =TechData_data.iloc[83:90, 11].values
    SD_df = TechData_data.iloc[83:90, [10, 11]]
    SD_map = {str(k).strip(): v for k, v in zip(SD_df.iloc[:, 0], SD_df.iloc[:, 1])}


    SU_data =TechData_data.iloc[83:90, 16].values
    SU_df = TechData_data.iloc[83:90, [15, 16]]
    SU_map = {str(k).strip(): v for k, v in zip(SU_df.iloc[:, 0], SU_df.iloc[:, 1])}


    Sdur_data =TechData_data.iloc[127:129, 1].values
    Sdur_df = TechData_data.iloc[127:129, [0, 1]]
    Sdur_map = {str(k).strip(): v for k, v in zip(Sdur_df.iloc[:, 0], Sdur_df.iloc[:, 1])}



    drf_data =TechData_data.iloc[133:147, 1].values
    drf_df = TechData_data.iloc[133:147, [0, 1]]
    drf_map = {str(k).strip(): v for k, v in zip(drf_df.iloc[:, 0], drf_df.iloc[:, 1])}

    Ifmin_data =TechData_data.iloc[184:208, 1].values
    Ifmin_df = TechData_data.iloc[184:208, [0, 1]]
    Ifmin_map = {str(k).strip(): v for k, v in zip(Ifmin_df.iloc[:, 0], Ifmin_df.iloc[:, 1])}


    Ifmax_data =TechData_data.iloc[184:208, 5].values
    Ifmax_df = TechData_data.iloc[184:208, [4, 5]]
    Ifmax_map = {str(k).strip(): v for k, v in zip(Ifmax_df.iloc[:, 0], Ifmax_df.iloc[:, 1])}


    etasef_data =TechData_data.iloc[212:220, 1].values
    etasef_df = TechData_data.iloc[212:220, [0, 1]]
    etasef_map = {str(k).strip(): v for k, v in zip(etasef_df.iloc[:, 0], etasef_df.iloc[:, 1])}


    EtP_data =TechData_data.iloc[224:232, 1].values
    EtP_df = TechData_data.iloc[224:232, [0, 1]]
    EtP_map = {str(k).strip(): v for k, v in zip(EtP_df.iloc[:, 0], EtP_df.iloc[:, 1])}

    LT_heat_data =HeatTech_data.iloc[19:24, 1].values
    LT_heat_df = HeatTech_data.iloc[19:24, [0, 1]]
    LT_heat_map = {str(k).strip(): v for k, v in zip(LT_heat_df.iloc[:, 0], LT_heat_df.iloc[:, 1])}


    cstart_data =CostTech_data.iloc[29:40, 1].values
    cstart_df = CostTech_data.iloc[29:40, [0, 1]]
    cstart_map = {str(k).strip(): v for k, v in zip(cstart_df.iloc[:, 0], cstart_df.iloc[:, 1])}




    cshut_data =CostTech_data.iloc[29:40, 5].values
    cshut_df = CostTech_data.iloc[29:40, [4, 5]]
    cshut_map = {str(k).strip(): v for k, v in zip(cshut_df.iloc[:, 0], cshut_df.iloc[:, 1])}



    oc_var_data =CostTech_data.iloc[1:25, 23].values
    oc_var_df = CostTech_data.iloc[1:25, [22, 23]]
    oc_var_map = {str(k).strip(): v for k, v in zip(oc_var_df.iloc[:, 0], oc_var_df.iloc[:, 1])}


    oc_var_ch_data =CostTech_data.iloc[1:9, 31].values
    oc_var_ch_df = CostTech_data.iloc[1:9, [30, 31]]
    oc_var_ch_map = {str(k).strip(): v for k, v in zip(oc_var_ch_df.iloc[:, 0], oc_var_ch_df.iloc[:, 1])}

    dur_data=General_data.iloc[6,0]
    ir_data=General_data.iloc[16,0]
    nel_data=General_data.iloc[21,0]
    iph_data=General_data.iloc[26,0]
    goc_data=General_data.iloc[36,0]
    CM_data=General_data.iloc[42,0]
    cVOLL_data=General_data.iloc[47,0]
    ctr_data=Trans_data.iloc[1,0]
    triup_data=Trans_data.iloc[21,0]
    Population_data=General_data.iloc[19:32,14].values
    Population_df = General_data.iloc[19:32, [13, 14]]
    Population_map = {str(k).strip(): v for k, v in zip(Population_df.iloc[:, 0], Population_df.iloc[:, 1])}


    drfl_data=Trans_data.iloc[25:37,1].values
    drfl_df = Trans_data.iloc[25:37, [0, 1]]
    drfl_map = {str(k).strip(): v for k, v in zip(drfl_df.iloc[:, 0], drfl_df.iloc[:, 1])}

    loss_data=Trans_data.iloc[40:52,1].values
    loss_df = Trans_data.iloc[40:52, [0, 1]]
    loss_map = {str(k).strip(): v for k, v in zip(loss_df.iloc[:, 0], loss_df.iloc[:, 1])}



    WF_data=Cluster_data.iloc[2:8,114].values
    WF_df = Cluster_data.iloc[2:8, [113, 114]]
    WF_map = {str(k).strip(): v for k, v in zip(WF_df.iloc[:, 0], WF_df.iloc[:, 1])}


    breg_data = Biomass_data.iloc[2:14, 2]
    breg_df =Biomass_data.iloc[2:15, [1, 2]]
    breg_map = {str(k).strip(): v for k, v in zip(breg_df.iloc[:, 0], breg_df.iloc[:, 1])}

    Vbiomax_data = Biomass_data.iloc[20, 1:7]
    Vbiomax_df =Biomass_data.iloc[22:28,[1,2]]
    Vbiomax_map = {int(k): v for k, v in zip(Vbiomax_df.iloc[:, 0], Vbiomax_df.iloc[:, 1])}


    DACCC_df =DAC_data.iloc[2:8,[8,9]]
    DACCC_map = {int(k): v for k, v in zip(DACCC_df.iloc[:, 0], DACCC_df.iloc[:, 1])}

    DACEC_df =DAC_data.iloc[9:15,[8,9]]
    DACEC_map = {int(k): v for k, v in zip(DACEC_df.iloc[:, 0], DACEC_df.iloc[:, 1])}

    DACHC_df =DAC_data.iloc[17:22,[8,9]]
    DACHC_map = {int(k): v for k, v in zip(DACHC_df.iloc[:, 0], DACHC_df.iloc[:, 1])}





    rcap_data=Reservoir_data.iloc[1:5, 1]
    rcap_df = Reservoir_data.iloc[1:5, [0, 1]]
    rcap_map = {str(k).strip(): v for k, v in zip(rcap_df.iloc[:, 0], rcap_df.iloc[:, 1])}

    ri0_data=Reservoir_data.iloc[9:13, 1]
    ri0_df = Reservoir_data.iloc[9:13, [0, 1]]
    ri0_map = {str(k).strip(): v for k, v in zip(ri0_df.iloc[:, 0], ri0_df.iloc[:, 1])}


    yc_data=Emissions_data.iloc[7:18, 1]
    yc_df = Emissions_data.iloc[7:18, [0, 1]]
    yc_map = {str(k).strip(): v for k, v in zip(yc_df.iloc[:, 0], yc_df.iloc[:, 1])}


    ye_data=Emissions_data.iloc[22:33, 1]
    ye_df = Emissions_data.iloc[22:33, [0, 1]]
    ye_map = {str(k).strip(): v for k, v in zip(ye_df.iloc[:, 0], ye_df.iloc[:, 1])}

    ct_data=Emissions_data.iloc[1:7, 9]
    ct_df = Emissions_data.iloc[1:7, [8, 9]]
    ct_map = {int(k) : int(v) for k, v in zip(
        Emissions_data.iloc[1:7, 8],
        Emissions_data.iloc[1:7, 9]
    )}

    et_data=Emissions_data.iloc[37:43, 9]
    et_df = Emissions_data.iloc[37:43, [8, 9]]
    et_map = {int(k): int(v) for k, v in zip(
        Emissions_data.iloc[37:43, 8],
        Emissions_data.iloc[37:43, 9]
    )}

    diaH_data=Pipelines_data.iloc[9:12, 1]
    diaH_df = Pipelines_data.iloc[9:12, [0, 1]]
    diaH_map = {str(k).strip(): v for k, v in zip(diaH_df.iloc[:, 0], diaH_df.iloc[:, 1])}


    diaC_data=Pipelines_data.iloc[9:11, 2]
    diaC_df = Pipelines_data.iloc[9:11, [0, 2]]
    diaC_map = {str(k).strip(): v for k, v in zip(diaC_df.iloc[:, 0], diaC_df.iloc[:, 1])}


    qHmax_data=Pipelines_data.iloc[20:23, 1]
    qHmax_df = Pipelines_data.iloc[20:23, [0, 1]]
    qHmax_map = {str(k).strip(): v for k, v in zip(qHmax_df.iloc[:, 0], qHmax_df.iloc[:, 1])}


    qCmax_data=Pipelines_data.iloc[20:22, 2]
    qCmax_df = Pipelines_data.iloc[20:22, [0, 2]]
    qCmax_map = {str(k).strip(): v for k, v in zip(qCmax_df.iloc[:, 0], qCmax_df.iloc[:, 1])}


    pc_H2_data=Pipelines_data.iloc[31:34, 1]
    pc_H2_df = Pipelines_data.iloc[31:34, [0, 1]]
    pc_H2_map = {str(k).strip(): v for k, v in zip(pc_H2_df.iloc[:, 0], pc_H2_df.iloc[:, 1])}


    pc_COnshore_data=Pipelines_data.iloc[31:33, 2]
    pc_COnshore_df = Pipelines_data.iloc[31:33, [0, 2]]
    pc_COnshore_map = {str(k).strip(): v for k, v in zip(pc_COnshore_df.iloc[:, 0], pc_COnshore_df.iloc[:, 1])}


    pc_COffshore_data=Pipelines_data.iloc[31:33, 6]
    pc_COffshore_df = Pipelines_data.iloc[31:33, [0, 6]]
    pc_COffshore_map = {str(k).strip(): v for k, v in zip(pc_COffshore_df.iloc[:, 0], pc_COffshore_df.iloc[:, 1])}

    dom_year_df = year_data.iloc[54:60,[9,10]]
    dom_year_map = {int(k): v for k, v in zip(dom_year_df.iloc[:, 0], dom_year_df.iloc[:, 1])}

    com_year_df = year_data.iloc[54:60,[9,11]]
    com_year_map = {int(k): v for k, v in zip(com_year_df.iloc[:, 0], com_year_df.iloc[:, 1])}

    Ind_year_df = year_data.iloc[54:60,[9,12]]
    Ind_year_map = {int(k): v for k, v in zip(Ind_year_df.iloc[:, 0], Ind_year_df.iloc[:, 1])}

    elec_year_df  = year_data.iloc[39:45,[15,16]]
    elec_year_map = {int(k): v for k, v in zip(elec_year_df.iloc[:, 0], elec_year_df.iloc[:, 1])}


    DistPipe_data = {
        (g_row, g_col): df_DistPipe.iloc[i, j]
        for i, g_row in enumerate(model.g)
        for j, g_col in enumerate(model.g)
        if df_DistPipe.iloc[i, j] > 0  
    }


    DistRes_data = {(g, r): df_DistRes.iloc[i,2] 
              for i, g in enumerate(df_DistRes.iloc[:, 0])
              for j, r in enumerate(df_DistRes.iloc[:, 1])
              if i==j}


    Dist_data = {
        (g_row, g_col): df_Dist.iloc[i, j]
        for i, g_row in enumerate(model.g)
        for j, g_col in enumerate(model.g) 
        if df_Dist.iloc[i, j] > 0
        }

    DistSt_data = {(g, s): df_DistSt.iloc[i,2] 
              for i, g in enumerate(df_DistSt.iloc[:, 0])
              for j, s in enumerate(df_DistSt.iloc[:, 1])
              if i==j}

    techs = df_eta.iloc[:, 0].str.strip()

    eta_data = {
        (techs[i], t): df_eta.iloc[i, t_idx + 1] 
        for i in range(len(techs))
        for t_idx, t in enumerate(model.t)
    }



    techs1 = df_BR.iloc[:, 0].str.strip()

    cols_to_use = [2,3, 4,5, 6]

    BR_data = {
        (tech, t): df_BR.iloc[i, col]
        for i, tech in enumerate(techs1)
        for col, t in zip(cols_to_use, [model.t[2],model.t[3], model.t[4],model.t[5], model.t[6]]) }



    techs2 = df_cc_Heat.iloc[:, 0].str.strip()
    cc_Heat_data = {
        (techs2[i], t): df_cc_Heat.iloc[i, t_idx + 1] 
        for i in range(len(techs2))
        for t_idx, t in enumerate(model.t)
    }

    ### PATCH ###  sensitivity multipliers on heating-technology capex
    for _k in list(cc_Heat_data.keys()):
        if _k[0] == 'ASHP':
            cc_Heat_data[_k] = cc_Heat_data[_k] * cfg['ashp_mult']
        if _k[0] == 'HyBoiler':
            cc_Heat_data[_k] = cc_Heat_data[_k] * cfg['hyboiler_mult']

    techs2 = df_eta_Heat.iloc[:, 0].str.strip()
    eta_Heat_data = {
        (techs2[i], t): df_eta_Heat.iloc[i, t_idx + 1] 
        for i in range(len(techs2))
        for t_idx, t in enumerate(model.t)
    }

    techs3 = df_cc_fix.iloc[:, 0].str.strip()
    cc_fix_data = {
        (techs3[i], t): df_cc_fix.iloc[i, t_idx + 1] 
        for i in range(len(techs3))
        for t_idx, t in enumerate(model.t)
    }



    ### PATCH ###  sensitivity multiplier on hydrogen-production capex
    for _k in list(cc_fix_data.keys()):
        if _k[0] in ('SMRCCS', 'ATRCCS', 'BGCCS', 'WE'):
            cc_fix_data[_k] = cc_fix_data[_k] * cfg['h2prod_mult']

    oc_fix_data = {
        (techs3[i], t): df_oc_fix.iloc[i, t_idx + 1] 
        for i in range(len(techs3))
        for t_idx, t in enumerate(model.t)
    }

    techs4 = df_LandAvailability.iloc[:, 0].str.strip()
    LandAvailability_data = {
        (techs4[i], g): df_LandAvailability.iloc[i, g_idx + 1] 
        for i in range(len(techs4))
        for g_idx, g in enumerate(model.g)
    }

    techs5 = df_NUint.iloc[:, 0].str.strip()
    NUint_data = {
        (techs5[i], g): df_NUint.iloc[i, g_idx + 1] 
        for i in range(len(techs5))
        for g_idx, g in enumerate(model.g)
    }

    techs6 = df_Capinit.iloc[:, 0].str.strip()
    Capinit_data = {
        (techs6[i], g): df_Capinit.iloc[i, g_idx + 1] 
        for i in range(len(techs6))
        for g_idx, g in enumerate(model.g)
    }

    techs7 = df_NUf.iloc[:, 0].str.strip()


    NUF_data = {
        (j.strip(), int(t), g): df_NUf.iloc[i, 2 + gi]
        for i, (j, t) in enumerate(zip(df_NUf.iloc[:, 0], df_NUf.iloc[:, 1]))
        for gi, g in enumerate(model.g)
    }

    techs8 = df_Capf.iloc[:, 0].str.strip()

    Capf_data = {
        (j.strip(), int(t), g): df_Capf.iloc[i, 2 + gi]
        for i, (j, t) in enumerate(zip(df_Capf.iloc[:, 0], df_Capf.iloc[:, 1]))
        for gi, g in enumerate(model.g)
    }


    links = df_ICap.iloc[:, 0].str.strip()   
    regions = df_ICap.iloc[:, 1].str.strip() 

    cols_time = range(2, 8)  

    ICap_data = {
        (i, g, t): df_ICap.iloc[idx, col]
        for idx, (i, g) in enumerate(zip(links, regions))
        for col, t in zip(cols_time, model.t) 
    }


    Country = df_pim_y.iloc[:, 0].str.strip()
    Country_data = {
        (Country[i], t): df_pim_y.iloc[i, t_idx + 1] 
        for i in range(len(Country))
        for t_idx, t in enumerate(model.t)
    }


    cluster = df_ipe.iloc[:, 0].str.strip()   
    Hour = df_ipe.iloc[:, 1].str.strip() 

    cols_time = range(2, 8)  

    ipe_data = {
        (c, h, k): df_ipe.iloc[cdx, col]
        for cdx, (c, h) in enumerate(zip(cluster, Hour))
        for col, k in zip(cols_time, model.k) 
    }


    ElecDem_data = {
        (row[8], row[9]): row[10] for idx, row in df_ElecDem.iterrows()
    }



    Ind_data = {(c, h, g): df_Ind.iloc[i, 2+j] 
                   for i, (c, h) in enumerate(zip(df_Ind.iloc[:, 0], df_Ind.iloc[:, 1]))  
                   for j, g in enumerate(model.g)}

    Com_data = {(c, h, g): df_Com.iloc[i, 2+j] 
                   for i, (c, h) in enumerate(zip(df_Com.iloc[:, 0], df_Com.iloc[:, 1]))  
                   for j, g in enumerate(model.g)}

    Dom_data = {(c, h, g): df_Dom.iloc[i, 2+j] 
                   for i, (c, h) in enumerate(zip(df_Dom.iloc[:, 0], df_Dom.iloc[:, 1]))  
                   for j, g in enumerate(model.g)}

    jre_filtered = ["Solar", "WindOn", "WindOff"]

    AV_data = {
        (c, h, g, e): df_AV.iloc[i, 2 + 3 * g_idx + e_idx]
        for i, (c, h) in enumerate(zip(df_AV.iloc[:, 0], df_AV.iloc[:, 1]))
        for g_idx, g in enumerate(model.g)
        for e_idx, e in enumerate(jre_filtered) 
    }
    
   
    
    
    
    
    PUE_data1 = {
    (c, h, g): df_AirCooled.iloc[i, 2 + 2 * g_idx]
    for i, (c, h) in enumerate(
        zip(df_AirCooled.iloc[:, 0], df_AirCooled.iloc[:, 1])
    )
    for g_idx, g in enumerate(model.g)
    }
    
    WUE_data1 = {
        (c, h, g): df_AirCooled.iloc[i, 3 + 2 * g_idx]
        for i, (c, h) in enumerate(
            zip(df_AirCooled.iloc[:, 0], df_AirCooled.iloc[:, 1])
        )
        for g_idx, g in enumerate(model.g)
    }
    
    PUE_data2 = {
    (c, h, g): df_WaterCooled.iloc[i, 2 + 2 * g_idx]
    for i, (c, h) in enumerate(
        zip(df_WaterCooled.iloc[:, 0], df_WaterCooled.iloc[:, 1])
    )
    for g_idx, g in enumerate(model.g)
    }
    
    WUE_data2 = {
        (c, h, g): df_WaterCooled.iloc[i, 3 + 2 * g_idx]
        for i, (c, h) in enumerate(
            zip(df_WaterCooled.iloc[:, 0], df_WaterCooled.iloc[:, 1])
        )
        for g_idx, g in enumerate(model.g)
    }
    
    
    
    PUE_data3 = {
    (c, h, g): df_Liquid.iloc[i, 2 + 2 * g_idx]
    for i, (c, h) in enumerate(
        zip(df_Liquid.iloc[:, 0], df_Liquid.iloc[:, 1])
    )
    for g_idx, g in enumerate(model.g)
    }
    
    WUE_data3 = {
        (c, h, g): df_Liquid.iloc[i, 3 + 2 * g_idx]
        for i, (c, h) in enumerate(
            zip(df_Liquid.iloc[:, 0], df_Liquid.iloc[:, 1])
        )
        for g_idx, g in enumerate(model.g)
    }
     




    temp_data = {(c, h, g): df_temp.iloc[i, 2+j] 
                   for i, (c, h) in enumerate(zip(df_temp.iloc[:, 0], df_temp.iloc[:, 1]))  
                   for j, g in enumerate(model.g)}


    fuel = df_fuel.iloc[:, 0].str.strip()
    fuel_data = {
        (fuel[i], t): df_fuel.iloc[i, t_idx + 1] 
        for i in range(len(fuel))
        for t_idx, t in enumerate(model.t)
    }




    Mineral = df_MinAV.iloc[:, 0].str.strip()
    MineralAV_data = {
        (Mineral[i], t): df_MinAV.iloc[i, t_idx + 1] 
        for i in range(len(Mineral))
        for t_idx, t in enumerate(model.t)
    }

    Intensity = df_intensity.iloc[:, 0].str.strip()
    Intensity_data = {
        (Intensity[i], m): df_intensity.iloc[i, m_idx + 1] 
        for i in range(len(Intensity))
        for m_idx, m in enumerate(model.m)
    }


    TRC_data = {
        (g_row, g_col): df_ExT.iloc[i, j]
        for i, g_row in enumerate(model.g)
        for j, g_col in enumerate(model.g) 
        }


    DC_year_df = year_data2.iloc[11:17,[6,7]]
    DC_year_map = {int(k): v for k, v in zip(DC_year_df.iloc[:, 0], DC_year_df.iloc[:, 1])}


    DC_init_df = year_data2.iloc[11:24,[10,11]]
    DC_init_map = {str(k): v for k, v in zip(DC_init_df.iloc[:, 0], DC_init_df.iloc[:, 1])}




    DCDem_data = {
        (row[0], row[1]): row[2] for idx, row in df_DCProfile.iterrows()
    }





    # Suppose your df_DCCap has rows only for t = 2,4,6 in that order
    filtered_t = [2, 3,4,5, 6]

    DCCAP_data = {
        (t, g): df_DCCap.iloc[row_idx, g_idx + 1]
        for row_idx, t in enumerate(filtered_t)   # row_idx matches df rows
        for g_idx, g in enumerate(model.g)
    }



    DCCAP_data = {k: v * cfg['dc_scale'] for k, v in DCCAP_data.items()}   ### PATCH ###  dc_scale = 0 -> no data centres

    #%%PARAMETERs
    model.dw=Param(initialize=16.62)
    model.fp=Param(initialize=1.63)
    model.ge=Param(initialize=0.25)
    model.fe=Param(initialize=2.3)
    model.lut=Param(initialize=2)
    model.me=Param(initialize=0.07)
    model.sp=Param(initialize=55)
    model.tcap=Param(initialize=21.66)
    model.tma=Param(initialize=18)
    model.tmc=Param(initialize=253000)
    model.Ltroad=Param(initialize=15)
    model.delta=Param(initialize=0.05)
    model.LTpipe=Param(initialize=50)
    model.ccurt=Param(initialize=47)
    model.dur=Param(initialize=10)
    model.ir=Param(initialize=0.035)
    model.nel=Param(initialize=30)
    model.iph=Param(initialize=127.6)
    model.goc=Param(initialize=18.7)
    model.CM=Param(initialize=0.088)
    model.cVOLL=Param(initialize=20109)
    model.ctr=Param(initialize=247)
    model.crf= Param(initialize=0.05)
    model.triup=Param(initialize=1500)
    model.iota=Param(initialize=0.1)
    model.aeC0 = Param(model.r, initialize=0, doc='Initial availability of an offshore CO2 pipeline between collection point in regions g and reservoir r (0-1)')
    model.Capunit=Param(model.j, initialize=Capunit_map)
    model.CHmax = Param(model.j, initialize=Chmax_map, domain=Any)
    model.DHmax = Param(model.j, initialize=DHmax_map, domain=Any)
    model.UT = Param(model.j, initialize=UT_map, domain=Any)
    model.DT = Param(model.j, initialize=UT_map)
    model.LT = Param(model.j, initialize=LT_map)
    model.Pmin=Param(model.j, initialize=Pmin_map)
    model.Pmax=Param(model.j, initialize=Pmax_map)
    model.Stmin=Param(model.jhs, initialize=Stmin_map)
    model.Stmax=Param(model.jhs, initialize=Stmax_map)
    model.RD=Param(model.j, initialize=RD_map)
    model.RU=Param(model.j, initialize=RD_map)
    model.SD=Param(model.j, initialize=SD_map)
    model.SU=Param(model.j, initialize=SU_map)
    model.Sdur=Param(model.jes, initialize=Sdur_map)
    model.drf=Param(model.j,initialize=drf_map)
    model.Ifmin=Param(model.j, initialize=Ifmin_map)
    model.Ifmax=Param(model.j, initialize=Ifmax_map)
    model.etasef=Param(model.j,initialize=etasef_map)
    model.EtP=Param(model.j,initialize=EtP_map)
    model.LT_heat=Param(model.jhe, initialize=LT_heat_map)
    model.oc_var_ch=Param(model.j,initialize=oc_var_ch_map)
    model.oc_var=Param(model.j,initialize=oc_var_map)
    model.cstart=Param(model.j,initialize=cstart_map)
    model.cshut=Param(model.j,initialize=cshut_map)
    model.Population=Param(model.g,initialize=Population_map)
    model.drfl=Param(model.i,initialize=drfl_map)
    model.loss=Param(model.i,initialize=loss_map)
    model.WF=Param(model.c,initialize=WF_map)
    model.breg=Param(model.g,initialize=breg_map)
    model.Vbiomax=Param(model.t, initialize=Vbiomax_map)
    model.DACCC=Param(model.t, initialize=DACCC_map)
    model.ec_dac=Param(model.t, initialize=DACEC_map)
    model.hc_dac=Param(model.t, initialize=DACHC_map)

    model.ri0=Param(model.r, initialize=ri0_map)
    model.rcap=Param(model.r, initialize=rcap_map)
    model.yc=Param(model.j,initialize=yc_map)
    model.ye=Param(model.j,initialize=ye_map)
    model.ct=Param(model.t,initialize=ct_map)
    model.et=Param(model.t,initialize=et_map)
    model.diaH=Param(model.d,initialize=diaH_map)
    model.diaC=Param(model.d2,initialize=diaC_map)
    model.qHmax=Param(model.d,model.f, initialize={('d1', 'GH2'): 2117, ('d2', 'GH2'): 10052, ('d3', 'GH2'): 15343})
    model.qCmax=Param(model.d2, model.f, initialize={('d1', 'CO2'): 1666.57, ('d2', 'CO2'): 11666.67})
    model.pc_H2=Param(model.d,initialize=pc_H2_map)
    model.pc_COnshore=Param(model.d2,initialize=pc_COnshore_map)
    model.pc_COffshore=Param(model.d2,initialize=pc_COffshore_map)
    model.ldd=Param(model.TransDis,initialize=Distance_dict)
    model.DistSt = Param(model.g, model.jhs, initialize=DistSt_data, doc='distance between region g and underground storage type s')
    model.DistPipe = Param(model.g, model.g, initialize=DistPipe_data, within=NonNegativeReals, doc='Delivery distance of an onshore CO2 pipeline between regions g and g1 (km)')
    model.DistRes = Param(model.g, model.r, initialize=DistRes_data, doc='Distance from CO2 collection point in region g to reservoir r (km)')
    model.Dist = Param(model.g, model.g, initialize=Dist_data, doc='Regional delivery distance of hydrogen transportation mode l in region g (km)')
    model.TRC= Param(model.g,model.g,initialize=TRC_data)
    model.eta=Param(model.j,model.t,initialize=eta_data)
    model.BR = Param(model.j, model.TT, initialize=BR_data, domain=NonNegativeReals)
    model.cc_Heat=Param(model.jhe,model.t,initialize=cc_Heat_data)
    model.eta_Heat=Param(model.jhe,model.t,initialize=eta_Heat_data)
    model.cc_fix=Param(model.j,model.t,initialize=cc_fix_data)
    model.oc_fix=Param(model.j,model.t,initialize=oc_fix_data)
    model.LandAvailability=Param(model.jre,model.g,initialize=LandAvailability_data)
    model.NUint=Param(model.j,model.g,initialize=NUint_data,default=0)
    model.Capinit=Param(model.j,model.g,initialize=Capinit_data, default=0, mutable=True)
    model.ICap= Param(model.i,model.g,model.t, initialize=ICap_data)
    model.pim_y=Param(model.k,model.t,initialize=Country_data)
    model.ipe=Param(model.c,model.h,model.k,initialize=ipe_data)
    model.ElecDem = Param(model.c, model.h, initialize=ElecDem_data)
    model.Ind=Param(model.c,model.h,model.g, initialize=Ind_data)
    model.Com=Param(model.c,model.h,model.g, initialize=Com_data)
    model.Dom=Param(model.c,model.h,model.g, initialize=Dom_data)
    model.AV = Param(model.c, model.h, model.g, model.jre, initialize=AV_data, mutable=True)
    model.Intensity=Param(model.j,model.m,initialize=Intensity_data)
    model.MinAV=Param(model.m, model.t, initialize=MineralAV_data)
    model.K=Param(model.m,initialize=Propotion_map)
    model.REC=Param(model.m,initialize=Recovery_map)
    model.W=Param(model.j,initialize=Water_map)


    for c in model.c:
        for h in model.h:
            for g in model.g:
                model.AV[c,h,g,'Hydro'] = 0.45
    model.temp=Param(model.c, model.h,model.g, initialize=temp_data)
    model.fuel=Param(model.f,model.t,initialize=fuel_data)
    model.NUF = Param(model.j, model.t, model.g, initialize=NUF_data, default=0)
    model.Capf= Param(model.jre,model.t,model.g, initialize=Capf_data, default=0)




    from pyomo.environ import value

    def dfc_init(model, t):
        t_num = int(t)           
        return round(1 / (1 + value(model.ir)) ** (model.dur * t_num - model.dur), 2)

    model.dfc = Param(
        model.t,
        initialize=dfc_init,
        doc='Discount factor for capital costs in time period t'
    )

    # Predefined values in order
    dfo_values_list = [4.520, 3.690, 3.030, 2.490, 2.060, 1.710]

    # Create a dictionary mapping each t in model.t to the value
    dfo_values = {t: val for t, val in zip(model.t, dfo_values_list)}

    # Initialize the Param
    model.dfo = Param(
        model.t,
        initialize=dfo_values,
        doc='Predefined discount factor for each time period'
    )


    model.Npipe = Set(dimen=2,initialize=model.DistPipe.keys(), doc='Set of region pairs with nonzero pipeline distances')

    model.ayHR0 = Param(model.d, model.Npipe,initialize=0, doc='Initial availability of a regional hydrogen pipeline of diameter size d between regions g and g1 (0-1)')
    model.ayC0 = Param(model.d2, model.N, initialize=0, doc='Initial availability of an onshore CO2 pipeline of diameter size d between regions g and g1 (0-1)')

    model.StLevelInit=Param(model.jes,model.g,model.t, initialize=0)

    def ipe_t_init(model, c, h, k, t):
        return model.pim_y[k, t] * model.ipe[c, h, k]

    model.ipe_t = Param(
        model.c, model.h, model.k, model.t,
        initialize=ipe_t_init,
        doc="Adjusted ipe by pim_y for each (c,h,k,t)"
    )

    model.y1=Param(initialize=2)

    def GJh_init(model):
        jh_list = list(model.jh)  

        cond_set = [
            (g, jh)
            for g in model.g
            for jh in model.jh
            if jh_list.index(jh) < 6
        ]

        explicit_set = [
            ('NO', 'OnTeeside'),
            ('NW', 'OnChesire'),
            ('NE', 'OnYorkshire'),
            ('NW', 'OffIrishSea')
        ]

        return list(set(cond_set + explicit_set))

    model.GJh = Set(dimen=2, initialize=GJh_init, within=model.g * model.jh)

    model.dom_year= Param (model.t, initialize=dom_year_map)
    model.com_year= Param (model.t, initialize=com_year_map)
    model.Ind_year= Param (model.t, initialize=Ind_year_map)
    model.elec_year= Param(model.t,initialize=elec_year_map)


    def THeatDem_init(model, g, t, c, h):
        return (model.dom_year[t] * model.Dom[c, h, g] +
                model.com_year[t] * model.Com[c, h, g]) * model.eta_Heat['GasBoiler', t]

    model.THeatDem = Param(model.g, model.t, model.c, model.h, initialize=THeatDem_init)

    def THeatDem_max_init(model, g, t):
        return max(model.THeatDem[g, t, c, h] for c in model.c for h in model.h)

    model.THeatDem_max = Param(model.g, model.t, initialize=THeatDem_max_init)

    def TPowerDem_init(model, g, t, c, h):
        return model.elec_year[t] * model.Population[g] * model.ElecDem[c, h]

    model.TPowerDem = Param(model.g, model.t, model.c, model.h, initialize=TPowerDem_init)

    def COP_init(model, g, c, h):
        return 0.0541 * model.temp[c, h, g] + 2.6674

    model.COP = Param(model.g, model.c, model.h, initialize=COP_init)

    def CAPinit_init(model, tech, g):
        if tech != 'GasBoiler':
            return 0
        max_val = max(model.Dom[c, h, g] + model.Com[c, h, g]
                      for c in model.c for h in model.h)
        return max_val * model.eta_Heat['GasBoiler', 1]


    for tech in ['GasBoiler']:
        for g in model.g:
            val = CAPinit_init(model, tech, g)
            model.Capinit[tech, g] = val




    def IndDem_init(model, g, t, c, h):
        return model.Ind_year[t] * model.Ind[c, h, g] * model.eta_Heat['GasBoiler', t]

    model.IndDem = Param(model.g, model.t, model.c, model.h, initialize=IndDem_init)

            
    def Qpipe_bounds(model, f, g, g1, t, c, h):
        if f == 'GH2':
            return (0, 15343)
        elif f == 'CO2':
            return (0, 11666)
        return (0, None)


    def Qres_bounds(model, g, r, t, c, h):
        return (0, 11666)



    model.DCCap_max=Param(model.t,model.g, initialize=DCCAP_data)
    model.DCProfile0 = Param(model.c, model.h, initialize=DCDem_data)
    model.DC_year= Param(model.t,initialize=DC_year_map)
    model.DCInit=Param(model.g,initialize=DC_init_map)
    model.PUE_air=Param(model.c,model.h,model.g, initialize=PUE_data1)
    model.WUE_air=Param(model.c,model.h,model.g, initialize=WUE_data1)
    model.PUE_water=Param(model.c,model.h,model.g, initialize=PUE_data2)
    model.WUE_water=Param(model.c,model.h,model.g, initialize=WUE_data2)
    model.PUE_Liquid=Param(model.c,model.h,model.g, initialize=PUE_data3)
    model.WUE_Liquid=Param(model.c,model.h,model.g, initialize=WUE_data3)

    #%%Variables

    model.NTU = Var(model.g, model.g, model.t, domain=NonNegativeReals)
    model.NU = Var(model.j, model.g, model.t, domain=NonNegativeReals)

    model.CMD= Var(model.m, model.t, domain=NonNegativeReals)
    model.CMr= Var(model.m, model.t, domain=NonNegativeReals)
    model.CMt= Var(model.m, model.t, domain=NonNegativeReals)
    model.MineralAV= Var(model.m,model.t, domain=NonNegativeReals)
    model.ImportCM=Var(model.m,model.t, domain=NonNegativeReals)

    model.DU = Var(model.j, model.g, model.t, domain=NonNegativeIntegers)
    model.CU = Var(model.j, model.g, model.t, domain=NonNegativeIntegers)
    model.ITU = Var(model.g, model.g, model.t, domain=Integers)
    model.u = Var(model.j, model.g, model.t, model.c, model.h, domain=Integers)
    model.v = Var(model.j, model.g, model.t, model.c, model.h, domain=Integers)
    model.w = Var(model.j, model.g, model.t, model.c, model.h, domain=Integers)

    model.Y = Var(model.f, model.d, model.Npipe, model.t, domain=Binary)
    model.Y1 = Var(model.f, model.d2, model.N, model.t, domain=Binary)

    model.Yres = Var(model.d2, model.GR, model.t, domain=Binary)
    model.Yst = Var(model.d, model.GJh, model.t, domain=Binary)


    model.AY = Var(model.f, model.d, model.Npipe, model.t, bounds=(0,1),domain=NonNegativeReals)
    model.AY1 = Var(model.f, model.d2, model.N, model.t,bounds=(0,1), domain=NonNegativeReals)

    model.AYres = Var(model.d2, model.GR, model.t, bounds=(0,1),domain=NonNegativeReals)
    model.AYst = Var(model.d, model.g, model.jhs, model.t, bounds=(0,1),domain=NonNegativeReals)

    model.BS = Var(model.j, model.g, model.t, model.per, domain=NonNegativeReals)
    model.CAP = Var(model.j, model.g, model.t, domain=NonNegativeReals)
    model.CAPnew = Var(model.j, model.g, model.t, domain=NonNegativeReals)
    model.CAPDACnew = Var(model.g, model.t, domain=NonNegativeReals)
    model.DCAPDAC = Var(model.g, model.t, domain=NonNegativeReals)

    model.CAPDAC = Var(model.g, model.t, domain=NonNegativeReals)

    model.CAPheat = Var(model.jhe, model.g, model.t, domain=NonNegativeReals)
    model.CAPheat_new = Var(model.jhe, model.g, model.t, domain=NonNegativeReals)
    model.CH = Var(model.j, model.g, model.t, model.c, model.h, domain=NonNegativeReals)
    model.DCheat = Var(model.jhe, model.g, model.t, domain=NonNegativeReals)
    model.DCAP = Var(model.j, model.g, model.t, domain=NonNegativeReals)
    model.totdem_elec = Var(model.g, model.t, model.c, model.h, domain=NonNegativeReals)
    model.hedem_elec = Var(model.g, model.t, model.c, model.h, domain=NonNegativeReals)
    model.totdem_hydro = Var(model.g, model.t, model.c, model.h, domain=NonNegativeReals)
    model.totdem_gas = Var(model.g, model.t, model.c, model.h, domain=NonNegativeReals)
    model.hedem_hydro = Var(model.g, model.t, model.c, model.h, domain=NonNegativeReals)
    model.hedem_gas = Var(model.g, model.t, model.c, model.h, domain=NonNegativeReals)
    model.DC = Var(model.j, model.g, model.t, model.c, model.h, domain=NonNegativeReals)
    model.ETC = Var(model.t, domain=NonNegativeReals)
    model.FCC = Var(model.t, domain=NonNegativeReals)
    model.FOC = Var(model.t, domain=NonNegativeReals)
    model.HC = Var(model.t, domain=NonNegativeReals)
    model.HGDC = Var(model.t, domain=NonNegativeReals)
    model.HGOC = Var(model.t, domain=NonNegativeReals)
    model.IMPh = Var(model.g, model.t, model.c, model.h, domain=NonNegativeReals)
    model.indem_elec = Var(model.g, model.t, model.c, model.h, domain=NonNegativeReals)
    model.indem_gas = Var(model.g, model.t, model.c, model.h, domain=NonNegativeReals)
    model.indem_hydro = Var(model.g, model.t, model.c, model.h, domain=NonNegativeReals)
    model.LC = Var(model.g, model.t, model.c, model.h, domain=NonNegativeReals)
    model.LS = Var(model.g, model.t, model.c, model.h, domain=NonNegativeReals)
    model.Lelec = Var(model.g, model.t, domain=NonNegativeReals)
    model.Lgas = Var(model.g, model.t, domain=NonNegativeReals)
    model.Lhydro = Var(model.g, model.t, domain=NonNegativeReals)
    model.P = Var(model.j, model.g, model.t, model.c, model.h, domain=NonNegativeReals)
    model.PeakDemand = Var(model.t, domain=NonNegativeReals)
    model.RMslack = Var(model.t, domain=NonNegativeReals)        ### PATCH ###  reserve-margin shortfall (MW), only used if soft_reserve
    if not cfg['soft_reserve']:
        for _t in model.t:
            model.RMslack[_t].fix(0)
    model.Qelec = Var(model.g, model.g, model.t, model.c, model.h, domain=NonNegativeReals)
    model.Qroad = Var(model.f, model.g, model.g, model.t, model.c, model.h, domain=NonNegativeReals)
    model.Qpipe = Var(model.f, model.g, model.g, model.t, model.c, model.h, domain=NonNegativeReals, bounds=Qpipe_bounds)
    model.Qres = Var(model.g, model.r, model.t, model.c, model.h, domain=NonNegativeReals,bounds=Qres_bounds)
    model.PCC = Var(model.TT, domain=NonNegativeReals)
    model.POC = Var(model.TT, domain=NonNegativeReals)
    model.RCC = Var(model.t, domain=NonNegativeReals)
    model.Rdown = Var(model.j, model.g, model.t, model.c, model.h, domain=NonNegativeReals)
    model.RI = Var(model.r, model.t, domain=NonNegativeReals)
    model.ROC = Var(model.t, domain=NonNegativeReals)
    model.Rup = Var(model.j, model.g, model.t, model.c, model.h, domain=NonNegativeReals)
    model.S = Var(model.j, model.g, model.t, model.c, model.h, domain=NonNegativeReals)
    model.TCC = Var(model.TT, domain=NonNegativeReals)
    model.TOC = Var(model.TT, domain=NonNegativeReals)
    model.TRCnew = Var(model.g, model.g, model.t, domain=NonNegativeReals)
    model.TRI = Var(model.g, model.g, model.TT, domain=NonNegativeReals)
    model.Vf = Var(model.f, model.j, model.g, model.t, domain=NonNegativeReals)
    model.THeatDem_max1 = Var(model.g, model.t, domain=NonNegativeReals)
        
    model.CEC = Var(model.t)
    model.Etotal = Var(model.t)
    model.Ee = Var(model.t)
    model.Eh = Var(model.t)
    model.Eg = Var(model.t)
    model.IIC = Var(model.t)
    model.GasC = Var(model.t)
    model.Imp = Var()
    model.IMPe = Var(model.i, model.g, model.t, model.c, model.h)
    model.PipeCost = Var(domain=NonNegativeReals)


    model.CapDC=Var(model.TT, model.g,domain=NonNegativeReals)
    model.CapDCNew=Var(model.TT, model.g,domain=NonNegativeReals)

    model.TDemandDC=Var(model.g,model.TT,model.c,model.h, domain=NonNegativeReals)
    model.alpha=Var(model.t,model.z,domain=Reals, bounds=(-0.2,0.2))


    model.DAC=Var(model.g,model.t,model.c,model.h, domain=NonNegativeReals)
    model.E_DAC=Var(model.g,model.t,model.c,model.h, domain=NonNegativeReals)
    model.H_DAC=Var(model.g,model.t,model.c,model.h, domain=NonNegativeReals)
    model.Water=Var(model.j,model.g,model.t,model.c,model.h,domain=NonNegativeReals)
    model.Water_DC=Var(model.g,model.t,model.c,model.h,domain=NonNegativeReals)
    model.ttt=RangeSet(2,hl_max)

    #%%
    # Facilities capital cost
    def FCC_rule(model, t):
        return (
           0.001* model.FCC[t]
            == 0.001*sum(
                model.cc_fix[j, t] * model.Capunit[j] * model.CU[j, g, t]
                for g in model.g
                for j in model.j
                if ((g, j) in model.GJh or j in model.jth)
            )
            +0.001* sum(
                model.cc_fix[j, t] * model.CAPnew[j, g, t]
                for g in model.g
                for j in model.j
                if (j in model.jes or j in model.jre)
            )+0.001*sum(
                model.DACCC[t]*model.CAPDACnew[g,t] for g in model.g)
        )

    model.FCCConstraint = Constraint(model.ttt, rule=FCC_rule)

    def ETC_rule(model, t):
        
            return 0.001*model.ETC[t] == 0.001*sum(
                model.ctr * model.ldd[g, g1] * model.TRI[g, g1, t] / 2
                for g in model.g for g1 in model.g if (g, g1) in model.N
            )
       

    model.ETConstraint = Constraint(model.ttt, rule=ETC_rule)


    def PCC_rule(model, t):
        
            return 0.001*model.PCC[t] == 0.001*(
                # 1st sum: Hydrogen pipelines
                sum(
                    model.pc_H2[d] * model.DistPipe[g,g1] * model.Y[f,d,g,g1,t]
                    for d in model.d
                    for f in model.f if f=="f2"
                    for g in model.g
                    for g1 in model.g
                    if (g,g1) in model.Npipe and model.ord_g[g] < model.ord_g[g1] and (d,f) in model.df
                )
                +
                # 2nd sum: CO2 onshore
                sum(
                    model.pc_COnshore[d2] * model.Dist[g,g1] * model.Y1[f,d2,g,g1,t]
                    for d2 in model.d2
                    for f in model.f if f=="f3"
                    for g in model.g
                    for g1 in model.g
                    if (g,g1) in model.N and model.ord_g[g] < model.ord_g[g1] and (d2,f) in model.df
                )
                +
                # 3rd sum: CO2 offshore
                sum(
                    model.pc_COffshore[d2] * model.DistRes[g,r] * model.Yres[d2,g,r,t]
                    for d2 in model.d2
                    for g in model.g
                    for r in model.r
                    if (g,r) in model.GR
                )
                +
                # 4th sum: Hydrogen storage
                sum(
                    model.pc_H2[d] * model.DistSt[g,jhs] * model.Yst[d,g,jhs,t]
                    for d in model.d
                    for g in model.g
                    for jhs in model.jhs
                    if (g,jhs) in model.GJh and jhs in ['OnTeeside','OnChesire','OnYorkshire','OffIrishSea']
                )
            )
        

    model.PCCConstraint = Constraint(model.ttt, rule=PCC_rule)



    def POC_rule(model, t):
       
            return 0.001*model.POC[t] == 0.001*(
                model.delta * model.crf * (
                    # 1st sum: Hydrogen pipelines
                    sum(
                        model.pc_H2[d] * model.DistPipe[g,g1] * model.AY[f,d,g,g1,t]
                        for d in model.d
                        for f in model.f if f=="f2"
                        for g in model.g
                        for g1 in model.g
                        if (g,g1) in model.Npipe and model.ord_g[g] < model.ord_g[g1] and (d,f) in model.df
                    )
                    +
                    # 2nd sum: CO2 onshore
                    sum(
                        model.pc_COnshore[d2] * model.Dist[g,g1] * model.AY1[f,d2,g,g1,t]
                        for d2 in model.d2
                        for f in model.f if f=="f3"
                        for g in model.g
                        for g1 in model.g
                        if (g,g1) in model.N and model.ord_g[g] < model.ord_g[g1] and (d2,f) in model.df
                    )
                    +
                    # 3rd sum: CO2 offshore
                    sum(
                        model.pc_COffshore[d2] * model.DistRes[g,r] * model.AYres[d2,g,r,t]
                        for d2 in model.d2
                        for g in model.g
                        for r in model.r
                        if (g,r) in model.GR
                    )
                    +
                    # 4th sum: Hydrogen storage
                    sum(
                        model.pc_H2[d] * model.DistSt[g,jhs] * model.AYst[d,g,jhs,t]
                        for d in model.d
                        for g in model.g
                        for jhs in model.jhs
                        if (g,jhs) in model.GJh and jhs in ['OnTeeside','OnChesire','OnYorkshire','OffIrishSea']
                    )
                )
            )
       

    model.POCConstraint = Constraint(model.ttt, rule=POC_rule)






    def FOC_rule(model, t):
        
            return 0.001*model.FOC[t] == 0.001*(

                # 1st sum: (j,g) in Gjh(g,j) or jth(j)
                sum(
                    model.oc_fix[j, t] * model.Capunit[j] * model.NU[j, g, t]
                    for j in model.j
                    for g in model.g
                    if ((g, j) in model.GJh or j in model.jth)
                )
                +
                # 2nd sum: (j,g) in jes(j) or jre(j)
                sum(
                    model.oc_fix[j, t] * model.CAP[j, g, t]
                    for j in model.j
                    for g in model.g
                    if (j in model.jes or j in model.jre)
                )
                +
                # 3rd sum: (j,g,c,h) with jhp(j) or jep(j)
                sum(
                    model.WF[c] * model.oc_var[j] * model.P[j, g, t, c, h]
                    for j in model.j
                    for g in model.g
                    for c in model.c
                    for h in model.h
                    if (j in model.jhp or j in model.jep)
                )
                +
                # 4th sum: (f,j,g) in jf
                sum(
                    model.fuel[f, t] * model.Vf[f, j, g, t]
                    for f in model.f
                    for j in model.j
                    for g in model.g
                    if (f, j) in model.jf
                )
                +
                # 5th sum: (j,g,c,h) with jhs(j) or jes(j)
                sum(
                    model.WF[c] * model.oc_var[j] * model.S[j, g, t, c, h]
                    for j in model.j
                    for g in model.g
                    for c in model.c
                    for h in model.h
                    if (j in model.jhs or j in model.jes)
                )
                +
                # 6th sum: (j,g,c,h,f) with jhs(j) or jes(j)
                sum(
                    model.WF[c] * model.oc_var_ch[j] * model.CH[j, g, t, c, h]
                    for j in model.j
                    for g in model.g
                    for c in model.c
                    for h in model.h
                    for f in model.f
                    if (j in model.jhs or j in model.jes)
                )
                +
                # 7th sum: curtailment cost
                sum(
                    model.WF[c] * model.ccurt * model.LC[g, t, c, h]
                    for g in model.g
                    for c in model.c
                    for h in model.h
                )
                +
                # 8th sum: Value of Lost Load
                sum(
                    model.WF[c] * model.cVOLL*2 * model.LS[g, t, c, h]
                    for g in model.g
                    for c in model.c
                    for h in model.h
                )
                
            )
      

    model.FOCConstraint = Constraint(model.ttt, rule=FOC_rule)

    def CEC_rule(model, t):
       
            return 0.001*model.CEC[t]==0.001*model.ct[t]*model.Etotal[t]
        
    model.CECConstraint = Constraint(model.ttt, rule=CEC_rule)   


    def IIC_rule(model, t):
       
            return 0.001*model.IIC[t] == 0.001 *(
                # 1st sum: Electric imports
                sum(
                    model.WF[c] * model.ipe_t[c, h, k, t] * model.IMPe[i, g, t, c, h]
                    for g in model.g
                    for c in model.c
                    for h in model.h
                    for i in model.i
                    for k in model.k
                    if ('Elec', i, g) in model.GimpE and (k, i) in model.ik
                )
                +
                # 2nd sum: Hydrogen imports
                sum(
                    model.WF[c] * model.iph * model.IMPh[g, t, c, h]
                    for g in model.g
                    for c in model.c
                    for h in model.h
                    if ('GH2', g) in model.GimpH
                )
            )
        

    model.IICConstraint = Constraint(model.ttt, rule=IIC_rule)
    '''
    def GasC_rule(model,t):
        if t in model.TT:
            return model.GasC[t] == model.dfo[t]*(
                # 1st sum: gas use in technologies
                sum(
                    model.Vf['Gas', j, g, t]
                    for j in model.j
                    for g in model.g
                    if ('Gas', j) in model.jf 
                )
                +
                # 2nd sum: total gas demand
                sum(
                    model.WF[c] * model.totdem_gas[g, t, c, h]
                    for g in model.g
                    for c in model.c
                    for h in model.h
                    
                )
            )
        return Constraint.Skip   
    model.GasCeq = Constraint(model.ttt,rule=GasC_rule)
    '''
    # Heating capacity cost
    def HC_rule(model, t):
       
            return 0.001*model.HC[t] == 0.001*sum(
                model.cc_Heat[jhe, t] * model.CAPheat_new[jhe, g, t]
                for jhe in model.jhe
                for g in model.g
            )
       

    model.HCConstraint = Constraint(model.ttt, rule=HC_rule)


    # Direct Gas Cost for heating
    def HGDC_rule(model, t):
        if t in model.TT:
            return 0.001*model.HGDC[t] == 0.001*sum(
                model.WF[c] * model.fuel['Gas', t] * model.totdem_gas[g, t, c, h]
                for g in model.g
                for c in model.c
                for h in model.h
               
            )
        return Constraint.Skip

    model.HGDCConstraint = Constraint(model.ttt, rule=HGDC_rule)


    # Operating Gas Cost for heating
    def HGOC_rule(model, t):
       
            return 0.001*model.HGOC[t] == 0.001*sum(
                model.WF[c] * model.goc * model.totdem_gas[g, t, c, h]
                for g in model.g
                for c in model.c
                for h in model.h
            )
        

    model.HGOCConstraint = Constraint(model.ttt, rule=HGOC_rule)



    def TCC_rule(model,t):
        
          return model.TCC[t]==model.PCC[t]+model.FCC[t]+model.ETC[t]+model.HC[t]
        
    model.TCCConstraint=Constraint(model.ttt,rule=TCC_rule)


    def TOC_rule(model,t):
        
          return model.TOC[t]==model.POC[t]+model.FOC[t]+model.CEC[t]+model.IIC[t]+model.HGDC[t]+model.HGOC[t]#+model.GasC[t]
        
    model.TOCConstraint=Constraint(model.ttt,rule=TOC_rule)


    def TC_rule(model):
        return sum(model.dfc[t]*model.TCC[t] +  model.dfo[t]*model.TOC[t] for t in model.ttt)+ (cfg['reserve_penalty'] * sum(model.dfo[t] * model.RMslack[t] for t in model.ttt) if cfg['soft_reserve'] else 0) + 0.1 * sum(
            (model.Qpipe['GH2', g, g1, t, c, h] if (g, g1) in model.Npipe else 0)
            + (model.Qpipe['CO2', g, g1, t, c, h] if (g, g1) in model.N else 0)
            for g in model.g
            for g1 in model.g
            for t in model.ttt
            for c in model.c
            for h in model.h
        )
            

    model.TC = Objective(rule=TC_rule, sense=minimize)

    #%% Heating Calculation
    def HeatElec_rule(model, g, t, c, h):
        #if t in model.TT:
            return model.hedem_elec[g, t, c, h] == model.Lelec[g, t] * model.THeatDem[g, t, c, h]
        #return Constraint.Skip

    model.HeatElec = Constraint(model.g, model.ttt, model.c, model.h, rule=HeatElec_rule)

    # Heating hydrogen demand
    def HeatHydro_rule(model, g, t, c, h):
        #if t in model.TT:
            return model.hedem_hydro[g, t, c, h] == model.Lhydro[g, t] * model.THeatDem[g, t, c, h]
        #return Constraint.Skip

    model.HeatHydro = Constraint(model.g, model.ttt, model.c, model.h, rule=HeatHydro_rule)

    # Heating gas demand
    def HeatGas_rule(model, g, t, c, h):
        #if t in model.TT:
            return model.hedem_gas[g, t, c, h] == model.Lgas[g, t] * model.THeatDem[g, t, c, h]
        #return Constraint.Skip

    model.HeatGas = Constraint(model.g, model.ttt, model.c, model.h, rule=HeatGas_rule)

    # Heat summation for flexible system
    def HeatSum_rule(model, g, t, c, h):
        #if t in model.TT:
            return model.hedem_elec[g, t, c, h] + model.hedem_hydro[g, t, c, h] + model.hedem_gas[g, t, c, h] == model.THeatDem[g, t, c, h]
        #return Constraint.Skip

    model.HeatSum = Constraint(model.g, model.ttt, model.c, model.h, rule=HeatSum_rule)

    # Lambda coefficient summation
    def Lcoefsum_rule(model, g, t):
        #if t in model.TT:
            return model.Lelec[g, t] + model.Lhydro[g, t] + model.Lgas[g, t] == 1
        #return Constraint.Skip

    model.Lcoefsum = Constraint(model.g, model.ttt, rule=Lcoefsum_rule)

    # Upper bounds for lambda coefficients
    #def Lelec2_rule(model, g, t):
       # if t in model.TT:
            #return model.Lelec[g, t] <= 1
        #return Constraint.Skip

    #model.Lelec2 = Constraint(model.g, model.ttt, rule=Lelec2_rule)


    #def Lgas3_rule(model, g, t):
        #if t in model.ttt:
            #return model.Lgas[g, t] <= 1
        #return Constraint.Skip

    #model.Lgas3 = Constraint(model.g, model.ttt, rule=Lgas3_rule)


    # Industrial heating demand
    def IndHeat_rule(model, g, t, c, h):
        #if t in model.TT:
            return (model.indem_elec[g, t, c, h] + model.indem_hydro[g, t, c, h] +
                    model.indem_gas[g, t, c, h] == model.IndDem[g, t, c, h])
        #return Constraint.Skip

    model.IndHeat = Constraint(model.g, model.ttt, model.c, model.h, rule=IndHeat_rule)

    # Fixing variables
    for g in model.g:
        for t in model.ttt:
            for c in model.c:
                for h in model.h:
                    model.indem_hydro[g, t, c, h].fix(0)

                    if t == 6:
                        model.indem_elec[g, t, c, h].fix(model.IndDem[g, t, c, h])

    def HeatPen1_rule(model, g, t):
        if model.ord_t[t] > model.y1:
            t_prev = model.ord_t[t] - 1  
            t_prev_label = [tt for tt in model.ttt if model.ord_t[tt] == t_prev]
            if len(t_prev_label) == 0:
                return Constraint.Skip
            t_prev_label = t_prev_label[0]
            return sum(model.hedem_hydro[g, t_prev_label, c, h] for c in model.c for h in model.h) <= \
                   sum(model.hedem_hydro[g, t, c, h] for c in model.c for h in model.h)
        return Constraint.Skip

    model.HeatPen1 = Constraint(model.g, model.ttt, rule=HeatPen1_rule)

    def HeatPen2_rule(model, g, t):
        if  model.ord_t[t] > model.y1:
            t_prev = model.ord_t[t] - 1
            t_prev_label = [tt for tt in model.ttt if model.ord_t[tt] == t_prev]
            if len(t_prev_label) == 0:
                return Constraint.Skip
            t_prev_label = t_prev_label[0]
            return sum(model.hedem_elec[g, t_prev_label, c, h] for c in model.c for h in model.h) <= \
                   sum(model.hedem_elec[g, t, c, h] for c in model.c for h in model.h)
        return Constraint.Skip

    model.HeatPen2 = Constraint(model.g, model.ttt, rule=HeatPen2_rule)


    #%% Data Centre


    def CapDC_rule(model, t, g):
        T = model.ttt
        if t == T.first():
            return model.CapDC[t, g] == model.DCCap_max[2,g]
        else:
            t_prev = T.prev(t)
            return model.CapDC[t, g] == model.CapDC[t_prev, g] + model.CapDCNew[t, g]
    model.CapDataCentreCON=Constraint(model.ttt,model.g, rule=CapDC_rule)

    ### PATCH ###  cooling switch (the uploaded code was hard-wired to the liquid / D2C data)
    PUE_sel = {'air': model.PUE_air, 'water': model.PUE_water, 'liquid': model.PUE_Liquid}[cfg['cooling']]
    WUE_sel = {'air': model.WUE_air, 'water': model.WUE_water, 'liquid': model.WUE_Liquid}[cfg['cooling']]

    def DC_Profile_rule(model,g,t,c,h):
        #if t in model.TT and c in model.c and h in model.h:
            return model.TDemandDC[g,t,c,h]==model.CapDC[t, g]*model.DCProfile0[c,h]*PUE_sel[c,h,g]
        #return Constraint.Skip
    model.DCProfileCON=Constraint(model.g,model.ttt, model.c,model.h, rule=DC_Profile_rule)
    
    
    
    def DC_Water_rule(model,g,t,c,h):
        #if t in model.TT and c in model.c and h in model.h:
            return model.Water_DC[g,t,c,h]==model.CapDC[t, g]*model.DCProfile0[c,h]*WUE_sel[c,h,g]*KWH_PER_MWH   ### PATCH ###  x1000: CapDC is in MW, WUE in L/kWh
        #return Constraint.Skip
    model.DCWaterCON=Constraint(model.g,model.ttt, model.c,model.h, rule=DC_Water_rule)

    ### PATCH ###  regional water-availability constraint (water-scarcity / Pareto analysis, Eq. 82-84 of the manuscript)
    #   TotalWater[g,t] = indirect (power + hydrogen plants) + direct (data-centre cooling), in ML/yr  <=  eps[g,t]
    if cfg['water_eps'] is not None:
        def WaterAvail_rule(model, g, t):
            lhs = sum(model.WF[c] * (sum(model.Water[j, g, t, c, h] for j in WATER_TECHS) + model.Water_DC[g, t, c, h])
                      for c in model.c for h in model.h)
            return lhs / 1.0e6 <= cfg['water_eps'][(g, t)]
        model.WaterAvail = Constraint(model.g, model.ttt, rule=WaterAvail_rule)
        

    def MaxDC_rule(model,t):
          #if t in model.TT:
              return sum (model.CapDC[t,g] for g in model.g)<= 1.2*sum(model.DCCap_max[t,g] for g in model.g)
          #return Constraint.Skip
    model.MaxCapDCCON=Constraint(model.ttt,rule=MaxDC_rule)
     
    def MaxDC_rule1(model,t):
          #if t in model.TT:
              return sum (model.CapDC[t,g] for g in model.g)>=0.95*sum(model.DCCap_max[t,g] for g in model.g)
          #return Constraint.Skip
    model.MaxCapDCCON1=Constraint(model.ttt,rule=MaxDC_rule1)
     
    def Region1_rule(model,t,z):
        #if t in model.TT:
            return sum (model.CapDC[t,g] for g in ['NT', 'SO'])>=0.5*sum(model.DCCap_max[t,g] for g in model.g)
        #return Constraint.Skip
    model.Region11CON=Constraint(model.ttt,model.z,rule=Region1_rule)


    def Region2_rule(model,t,z):
        #if t in model.TT:
            return sum (model.CapDC[t,g] for g in ['WN'])<=0.1*sum(model.DCCap_max[t,g] for g in model.g)
        #return Constraint.Skip
    model.Region12CON=Constraint(model.ttt,model.z,rule=Region1_rule)




    '''
    def Region_rule1(model,t,z):
        if t in model.TT:
            return sum (model.CapDC[t,g] for g in ['NT', 'SE','EA'])<=0.7*(1+model.alpha[t,'LND'])*sum(model.DCCap_max[t,g] for g in model.g)
        return Constraint.Skip
    model.Region1CON=Constraint(model.ttt,model.z,rule=Region_rule1)

    def Region1_rule(model,t,z):
        if t in model.TT:
            return sum (model.CapDC[t,g] for g in ['NT', 'SE','EA'])>=0.5*(1+model.alpha[t,'LND'])*sum(model.DCCap_max[t,g] for g in model.g)
        return Constraint.Skip
    model.Region11CON=Constraint(model.ttt,model.z,rule=Region1_rule)

    def Region1_rule2(model,t,g):
        if t in model.TT:
            return model.CapDC[t,'NT'] >=0.3*sum(model.DCCap_max[t,g] for g in model.g)
        return Constraint.Skip
    model.Region11CON2=Constraint(model.ttt,model.g,rule=Region1_rule2)

    def Region2_rule2(model,t,g):
        if t in model.TT:
            return model.CapDC[t,'EA'] >=0.05*sum(model.DCCap_max[t,g] for g in model.g)
        return Constraint.Skip
    model.Region2CON2=Constraint(model.ttt,model.g,rule=Region2_rule2)


    def Region_rule2(model,t,z):
        if t in model.TT:
            return sum (model.CapDC[t,g] for g in ['SO'])<=(1+model.alpha[t,'Slough'])*0.5*sum(model.DCCap_max[t,g] for g in model.g)
        return Constraint.Skip
    model.Region2CON=Constraint(model.ttt,model.z,rule=Region_rule2)

    def Region_rule22(model,t,z):
        if t in model.TT:
            return sum (model.CapDC[t,g] for g in ['SO'])>=0.4*sum(model.DCCap_max[t,g] for g in model.g)
        return Constraint.Skip
    model.Region22CON=Constraint(model.ttt,model.z,rule=Region_rule22)

    def Region_rule3(model,t,z):
        if t in model.TT:
            return sum (model.CapDC[t,g] for g in ['WS','WN'])<=(1+model.alpha[t,'Wales'])*0.1*sum(model.DCCap_max[t,g] for g in model.g)
        return Constraint.Skip
    model.Region3CON=Constraint(model.ttt,model.z,rule=Region_rule3)


    def Region_rule4(model,t,z):
        if t in model.TT:
            return sum (model.CapDC[t,g] for g in ['SW','NW','NE','NO','SC'])<=(1+model.alpha[t,'AI Zone'])*0.2*sum(model.DCCap_max[t,g] for g in model.g)
        return Constraint.Skip
    model.Region4CON=Constraint(model.ttt,model.z,rule=Region_rule4)

    def Region_rule5(model,t,z):
        if t in model.TT:
            return sum (model.CapDC[t,g] for g in ['WM', 'EM'])<=(1+model.alpha[t,'Manchester'])*0.05*sum(model.DCCap_max[t,g] for g in model.g)
        return Constraint.Skip
    model.Region5CON=Constraint(model.ttt,model.z,rule=Region_rule5)

    def Region_rule6(model,t,g):
        if t in model.TT and g in ['SC']:
            return model.CapDC[t,g] <=0.05*sum(model.DCCap_max[t,g] for g in model.g)
        return Constraint.Skip
    model.Region6CON=Constraint(model.ttt,model.z,rule=Region_rule6)

    for t in model.ttt:
        model.CapDC[t,'WN'] = 0


            
    def Relax_rule(model,t):
        return sum(model.alpha[t,z] for z in model.z)==0
    model.RelaxCON=Constraint(model.t,rule=Relax_rule)
    '''
           

    #%%DAC
    def heat_refuce_rule(model,g,t,c,h):
        return model.TDemandDC[g,t,c,h]*0.6>=model.H_DAC[g,t,c,h]
    #model.HeatRefuceCon=Constraint(model.g,model.ttt, model.c,model.h, rule=heat_refuce_rule)



    def heatDemand_DAC_rule(model,g,t,c,h):
        return model.H_DAC[g,t,c,h]==model.hc_dac[t]*model.DAC[g,t,c,h]
    #model.HeatDACCon=Constraint(model.g,model.ttt, model.c,model.h, rule=heatDemand_DAC_rule)

    def ElecDemand_DAC_rule(model,g,t,c,h):
        return model.E_DAC[g,t,c,h]==model.ec_dac[t]*model.DAC[g,t,c,h]
    #model.ElecDACCon=Constraint(model.g,model.ttt, model.c,model.h, rule=ElecDemand_DAC_rule)


    def DACMax_rule(model,g,t):
        return sum (model.WF[c]*model.DAC[g,t,c,h] for c in model.c for h in model.h)<=model.CAPDAC[g,t]
    #model.DACMAXCon=Constraint(model.g,model.ttt, rule=DACMax_rule)


    from pyomo.environ import value

    def CAPDAC_rule(model, g, t):
        t0 = 5   # numeric value

        #if t in model.TT:
        return  model.CAPDAC[g,t] == (
                (model.CAPDAC[g,t-1] if t>model.y1 else 0)
                + model.CAPDACnew[g,t] 
                - model.DCAPDAC[g,t]
                - (model.CAPDACnew[g,t-t0] if t-t0  in model.ttt else 0)
            )
        #return Constraint.Skip
     
    #model.CAPDACCON = Constraint(model.g, model.ttt, rule=CAPDAC_rule)




    #%%
    def total_elec_demand_rule(model, g, t, c, h):
        #if t in model.TT and c in model.c and h in model.h:
            return model.totdem_elec[g,t,c,h] == (
                model.TPowerDem[g,t,c,h]+model.TDemandDC[g,t,c,h]+
                + sum(model.P[j,g,t,c,h]/model.eta[j,t] for j in model.j if ('Elec', j) in model.jf)
                + model.hedem_elec[g,t,c,h]/model.COP[g,c,h]#+(model.H_DAC[g,t,c,h]-model.TDemandDC[g,t,c,h])/model.COP[g,c,h]
                + model.indem_elec[g,t,c,h]
            )
        #return Constraint.Skip

    model.TotalElecDemand = Constraint(model.g, model.ttt, model.c, model.h, rule=total_elec_demand_rule)

    def total_hydro_demand_rule(model, g, t, c, h):
        #if t in model.TT and c in model.c and h in model.h:
            return model.totdem_hydro[g,t,c,h] == (
                sum(model.P[j,g,t,c,h]/model.eta[j,t] for j in model.j if ('GH2', j) in model.jf)
                + (model.hedem_hydro[g,t,c,h] + model.indem_hydro[g,t,c,h]) / model.eta_Heat['HyBoiler',t]
            )
        #return Constraint.Skip

    model.TotalHydroDemand = Constraint(model.g, model.ttt, model.c, model.h, rule=total_hydro_demand_rule)

    def total_gas_demand_rule(model, g, t, c, h):
        #if t in model.TT and c in model.c and h in model.h:
            return model.totdem_gas[g,t,c,h] == (
                (model.hedem_gas[g,t,c,h] + model.indem_gas[g,t,c,h]) / model.eta_Heat['GasBoiler',t]
            )
       # return Constraint.Skip

    model.TotalGasDemand = Constraint(model.g, model.ttt, model.c, model.h, rule=total_gas_demand_rule)


    #%%
    #Electricity Balance
    def elec_balance_rule(model, f, g, t, c, h):
        if  f == 'Elec':
            return (
                sum(model.P[j, g, t, c, h] for j in model.j if j in model.jep) +
                sum(model.Qelec[g1, g, t, c, h] for g1 in model.g if (g1, g) in model.N) +
                sum(model.DC[j, g, t, c, h] for j in model.jes) +
                sum((1 - model.loss[i]) * model.IMPe[i, g, t, c, h] for i in model.i if ('Elec', i, g) in model.GimpE) +
                model.LS[g, t, c, h]
                ==
                sum(model.Qelec[g, g1, t, c, h] for g1 in model.g if (g, g1) in model.N) +
                sum(model.CH[j, g, t, c, h] for j in model.jes) +
                model.LC[g, t, c, h] +
                model.totdem_elec[g, t, c, h]
            )
        return Constraint.Skip

    model.ElecBalance = Constraint(model.f, model.g, model.ttt, model.c, model.h, rule=elec_balance_rule)


    #%%
    # Hydrogen Balance
    def hydro_balance_rule(model, f, g, t, c, h):
        if  f == 'GH2':
            return (
                sum(model.P[j, g, t, c, h] for j in model.j if j in model.jhp) +
                sum(model.Qpipe[f, g1, g, t, c, h] for g1 in model.g if (g1, g) in model.Npipe) +
                sum(model.DC[jhs, g, t, c, h] for jhs in model.jhs if (g, jhs) in model.GJh)
                ==
                sum(model.Qpipe[f, g, g1, t, c, h] for g1 in model.g if (g, g1) in model.Npipe) +
                sum(model.CH[jhs, g, t, c, h] for jhs in model.jhs if (g, jhs) in model.GJh) +
                model.totdem_hydro[g, t, c, h]
            )
        return Constraint.Skip

    model.HydroBalance = Constraint(model.f, model.g, model.ttt, model.c, model.h, rule=hydro_balance_rule)


    #%%
    #CO2 Balance
    def co2_balance_rule(model, f, g, t, c, h):
        if  f == 'CO2':
            return (
                sum(model.Qpipe[f, g1, g, t, c, h] for g1 in model.g if (g1, g) in model.N) +
                sum(model.yc[jccs] * model.P[jccs, g, t, c, h] for jccs in model.jccs)
                ==
                sum(model.Qpipe[f, g, g1, t, c, h] for g1 in model.g if (g, g1) in model.N) +
                sum(model.Qres[g, r, t, c, h] for r in model.r if (g, r) in model.GR)
            )
        return Constraint.Skip

    model.CO2Balance = Constraint(model.f, model.g, model.ttt, model.c, model.h, rule=co2_balance_rule)


    #%%
    from pyomo.environ import value

    def ElecInv1_rule(model, jth, g, t):
        t0 = value(model.LT[jth]) / 5   # numeric value

        #if t in model.TT:
        return  model.NU[jth,g,t] == (
                (model.NUint[jth,g] if  (t==model.y1 and t<=t0) else 0)
                - (model.NUint[jth,g] if t==t0 else 0)
                + (model.NU[jth,g,t-1] if t>model.y1 else 0)
                + model.NUF[jth,t,g] 
                + model.CU[jth,g,t] 
                - model.DU[jth,g,t]
                - (model.CU[jth,g,t-t0] if t-t0 in model.ttt else 0)
            )
        #return Constraint.Skip
     
    model.ElecInv1 = Constraint(model.jth, model.g, model.ttt, rule=ElecInv1_rule)


    from pyomo.environ import value

    def ElecInv2_rule(model, j, g, t):
        if  (j in model.jre or j in model.jes):
            t0 = value(model.LT[j]) / 5  # numeric shift
            return model.CAP[j, g, t] == (
                (model.Capinit[j, g] if t == model.y1 else 0)
                + (model.CAP[j, g, t-1] if t > model.y1 else 0)
                + (model.Capf[j, t, g] if  j in ['Solar', 'WindOff'] else 0)
                + model.CAPnew[j, g, t]
                - model.DCAP[j, g, t]
                - (model.CAPnew[j, g, t - t0] if (t - t0) in model.ttt else 0)
            )
        return Constraint.Skip

    model.ElecInv2 = Constraint(model.j, model.g, model.ttt, rule=ElecInv2_rule)





    def Buildrate_rule(model, j,t):
        if  j in ['SMRCCS','ATRCCS','BGCCS','WE','MPSV','HPSV','FC','H2CCGT','Nuclear','OCGT','CCGTCCS','BECCS','Biomass','CCGT']:
            return sum(model.CU[j,g,t]*model.Capunit[j] for g in model.g) <= model.BR[j,t]
        return Constraint.Skip
    model.BuildrateCon= Constraint(model.j, model.ttt, rule=Buildrate_rule)

    def Build2_rule(model,j,t):
        if (j in model.jre or j in model.jes):
            return sum(model.CAPnew[j,g,t] for g in model.g)<= model.BR[j,t]
        return Constraint.Skip
    model.Build2Con=Constraint(model.j,model.ttt, rule=Build2_rule)

    def LandAvailability_rule(model,jre,g,t):
        if  jre in ['Solar', 'WindOn', 'WindOff']:
            return model.CAP[jre,g,t]<= (model.LandAvailability[jre,g]+model.Capinit[jre,g])
        return Constraint.Skip
    model.LandAVCon=Constraint(model.jre,model.g, model.ttt, rule=LandAvailability_rule)
    #%%
    # Fuel consumption for power generation and hydrogen production units

    def Fuel_rule(model,f,j,g,t):
        if  (f,j) in model.jf:
            return model.Vf[f,j,g,t]==sum(model.WF[c]*model.P[j,g,t,c,h]/model.eta[j,t] for c in model.c for h in model.h)
        return Constraint.Skip
    model.FuelCon=Constraint(model.f,model.j,model.g,model.ttt, rule=Fuel_rule)



    #%% Power generation

    def ThermalCap1_rule(model,j,g,t,c,h):
        if  j in ['Nuclear']:
            return model.P[j,g,t,c,h]>= model.Pmin[j]*model.Capunit[j]*model.NU[j,g,t]
        return Constraint.Skip
    model.ThermalCap1Con=Constraint(model.j,model.g,model.ttt,model.c,model.h,rule=ThermalCap1_rule)

    def ThermalCap2_rule(model,j,g,t,c,h):
        if j in model.jth:
            return model.P[j,g,t,c,h]<= model.Pmax[j]*model.Capunit[j]*model.NU[j,g,t]
        return Constraint.Skip
    model.ThermalCap2Con=Constraint(model.j,model.g,model.ttt,model.c,model.h,rule=ThermalCap2_rule)

    def ReCap_rule(model,j,g,t,c,h):
        if  j in model.jre:
            return model.P[j,g,t,c,h]==model.AV[c,h,g,j]*model.CAP[j,g,t]
        return Constraint.Skip
    model.ReCapCon=Constraint(model.j,model.g,model.ttt,model.c,model.h, rule=ReCap_rule)

    def Curtailment_rule (model,g,t,c,h):
        #if t in model.TT:
            return model.LC[g,t,c,h]<= sum(model.P[j,g,t,c,h] for j in model.j if j in model.jre)
        #return Constraint.Skip
    model.CurtailCon=Constraint(model.g,model.ttt,model.c,model.h, rule=Curtailment_rule)
    
    #%% Water Consumption
    def Water_Consumption_rule(model,j,g,t,c,h):
        if j in ['FC', 'H2CCGT', 'Nuclear', 'OCGT', 'CCGTCCS', 'BECCS', 'Biomass', 'CCGT', 'SMRCCS', 'ATRCCS', 'BGCCS', 'WE']:
            return model.Water[j,g,t,c,h]==model.W[j]*model.P[j,g,t,c,h]
        return Constraint.Skip
    model.WaterCon=Constraint(model.j,model.g, model.ttt,model.c,model.h, rule=Water_Consumption_rule)


    #%% Thermal Ramp Constraints
    h_list = list(model.h)  
    h_index = {h:i for i,h in enumerate(h_list)} 


    def ThermalRampUp_rule(model, j,g,t,c,h):
        if  h_index[h] > 0 and j in ['FC','H2CCGT','Nuclear','CCGTCCS','OCGT','BECCS', 'Biomass', 'CCGT', 'SMRCCS', 'ATRCCS', 'BGCCS','WE']:
            prev_h = h_list[h_index[h]-1]  
            return model.P[j,g,t,c,h] - model.P[j,g,t,c,prev_h] <= model.RU[j]*model.Capunit[j]*model.NU[j,g,t]
        return Constraint.Skip
    model.thermalRampCON=Constraint(model.j,model.g,model.ttt,model.c,model.h, rule=ThermalRampUp_rule)
        
    def ThermalRampDown_rule(model, j,g,t,c,h):
        if  h_index[h] > 0 and j in ['FC','H2CCGT','Nuclear','CCGTCCS','OCGT','BECCS', 'Biomass', 'CCGT', 'SMRCCS', 'ATRCCS', 'BGCCS','WE']:
            prev_h = h_list[h_index[h]-1]  
            return model.P[j,g,t,c,prev_h] - model.P[j,g,t,c,h] <= model.RD[j]*model.Capunit[j]*model.NU[j,g,t]
        return Constraint.Skip
    model.thermalRampdownCON=Constraint(model.j,model.g,model.ttt,model.c,model.h, rule=ThermalRampDown_rule)
          


    #%% *Capacity of the transmission
    def TrCapacity_rule(model,f,g,g1,t,c,h):
        if f in ['Elec'] and (g,g1) in model.N:
            return model.Qelec[g,g1,t,c,h]<= model.TRCnew[g,g1,t]
        return Constraint.Skip
    model.TrCapacityCon=Constraint(model.f,model.N,model.ttt,model.c,model.h, rule=TrCapacity_rule)


        
    def TrInvest_rule(model, g, g1, t):
        if (g, g1) in model.N :
            
            return model.TRCnew[g, g1, t] ==(model.TRC[g,g1] if t==model.y1 else 0)
        + (model.TRCnew[g, g1, t-1] if t> model.y1 else 0)
        + model.TRI[g, g1, t]
        return Constraint.Skip

    model.TrInvest = Constraint(model.N, model.ttt, rule=TrInvest_rule)

        
    '''
    def TrInvest_rule(model, g, g1, t):
        if t in model.TT and (g, g1) in model.N:
            i = t_index[t]
            if i == 0:  # first period
                prev_val = 0
            else:
                prev_t = t_list[i-1]
                prev_val = model.TRC[g, g1, prev_t]
            return model.TRC[g, g1, t] == prev_val + model.TRI[g, g1, t]
        return Constraint.Skip

    model.TrInvest = Constraint(model.N, model.ttt, rule=TrInvest_rule)
    '''


    def TrInvest2_rule(model,g,g1,t):
        if  (g,g1) in model.N:
            return model.TRCnew[g,g1,t]==model.TRCnew[g1,g,t]
        return Constraint.Skip
    model.TrInvest2Con= Constraint(model.N,model.ttt,rule=TrInvest2_rule)

    def TrInvestUp_rule(model,g,g1,t):
        if  (g,g1) in model.N:
            return model.TRI[g,g1,t]<=model.triup
        return Constraint.Skip
    model.TrInvestUpCon= Constraint(model.N,model.ttt,rule=TrInvestUp_rule)


    def InterCapacity1_rule(model,f,i,g,t,c,h):
        if f in ['Elec'] and (f,i,g) in model.GimpE:
            return model.IMPe[i,g,t,c,h]<= model.ICap[i,g,t]
        return Constraint.Skip
    model.InterCapacity1Con= Constraint(model.f,model.i,model.g, model.ttt,model.c,model.h, rule=InterCapacity1_rule)

    def InterCapacity2_rule(model,f,i,g,t,c,h):
        if f in ['Elec'] and (f,i,g) in model.GimpE:
            return model.IMPe[i,g,t,c,h]>= -model.ICap[i,g,t]
        return Constraint.Skip
    model.InterCapacity2Con= Constraint(model.f,model.i,model.g, model.ttt,model.c,model.h, rule=InterCapacity2_rule)



    #%% Energy Storage
    def ChargeBound_rule(model,jes,g,c,h,t):
        #if t in model.TT:
            return model.CH[jes,g,t,c,h]<=model.CAP[jes,g,t]
        #return Constraint.Skip
    model.ChargeBoundCon=Constraint(model.jes,model.g,model.c,model.h,model.ttt, rule=ChargeBound_rule)

    def DischargeBound_rule(model,jes,g,c,h,t):
        #if t in model.TT:
            return model.DC[jes,g,t,c,h]<=model.CAP[jes,g,t]
        #return Constraint.Skip
    model.DischargeBoundCon=Constraint(model.jes,model.g,model.c,model.h,model.ttt, rule=DischargeBound_rule)

    def StorageCap_rule(model,jes,g,t,c,h,per):
        if  (c,per) in model.CP:
            return model.S[jes,g,t,c,h]+model.BS[jes,g,t,per]<=model.EtP[jes]*model.CAP[jes,g,t]
        return Constraint.Skip
    model.StorageCapCon= Constraint(model.jes,model.g,model.ttt,model.c,model.h,model.per, rule=StorageCap_rule)


    # build list + index for h
    h_list = list(model.h)
    h_index = {h: i for i, h in enumerate(h_list)}

    def StorageLevel_rule(model, jes, g, t, c, h):

        idx = h_index[h]

        if idx > 0:

            prev_h = h_list[idx - 1]

            return (
                model.S[jes, g, t, c, h]
                ==
                (1 - model.etasef[jes])
                * model.S[jes, g, t, c, prev_h]

                + model.eta[jes, t]
                * model.CH[jes, g, t, c, h]

                - model.DC[jes, g, t, c, h]
                / model.eta[jes, t]
            )

        return Constraint.Skip

    model.StorageLevelCon = Constraint(
        model.jes,
        model.g,
        model.ttt,
        model.c,
        model.h,
        rule=StorageLevel_rule
    )
    
    
    




    #%%PEAK DEMAND
    def PeakDemand_rule(model,t,c,h):
        #if t in model.TT:
            return model.PeakDemand[t]>= sum(model.totdem_elec[g,t,c,h] for g in model.g)
        #return Constraint.Skip
    model.PeakDemandCon=Constraint(model.ttt,model.c,model.h, rule=PeakDemand_rule)

    def Reserve_ruel(model,t):
        #if t in model.TT:
            return sum(model.drf[jth]*model.Capunit[jth]*model.NU[jth,g,t] for jth in model.jth for g in model.g)\
                +sum(model.drf[j]*model.CAP[j,g,t] for j in['WindOn', 'WindOff','Solar', 'Hydro', 'LeadBat', 'PumpHy'] for g in model.g)\
                    +sum(model.drfl[i]*model.ICap[i,g,t] for i in model.i for g in model.g for f in model.f if f in ['Elec'] and (f,i,g) in model.GimpE )\
                        + model.RMslack[t] >= (1+model.CM)*model.PeakDemand[t]
        #return Constraint.Skip
    model.ReserveCon= Constraint(model.ttt, rule=Reserve_ruel)



    #%%
    #def HydrogenCap1_rule(model,jhp,g,t,c,h):
       # if t in model.TT :
           # return model.P[jhp,g,t,c,h]>= model.Pmin[jhp]*model.Capunit[jhp]*model.NU[jhp,g,t]
        #return Constraint.Skip
    #model.HydrogenCap1Con=Constraint(model.jhp,model.g,model.ttt,model.c,model.h,rule=HydrogenCap1_rule)

    # Ordered list of time periods


    from pyomo.environ import value

    def HydroInv_rule(model, jh, g, t):
        t0 = value(model.LT[jh]) / 5   # numeric value

        if (g, jh) in model.GJh:
            return model.NU[jh, g, t] == (
                (model.NU[jh, g, t-1] if t > model.y1 else 0)
                + (model.NUF[jh, t, g] if jh in ['WE'] else 0)
                + model.CU[jh, g, t]
                - (model.CU[jh, g, t-t0] if t-t0 in model.ttt else 0)
            )
        return Constraint.Skip

    model.HydroInv = Constraint(model.jh, model.g, model.ttt, rule=HydroInv_rule)





    '''
    def HydroInv_rule(model, jh, g, t):
        # Only define constraint if time step and GJh exist
        if t in model.TT and (g, jh) in model.GJh:
            LTjh = model.LT[jh].value
            t1 = model.ord_t[t] - model.dur.value // 5
            t2 = model.ord_t[t] - LTjh // 5

            return model.NU[jh, g, t] == (
                (model.NU[jh, g, t1] if model.ord_t[t] > model.y1 and t1 in model.ttt else 0)
                + model.NUF[jh, t, g]
                + model.CU[jh, g, t]
                - (model.CU[jh, g, t2] if t2 in model.ttt else 0)
            )
        return Constraint.Skip

    model.HydroInv = Constraint(model.jh, model.g, model.ttt, rule=HydroInv_rule)

    '''


    def HydrogenCap2_rule(model,jhp,g,t,c,h):
        #if t in model.TT :
            return model.P[jhp,g,t,c,h]<= model.Pmax[jhp]*model.Capunit[jhp]*model.NU[jhp,g,t]
        #return Constraint.Skip
    model.HydrogenCap2Con=Constraint(model.jhp,model.g,model.ttt,model.c,model.h,rule=HydrogenCap2_rule)


    h_list = list(model.h)  
    h_index = {h:i for i,h in enumerate(h_list)} 

    def HydrogenRampDown_rule(model, jhp,g,t,c,h):
        if  h_index[h] > 0:
            prev_h = h_list[h_index[h]-1]  
            return model.P[jhp,g,t,c,prev_h] - model.P[jhp,g,t,c,h] <= model.RD[jhp]*model.Capunit[jhp]*model.NU[jhp,g,t]
        return Constraint.Skip
    model.HydrogenRampdownCON=Constraint(model.jhp,model.g,model.ttt,model.c,model.h, rule=HydrogenRampDown_rule)
      


    def HydrogenRampUP_rule(model, jhp,g,t,c,h):
        if  h_index[h] > 0:
            prev_h = h_list[h_index[h]-1]  
            return model.P[jhp,g,t,c,h]- model.P[jhp,g,t,c,prev_h]  <= model.RD[jhp]*model.Capunit[jhp]*model.NU[jhp,g,t]
        return Constraint.Skip
    model.HydrogenRampUPCON=Constraint(model.jhp,model.g,model.ttt,model.c,model.h, rule=HydrogenRampUP_rule)
      

    #%% Hydrogen Storage
    def HydrogenSCap1_rule(model,jhs,g,t,c,h,per):
        if  (c,per) in model.CP and (g,jhs) in model.GJh:
            return model.S[jhs,g,t,c,h]+model.BS[jhs,g,t,per]<=model.Stmax[jhs]*model.Capunit[jhs]*model.NU[jhs,g,t]
        return Constraint.Skip
    model.HydroSCap1CON= Constraint(model.jhs,model.g,model.ttt,model.c, model.h,model.per, rule=HydrogenSCap1_rule)


    def HydrogenSCap2_rule(model,jhs,g,t,c,h,per):
        if  (c,per) in model.CP and (g,jhs) in model.GJh:
            return model.S[jhs,g,t,c,h]+model.BS[jhs,g,t,per]>=model.Stmin[jhs]*model.Capunit[jhs]*model.NU[jhs,g,t]
        return Constraint.Skip
    model.HydroSCap2CON= Constraint(model.jhs,model.g,model.ttt,model.c, model.h,model.per, rule=HydrogenSCap2_rule)

    def MaxInj_rule(model,f,jhs,g,t,c,h):
        if  f in ['GH2'] and (g,jhs) in model.GJh:
            return model.CH[jhs,g,t,c,h]<=model.CHmax[jhs]
        return Constraint.Skip
    model.MaxInjCON= Constraint(model.f,model.jhs,model.g,model.ttt,model.c,model.h, rule=MaxInj_rule)

    def MaxRet_rule(model,f,jhs,g,t,c,h):
        if  f in ['GH2'] and (g,jhs) in model.GJh:
            return model.DC[jhs,g,t,c,h]<=model.DHmax[jhs]
        return Constraint.Skip
    model.MaxRetCON= Constraint(model.f,model.jhs,model.g,model.ttt,model.c,model.h, rule=MaxRet_rule)


    # build list + index for h
    h_list = list(model.h)
    h_index = {h: i for i, h in enumerate(h_list)}

    def HydStorageLevel_rule(model, jhs, g, t, c, h):

        idx = h_index[h]

        if idx == 0:
            return Constraint.Skip

        prev_h = h_list[idx - 1]

        return (
            model.S[jhs, g, t, c, h]
            ==
            (1 - model.etasef[jhs]) * model.S[jhs, g, t, c, prev_h]
            + model.eta[jhs, t] * model.CH[jhs, g, t, c, h]
            - model.DC[jhs, g, t, c, h] / model.eta[jhs, t]
        )

    model.HydStorageLevelCon = Constraint(
        model.jhs,
        model.g,
        model.ttt,
        model.c,
        model.h,
        rule=HydStorageLevel_rule
    )
    
    

    # %%  RESERVIORS Constraints ---------------------
    # Inventory 
    def res_inventory_rule(model, r, t):
        #if t in model.TT: 
           
            return model.RI[r, t] == (
                model.RI[r, t-1] if  t > model.y1 else model.ri0[r]
            ) + model.dur * sum(
                model.WF[c] * model.Qres[(g, r), t, c, h] 
                for g in model.g if (g, r) in model.GR
                for c in model.c for h in model.h
            )
        #return Constraint.Skip

    model.ResInventoryConstraint = Constraint(model.r, model.ttt, rule=res_inventory_rule)


    def ResCapacity_rule(model,r,t):
        #if t in model.TT:
            return 0.001*model.RI[r,t]<=0.001*model.rcap[r]
        #return Constraint.Skip
    model.ResCapacityCON=Constraint(model.r,model.ttt, rule=ResCapacity_rule)


    #%% BIOMASS AVAILABILITY
    def BioAvailability_rule(model,g,t):
        #if t in model.TT:
            return 0.001*sum (model.Vf['Bio', j,g,t] for j in model.jb) <= 0.001*0.5*1000000*model.breg[g]*model.Vbiomax[t]
        #return Constraint.Skip
    model.BioAvailCON=Constraint(model.g,model.ttt, rule=BioAvailability_rule)


    #%%INTERSEASONAL STORAGE
    def BSeq1_rule(model, j, g, t):
        if  (j in model.jhs or j in model.jes):
            return model.BS[j, g, t, 'p1'] == model.BS[j, g, t, 'p8'] \
                 + model.WF['c6'] * (model.S[j, g, t, 'c6', 'h24'] - model.S[j, g, t, 'c6', 'h1'])
        return Constraint.Skip
    model.BSeq1 = Constraint(model.j, model.g, model.ttt, rule=BSeq1_rule)

    def BSeq2_rule(model, j, g, t):
        if  (j in model.jhs or j in model.jes):
            return model.BS[j, g, t, 'p2'] == model.BS[j, g, t, 'p1'] \
                 + 18 * (model.S[j, g, t, 'c3', 'h24'] - model.S[j, g, t, 'c3', 'h1'])
        return Constraint.Skip
    model.BSeq2 = Constraint(model.j, model.g, model.ttt, rule=BSeq2_rule)

    def BSeq3_rule(model, j, g, t):
        if  (j in model.jhs or j in model.jes):
            return model.BS[j, g, t, 'p3'] == model.BS[j, g, t, 'p2'] \
                 + 1 * (model.S[j, g, t, 'c1', 'h24'] - model.S[j, g, t, 'c1', 'h1'])
        return Constraint.Skip
    model.BSeq3 = Constraint(model.j, model.g, model.ttt, rule=BSeq3_rule)

    def BSeq4_rule(model, j, g, t):
        if  (j in model.jhs or j in model.jes):
            return model.BS[j, g, t, 'p4'] == model.BS[j, g, t, 'p3'] \
                 + 5 * (model.S[j, g, t, 'c3', 'h24'] - model.S[j, g, t, 'c3', 'h1'])
        return Constraint.Skip
    model.BSeq4 = Constraint(model.j, model.g, model.ttt, rule=BSeq4_rule)

    def BSeq5_rule(model, j, g, t):
        if  (j in model.jhs or j in model.jes):
            return model.BS[j, g, t, 'p5'] == model.BS[j, g, t, 'p4'] \
                 + 1 * (model.S[j, g, t, 'c2', 'h24'] - model.S[j, g, t, 'c2', 'h1'])
        return Constraint.Skip
    model.BSeq5 = Constraint(model.j, model.g, model.ttt, rule=BSeq5_rule)

    def BSeq6_rule(model, j, g, t):
        if  (j in model.jhs or j in model.jes):
            return model.BS[j, g, t, 'p6'] == model.BS[j, g, t, 'p5'] \
                 + 65 * (model.S[j, g, t, 'c3', 'h24'] - model.S[j, g, t, 'c3', 'h1'])
        return Constraint.Skip
    model.BSeq6 = Constraint(model.j, model.g, model.ttt, rule=BSeq6_rule)

    def BSeq7_rule(model, j, g, t):
        if  (j in model.jhs or j in model.jes):
            return model.BS[j, g, t, 'p7'] == model.BS[j, g, t, 'p6'] \
                 + model.WF['c4'] * (model.S[j, g, t, 'c4', 'h24'] - model.S[j, g, t, 'c4', 'h1'])
        return Constraint.Skip
    model.BSeq7 = Constraint(model.j, model.g, model.ttt, rule=BSeq7_rule)

    def BSeq8_rule(model, j, g, t):
        if  (j in model.jhs or j in model.jes):
            return model.BS[j, g, t, 'p8'] == model.BS[j, g, t, 'p7'] \
                 + model.WF['c5'] * (model.S[j, g, t, 'c5', 'h24'] - model.S[j, g, t, 'c5', 'h1'])
        return Constraint.Skip
    model.BSeq8 = Constraint(model.j, model.g, model.ttt, rule=BSeq8_rule)


    #%% EMISSION

    def ElecEmissions_rule(model, t):
        #if t in model.TT:
            return 0.001*model.Ee[t] == 0.001*sum(
                model.WF[c] * model.ye[j] * model.P[j, g, t, c, h]
                for j in model.j if j in ['FC', 'Biomass', 'BECCS', 'CCGT', 'CCGTCCS', 'OCGT', 'Nuclear']
                for g in model.g
                for c in model.c
                for h in model.h
            )
        #return Constraint.Skip
    model.ElecEmissionsCon = Constraint(model.ttt, rule=ElecEmissions_rule)


    def H2Emissions_rule(model, t):
        #if t in model.TT:
            return model.Eh[t] == sum(
                model.WF[c] * model.ye[j] * model.P[j, g, t, c, h]
                for j in model.j if j in ['SMRCCS', 'ATRCCS', 'BGCCS', 'WE']
                for g in model.g
                for c in model.c
                for h in model.h
            )
        #return Constraint.Skip
    model.H2EmissionsCon = Constraint(model.ttt, rule=H2Emissions_rule)


    def GasEmissions_rule(model, t):
        #if t in model.TT:
            return 0.001*model.Eg[t] == 0.001*sum(
                model.WF[c] * 0.203 * model.totdem_gas[g, t, c, h]
                for g in model.g
                for c in model.c
                for h in model.h
            )
        #return Constraint.Skip
    model.GasEmissionsCon = Constraint(model.ttt, rule=GasEmissions_rule)


    def TotEmissions_rule(model, t):
        #if t in model.TT:
            return model.Etotal[t] == model.Ee[t] + model.Eh[t] + model.Eg[t]
        #return Constraint.Skip
    model.TotEmissionsCon = Constraint(model.ttt, rule=TotEmissions_rule)


    def TotEmissionsTarget_rule(model, t):
        #if t in model.TT:
            return model.Etotal[t] <= model.et[t]
        #return Constraint.Skip
    model.TotEmissionsTargetCon = Constraint(model.ttt, rule=TotEmissionsTarget_rule)

    model.Ee1=Var(model.t,model.g)
    model.Eh1=Var(model.t,model.g)
    model.Eg1=Var(model.t,model.g)

    def ElecEmissions1_rule(model, t,g):
        #if t in model.TT:
            return 0.001*model.Ee1[t,g] == 0.001*sum(
                model.WF[c] * model.ye[j] * model.P[j, g, t, c, h]
                for j in model.j if j in ['FC', 'Biomass', 'BECCS', 'CCGT', 'CCGTCCS', 'OCGT', 'Nuclear']
               
                for c in model.c
                for h in model.h
            )
        #return Constraint.Skip
    model.ElecEmissionsCon1 = Constraint(model.ttt,model.g, rule=ElecEmissions1_rule)


    def H2Emissions1_rule(model, t,g):
        #if t in model.TT:
            return model.Eh1[t,g] == sum(
                model.WF[c] * model.ye[j] * model.P[j, g, t, c, h]
                for j in model.j if j in ['SMRCCS', 'ATRCCS', 'BGCCS', 'WE']
               
                for c in model.c
                for h in model.h
            )
        #return Constraint.Skip
    model.H2EmissionsCon1 = Constraint(model.ttt, model.g,rule=H2Emissions1_rule)


    def GasEmissions1_rule(model, t,g):
        #if t in model.TT:
            return 0.001*model.Eg1[t,g] == 0.001*sum(
                model.WF[c] * 0.203 * model.totdem_gas[g, t, c, h]
                
                for c in model.c
                for h in model.h
            )
       # return Constraint.Skip
    model.GasEmissionsCon1 = Constraint(model.ttt,model.g, rule=GasEmissions1_rule)



    #%% Heat Technology
    # Assume TT is ordered
    from pyomo.environ import value

    def HeatInv_rule(model, jhe, g, t):
        t0 = value(model.LT_heat[jhe]) / 5  # numeric shift
        if  jhe in model.JJHE:
            return model.CAPheat[jhe, g, t] == (
                (model.Capinit[jhe, g] if t == model.y1 else 0)
                + (model.CAPheat[jhe, g, t-1] if t > model.y1 else 0)
                + model.CAPheat_new[jhe, g, t]
                - model.DCheat[jhe, g, t]
                - (model.CAPheat_new[jhe, g, t - t0] if (t - t0) in model.ttt else 0)
            )
        return Constraint.Skip

    model.HeatInv = Constraint(model.jhe, model.g, model.ttt, rule=HeatInv_rule)



    '''
    t_list = list(model.ttt)
    ord_to_t = {i+1: t for i, t in enumerate(t_list)}  # map ord(t) back to t label

    def HeatInv_rule(model, jhe, g, t):
        if t not in model.ttt or jhe not in model.JJHE:
            return Constraint.Skip

        t_shift = model.ord_t[t] - model.dur / 5
        prev_t = ord_to_t[t_shift] if t_shift in ord_to_t else None

        return model.CAPheat[jhe, g, t] == (
            (model.Capinit[jhe, g] if model.ord_t[t] == model.y1 else 0)
            + (model.CAPheat[jhe, g, prev_t] if prev_t else 0)
            + model.CAPheat_new[jhe, g, t]
            - (model.CAPheat_new[jhe, g, prev_t] if prev_t else 0)
            - model.DCheat[jhe, g, t]
        )

    model.HeatInv = Constraint(model.JJHE, model.g, model.ttt, rule=HeatInv_rule)
    '''


    def Boiler_rule(model,jhe,g,t):
        if jhe in ['GasBoiler']:
            return model.CAPheat['GasBoiler', g, 6]== 0
        return Constraint.Skip
    model.BoilerCons=Constraint(model.jhe, model.g, model.ttt, rule=Boiler_rule)




    def HeatCap_rule(model,g,t,c,h):
        #if t in model.TT:
            return sum(model.CAPheat[jhe,g,t] for jhe in model.jhe if jhe in model.JJHE) ==model.THeatDem_max[g,t]
        #return Constraint.Skip
    model.HeatCapCON=Constraint(model.g,model.ttt, model.c,model.h, rule=HeatCap_rule)

    def ElecHeat_rule(model,g,t,c,h):
        #if t in model.TT:
            return sum(model.CAPheat[jhe,g,t] for jhe in model.jhe for f in ['Elec'] if (jhe,f) in model.jhef and jhe in model.JJHE)>= model.hedem_elec[g,t,c,h]
        #return Constraint.Skip
    model.ElecHeatCON= Constraint(model.g,model.ttt,model.c,model.h, rule=ElecHeat_rule)

    def HyHeat_rule(model,g,t,c,h):
        #if t in model.TT:
            return sum(model.CAPheat[jhe,g,t] for jhe in model.jhe for f in ['GH2'] if (jhe,f) in model.jhef and jhe in model.JJHE)>= model.hedem_hydro[g,t,c,h]
        #return Constraint.Skip
    model.HyHeatCON= Constraint(model.g,model.ttt,model.c,model.h, rule=HyHeat_rule)

    def GasHeat_rule(model,g,t,c,h):
        #if t in model.TT:
            return sum(model.CAPheat[jhe,g,t] for jhe in model.jhe for f in ['Gas'] if (jhe,f) in model.jhef and jhe in model.JJHE)>= model.hedem_gas[g,t,c,h]
        #return Constraint.Skip
    model.GasHeatCON= Constraint(model.g,model.ttt,model.c,model.h, rule=GasHeat_rule)
    #%% PIPELINE CONSTRAINTS------------------------
    #------Hydrogen Pipeline Limit ------

    # Maximum flowrate for pipelines

    def h2pipe_max_rule(model,f, d,g, g1, t, c, h):
        if (g, g1) in model.Npipe and f in ['GH2'] and (d,f) in model.df:
            return 0.001*model.Qpipe[f, (g, g1), t, c, h] <= 0.001*model.qHmax[d,f] * (
                (model.AY[f,d, (g, g1), t] if model.ord_g[g] < model.ord_g[g1] else 0)+
                (model.AY[f,d, (g1, g), t] if model.ord_g[g1] < model.ord_g[g] else 0) 
                )
                
        return Constraint.Skip

    model.H2PipeMax = Constraint(model.f, model.d,model.Npipe, model.ttt, model.c, model.h, rule=h2pipe_max_rule)



    def onshorepipe_max_rule(model, f, d2, g, g1, t, c, h):
        if (g, g1) in model.N and  f in ['CO2'] and (d2,f) in model.df:
            return 0.001*model.Qpipe[f,g, g1, t, c, h] <= 0.001*model.qCmax[d2,f] * (
                    (model.AY1[f,d2, g, g1, t] if model.ord_g[g] < model.ord_g[g1] else 0) +
                    (model.AY1[f,d2, g1, g, t] if model.ord_g[g1] < model.ord_g[g] else 0)
                )
               
        return Constraint.Skip

    model.OnshorePipeMax = Constraint(model.f, model.d2, model.N, model.ttt, model.c, model.h, rule=onshorepipe_max_rule)



    def offshorepipe_max_rule(model, f,d2,g, r, t, c, h):
        if (g, r) in model.GR and  f in ['CO2']  and (d2,f) in model.df:
            return 0.001*model.Qres[(g, r), t, c, h]  <= 0.001*model.qCmax[d2,f] * model.AYres[d2, (g, r), t] 
        return Constraint.Skip
    model.OffshorePipeMax = Constraint(model.f,model.d2, model.GR, model.ttt, model.c, model.h, rule=offshorepipe_max_rule)




    # Availability of pipelines
    # Create a list and index for TT
    t_list = list(model.ttt)
    t_index = {t: i for i, t in enumerate(t_list)}

    def H2PAvailability_rule(model, f, d, g, g1, t):
        if (g, g1) in model.Npipe  and f in ['GH2'] and (d, f) in model.df and model.ord_g[g] < model.ord_g[g1]:
            # previous time index
            prev_t = t_list[t_index[t] - 1] if t_index[t] > 0 else None
            
            # lag time for LTpipe/dur
            lag_offset = int(model.LTpipe / model.dur)
            lag_t = t_list[t_index[t] - lag_offset] if t_index[t] >= lag_offset else None

            return model.AY[f, d, g, g1, t] == (
                (model.AY[f, d, g, g1, prev_t] if prev_t else 0) 
                + (model.ayHR0[d, g, g1] if model.ord_t[t] == model.y1 else 0)
                + model.Y[f, d, g, g1, t]
                - (model.Y[f, d, g, g1, lag_t] if lag_t and model.ord_t[t] > model.y1 else 0)
            )
        return Constraint.Skip

    model.H2PAvailability = Constraint(model.f, model.d, model.Npipe, model.ttt, rule=H2PAvailability_rule)


    def onp_availability_rule(model, f, d2, g, g1, t):
        if (g, g1) in model.N  and f in ['CO2'] and (d2, f) in model.df and model.ord_g[g] < model.ord_g[g1]:
            # previous time index
            prev_t = t_list[t_index[t] - 1] if t_index[t] > 0 else None
            
            # lag time for LTpipe/dur
            lag_offset = int(model.LTpipe / model.dur)
            lag_t = t_list[t_index[t] - lag_offset] if t_index[t] >= lag_offset else None

            return model.AY1[f, d2, g, g1, t] == (
                (model.AY1[f, d2, g, g1, prev_t] if prev_t else 0) 
                + (model.ayC0[d2, g, g1] if model.ord_t[t] == model.y1 else 0)
                + model.Y1[f, d2, g, g1, t]
                - (model.Y1[f, d2, g, g1, lag_t] if lag_t and model.ord_t[t] > model.y1 else 0)
            )
        return Constraint.Skip

    model.onp_availability = Constraint(model.f, model.d2, model.N, model.ttt, rule=onp_availability_rule)



    def offp_availability_rule(model, f, d2, g, r, t):
        if (g, r) in model.GR  and f in ['CO2'] and (d2, f) in model.df:
            # previous time index
            prev_t = t_list[t_index[t] - 1] if t_index[t] > 0 else None
            
            # lag time for LTpipe/dur
            lag_offset = int(model.LTpipe / model.dur)
            lag_t = t_list[t_index[t] - lag_offset] if t_index[t] >= lag_offset else None

            return model.AYres[ d2, g, r, t] == (
                (model.AYres[ d2, g, r, prev_t] if prev_t else 0) 
                + (model.aeC0[r] if model.ord_t[t] == model.y1 else 0)
                + model.Yres[ d2, g, r, t]
                - (model.Yres[ d2, g, r, lag_t] if lag_t and model.ord_t[t] > model.y1 else 0)
            )
        return Constraint.Skip

    model.offp_availability = Constraint(model.f, model.d2, model.GR, model.ttt, rule=offp_availability_rule)


    # Create t_list and t_index if not already done
    t_list = list(model.ttt)
    t_index = {t: i for i, t in enumerate(t_list)}

    def PipeStAvailability_rule(model, f, d, g, jhs, t):
        if (g, jhs) in model.GJh and f in ['GH2'] and (d, f) in model.df and jhs in ['OnTeeside', 'OnChesire', 'OnYorkshire', 'OffIrishSea']:
            # previous time index
            prev_t = t_list[t_index[t] - 1] if t_index[t] > 0 else None
            
            # lag for LTpipe/dur + dur/5
            lag_offset = int(model.LTpipe / model.dur + model.dur / 5)
            lag_t = t_list[t_index[t] - lag_offset] if t_index[t] >= lag_offset else None

            return model.AYst[d, g, jhs, t] == (
                (model.AYst[d, g, jhs, prev_t] if prev_t else 0)
                + model.Yst[d, g, jhs, t]
                - (model.Yst[d, g, jhs, lag_t] if lag_t and model.ord_t[t] > model.y1 else 0)
            )
        return Constraint.Skip

    model.PipeStAvailability = Constraint(model.f, model.d, model.g, model.jhs, model.ttt, rule=PipeStAvailability_rule)


    def CavernPipe_rule(model, jhs, g, t, f):
        if  (g, jhs) in model.GJh and f in ['GH2'] and jhs in ['OnTeeside', 'OnChesire', 'OnYorkshire', 'OffIrishSea']:
            return model.CU[jhs, g, t] <= sum(
                model.Yst[d, g, jhs, t] for d in model.d if (d, f) in model.df
            )
        return Constraint.Skip

    model.CavernPipeCon = Constraint(model.jhs, model.g, model.ttt, model.f, rule=CavernPipe_rule)



    # One diameter size
    def h2pipe_rule(model, g, g1, t,f):
         if (g,g1) in model.Npipe and model.ord_g[g] < model.ord_g[g1]  and f in ['GH2']:   
           return sum(model.AY[f, d, (g, g1), t] for d in model.d if (d,f) in model.df) <= 1
         return Constraint.Skip
    model.H2Pipe = Constraint(model.Npipe, model.ttt,model.f, rule=h2pipe_rule)



    def onpipe_rule(model, g, g1, t,f):
        if (g, g1) in model.N and model.ord_g[g] < model.ord_g[g1]  and f in ['CO2']:
            return sum(model.AY1[f,d2, g, g1, t] for d2 in model.d2 if (d2,f) in model.df) <= 1
        return Constraint.Skip

    model.OnPipeConstraint = Constraint(model.N, model.ttt,model.f, rule=onpipe_rule)



    def offpipe_rule(model, g, r, t,f):
         if (g,r) in model.GR  and f in ['CO2']:  
            return sum(model.AYres[d2, (g, r), t] for d2 in model.d2 if (d2,f) in model.df) <= 1
         return Constraint.Skip
    model.OffPipe = Constraint(model.GR, model.ttt,model.f, rule=offpipe_rule)

    def stpipe_rule(model, g, jhs, t,f):
        if (g,jhs) in model.GJh  and f in ['GH2'] and jhs in ['OnTeeside', 'OnChesire', 'OnYorkshire', 'OffIrishSea']:
            return sum(model.AYst[d, (g, jhs), t] for d in model.d if (d,f) in model.df) <= 1
        return Constraint.Skip
    model.StPipe = Constraint(model.g,model.jhs, model.ttt,model.f, rule=stpipe_rule)



    #%% UPPER BOUND

    for jhs in model.jhs:
        for g in model.g:
            for t in model.ttt:
                if model.ord_jhs[jhs] <= 4 and (g, jhs) in model.GJh:
                    model.CU[jhs, g, t].setub(1)

                if (g, jhs) not in model.GJh:
                    model.CU[jhs, g, t].setub(0)

    # Specific technologies banned
    for g in model.g:
        for t in model.ttt:
            model.CU['OCGT', g, t].setub(0)
            model.CU['CCGT', g, t].setub(0)
            model.CU['Biomass', g, t].setub(0)
            model.CAPnew['Hydro', g, t].setub(0)
            model.CAPheat_new['GasBoiler', g, t].setub(0)

     
    ### PATCH ###  DAC is not part of this analysis (its constraints are commented out in the uploaded code): keep it at zero
    for g in model.g:
        for t in model.t:
            model.CAPDACnew[g, t].setub(0)

    ### PATCH ###  renewable build-out requirement (sensitivity): sum_g CAPnew >= fraction x build rate
    if cfg['ren_min_frac'] > 0:
        def RenMin_rule(model, j, t):
            return sum(model.CAPnew[j, g, t] for g in model.g) >= cfg['ren_min_frac'] * model.BR[j, t]
        model.RenMin = Constraint(['Solar', 'WindOn', 'WindOff'], model.ttt, rule=RenMin_rule)

    return model
     #%%


def safe_value(v):

    try:

        val = value(v)

        # ignore uninitialized variables
        if val is None:
            return None

        return val

    except:
        return None


# =========================================================
# VARIABLE MAP
# =========================================================
def get_vars_map(model):

    return {

        # H2 pipelines
        "Y": model.Y,
        #"AY": model.AY,

        # Onshore CO2
        "Y1": model.Y1,
        #"AY1": model.AY1,

        # Offshore CO2
        "Yres": model.Yres,
        #"AYres": model.AYres,

        # Storage
        "Yst": model.Yst,
        #"AYst": model.AYst,

        # Heat
        #"CAPheat": model.CAPheat,
        "CAPheat_new": model.CAPheat_new,
        #"DCheat": model.DCheat,

        # Hydro
        #"NU": model.NU,
        "CU": model.CU,
        #"DU": model.DU,

        # Electricity
        #"CAP": model.CAP,
        "CAPnew": model.CAPnew,
        #"DCAP": model.DCAP,

        # Data centres
        #"CapDC": model.CapDC,
        "CapDCNew": model.CapDCNew,
        
        # DAC
        #"CAPDAC": model.CAPDAC,
        #"DAC": model.DAC,
        "CAPDACnew": model.CAPDACnew,
        
        #"TRI": model.TRI,
        
       
    }


# =========================================================
# =========================  INTEGRATED DRIVER  ===========
# =========================================================
# Everything below replaces the old 'SETTINGS / ROLLING HORIZON LOOP / result-export' blocks.

WATER_TECHS = ['FC', 'H2CCGT', 'Nuclear', 'OCGT', 'CCGTCCS', 'BECCS', 'Biomass', 'CCGT',
               'SMRCCS', 'ATRCCS', 'BGCCS', 'WE']      # technologies with a water factor (same list as WaterCon)
YEAR_LABEL = {1: 2025, 2: 2030, 3: 2035, 4: 2040, 5: 2045, 6: 2050}
YEAR_LABEL.update(YEAR_LABEL_OVERRIDE)
COOLING_LABEL = {'air': 'Air-cooled', 'water': 'Water-cooled', 'liquid': 'D2C', 'none': 'Without DC'}


def _v(x):
    """Numeric value of a Pyomo Var/Param/float (None -> 0.0)."""
    try:
        if hasattr(x, "value"):
            x = x.value
        return 0.0 if x is None else float(x)
    except Exception:
        return 0.0


def _p(x):
    """Numeric value of a (non-mutable) Pyomo Param entry."""
    try:
        return float(value(x))
    except Exception:
        return float(x)


# =========================================================
# 1.  SOLVE ONE CASE (myopic rolling horizon, as in the original script)
# =========================================================
def _safe(tag):
    return "".join(ch if ch.isalnum() or ch in "-_." else "_" for ch in tag)


def _cfg_suffix():
    return "_H%d_S%d_L%d%s%s" % (HL_MAX, ROLL_STEP, LOOKAHEAD, "r" if RELAX_LOOKAHEAD_INTEGERS else "", "s" if SOFT_RESERVE_MARGIN else "")


def _ckpt_path(tag, hl):
    return os.path.join(OUT_DIR, "cache", "ckpt_%s%s_hl%d.pkl" % (_safe(tag), _cfg_suffix(), hl))


_INT_VARS = {'DU': 2, 'CU': 2, 'ITU': 2, 'u': 2, 'v': 2, 'w': 2, 'Y': -1, 'Y1': -1, 'Yres': -1, 'Yst': -1}
# position of the planning-step index t inside the variable index tuple


def relax_integers_after(model, t_ctrl):
    """Relax every integer / binary variable of the periods t > t_ctrl (the look-ahead periods) to continuous.
    Bounds are kept (binary -> [0,1]). The control periods (t <= t_ctrl) keep their integer / binary domains."""
    n, failed = 0, 0
    for name, pos in _INT_VARS.items():
        var = getattr(model, name, None)
        if var is None:
            continue
        for idx, vd in var.items():
            try:
                t = idx[pos]
                if not isinstance(t, int) or t <= t_ctrl or vd.fixed:
                    continue
                was_binary = vd.is_binary()
                vd.domain = Reals if name == 'ITU' else NonNegativeReals
                if was_binary:
                    vd.setlb(0)
                    vd.setub(1)
                n += 1
            except Exception:
                failed += 1
    print("   relaxed %d integer/binary variables of the look-ahead periods (t > %d)%s" %
          (n, t_ctrl, (" - %d could not be relaxed" % failed) if failed else ""))
    return n


def solve_case(cfg, tag, mono=False):
    """Rolling horizon with look-ahead (see settings).  Iteration: fix the periods up to new_fix = fixed_upto + ROLL_STEP,
    optimise the periods up to horizon = new_fix + la (integers of the look-ahead periods relaxed).  If an iteration is
    infeasible and ADAPTIVE_LOOKAHEAD is on, the previous iteration is undone (checkpoint), la is increased by one and the
    iteration is repeated with the wider look-ahead."""
    fixed_values = {}
    fixed_upto = HL_INIT - 1
    la = LOOKAHEAD
    if SAVE_CHECKPOINTS and not mono:
        for h in range(HL_MAX - 1, HL_INIT - 1, -1):          # latest checkpoint before the final iteration
            p = _ckpt_path(tag, h)
            if os.path.exists(p):
                with open(p, "rb") as f:
                    fixed_values = pickle.load(f)
                fixed_upto = h
                print("Resuming %s from checkpoint: periods up to t = %d are fixed" % (tag, h))
                break
    last_model, status, gaps = None, "not_run", []
    step_log = []
    while fixed_upto < HL_MAX:
        new_fix = HL_MAX if mono else min(fixed_upto + ROLL_STEP, HL_MAX)
        horizon = HL_MAX if mono else min(new_fix + la, HL_MAX)
        print("\n=== %s | fix periods up to t = %d | optimise periods up to t = %d (look-ahead %d) | HL_MAX = %d ===" %
              (tag, new_fix, horizon, horizon - new_fix, HL_MAX))
        model = build_model(horizon, cfg)
        vars_map = get_vars_map(model)

        for (var_name, idx), val in fixed_values.items():
            if var_name in vars_map and val is not None:
                var_obj = vars_map[var_name]
                if idx in var_obj:
                    try:
                        var_obj[idx].fix(val)
                    except Exception:
                        pass

        if RELAX_LOOKAHEAD_INTEGERS and horizon > new_fix:
            relax_integers_after(model, new_fix)

        diag = bool(DIAGNOSE_RELAXED and new_fix == HL_MAX)
        if diag:
            TransformationFactory('core.relax_integer_vars').apply_to(model)
            print(">>> DIAGNOSE_RELAXED: integer variables relaxed at the last step (results will not be saved)")

        opt = SolverFactory('gurobi')
        opt.options['Threads'] = THREADS
        opt.options['Presolve'] = 2
        opt.options['MIPGap'] = MIPGAP
        opt.options['LogFile'] = os.path.join(OUT_DIR, "opt_%s.log" % _safe(tag))
        opt.options['BarHomogeneous'] = 1
        opt.options['NumericFocus'] = 1
        opt.options['IntegralityFocus'] = 1
        ilp = os.path.join(OUT_DIR, "infeasible_%s_t%d.ilp" % (_safe(tag), new_fix))
        if WRITE_IIS:
            opt.options['ResultFile'] = ilp
        if TIME_LIMIT:
            opt.options['TimeLimit'] = TIME_LIMIT

        t_start = time.time()
        ok, tc, results = False, None, None
        try:
            results = opt.solve(model, tee=SOLVER_TEE, symbolic_solver_labels=bool(WRITE_IIS))
            tc = results.solver.termination_condition
            status = str(tc)
            ok = tc in (TerminationCondition.optimal, TerminationCondition.feasible, TerminationCondition.maxTimeLimit)
        except Exception as e:                       # e.g. 'no solution loaded' for infeasible models
            print("Solve failed:", e)
            status = "failed"
        print("Termination condition:", status)
        minutes = (time.time() - t_start) / 60
        if diag:
            print(">>> Relaxed last step finished with status:", status)
            last_model = None
            break

        gap = float('nan')
        if ok:
            try:
                ub, lb = results.problem.upper_bound, results.problem.lower_bound
                gap = abs(ub - lb) / max(abs(ub), 1e-9)
            except Exception:
                pass
        step_log.append(dict(fix_up_to_t=new_fix, optimised_up_to_t=horizon, look_ahead=horizon - new_fix, status=status,
                             mip_gap=gap, minutes=minutes))

        if not ok:
            can_widen = bool(ADAPTIVE_LOOKAHEAD and not mono and la < MAX_LOOKAHEAD and la < HL_MAX - HL_INIT + 1)
            if can_widen:
                la += 1
                if fixed_upto > HL_INIT - 1:                   # undo the previous iteration (go back one checkpoint)
                    prev = max(fixed_upto - ROLL_STEP, HL_INIT - 1)
                    if prev >= HL_INIT:
                        p = _ckpt_path(tag, prev)
                        if SAVE_CHECKPOINTS and os.path.exists(p):
                            with open(p, "rb") as f:
                                fixed_values = pickle.load(f)
                        else:
                            print(">>> no checkpoint to go back to - cannot widen the look-ahead for %s" % tag)
                            last_model = None
                            break
                    else:
                        fixed_values = {}
                    fixed_upto = prev
                    for h in range(fixed_upto + 1, HL_MAX + 1):   # drop stale checkpoints of the abandoned attempt
                        p = _ckpt_path(tag, h)
                        if os.path.exists(p):
                            os.remove(p)
                print(">>> INFEASIBLE at fix-step t = %d: widening the look-ahead to %d and retrying from t = %d" %
                      (new_fix, la, fixed_upto))
                gaps = gaps[:max(fixed_upto - HL_INIT + 1, 0)]
                continue
            print(">>> INFEASIBLE / no solution at fix-step t = %d (horizon %d). Increase LOOKAHEAD / MAX_LOOKAHEAD or use "
                  "DIAGNOSE_FEASRELAX to see which constraints conflict." % (new_fix, horizon))
            last_model = None
            break
        gaps.append(gap)

        for var_name, var_obj in vars_map.items():
            for idx in var_obj.index_set():
                try:
                    if isinstance(idx, tuple):
                        if isinstance(idx[-1], int):
                            t = idx[-1]
                        elif isinstance(idx[0], int):
                            t = idx[0]
                        else:
                            continue
                    else:
                        if isinstance(idx, int):
                            t = idx
                        else:
                            continue
                except Exception:
                    continue
                if t <= new_fix:
                    val = safe_value(var_obj[idx])
                    if val is not None:
                        fixed_values[(var_name, idx)] = val
        fixed_upto = new_fix
        if SAVE_CHECKPOINTS and not mono:
            with open(_ckpt_path(tag, new_fix), "wb") as f:
                pickle.dump(fixed_values, f)
        last_model = model
    return last_model, status, gaps, step_log


# =========================================================
# 2.  EXTRACT RESULTS FROM A SOLVED MODEL
# =========================================================
def collect(model, cfg, tag, factor, status, gaps):
    """Return dict of small DataFrames (all for the final planning year T, plus annual flows for all years)."""
    ttt = list(model.ttt)
    T = max(ttt)
    G, C, H = list(model.g), list(model.c), list(model.h)
    WF = {c: _p(model.WF[c]) for c in C}
    cooling = cfg['cooling']
    no_dc = (cfg.get('dc_scale', 1.0) == 0)
    meta = dict(case=tag, cooling=COOLING_LABEL['none'] if no_dc else COOLING_LABEL.get(cooling, cooling), factor=factor)

    def add_meta(df):
        for k, v in reversed(list(meta.items())):
            df.insert(0, k, v)
        return df

    # ---------------- cost breakdown -----------------
    dfc = {t: _p(model.dfc[t]) for t in ttt}
    dfo = {t: _p(model.dfo[t]) for t in ttt}
    ccurt, cvoll = _p(model.ccurt), _p(model.cVOLL) * 2.0          # (the model multiplies VOLL by 2 in FOC_rule)
    curt_cost = {t: sum(WF[c] * ccurt * _v(model.LC[g, t, c, h]) for g in G for c in C for h in H) for t in ttt}
    voll_cost = {t: sum(WF[c] * cvoll * _v(model.LS[g, t, c, h]) for g in G for c in C for h in H) for t in ttt}
    FOC = {t: _v(model.FOC[t]) for t in ttt}
    comp_t = {}
    for t in ttt:
        comp_t[t] = {
            'CAPEX - facilities (generation, storage, H2, CCS units)': ('capex', _v(model.FCC[t])),
            'CAPEX - H2/CO2 pipelines and storage': ('capex', _v(model.PCC[t])),
            'CAPEX - electricity transmission': ('capex', _v(model.ETC[t])),
            'CAPEX - heating technologies': ('capex', _v(model.HC[t])),
            'OPEX - O&M and fuel of facilities': ('opex', FOC[t] - curt_cost[t] - voll_cost[t]),
            'OPEX - renewable curtailment penalty': ('opex', curt_cost[t]),
            'OPEX - load-shedding penalty (VOLL)': ('opex', voll_cost[t]),
            'OPEX - pipeline operation': ('opex', _v(model.POC[t])),
            'OPEX - carbon cost': ('opex', _v(model.CEC[t])),
            'OPEX - electricity and hydrogen imports': ('opex', _v(model.IIC[t])),
            'OPEX - gas for heating (fuel + network)': ('opex', _v(model.HGDC[t]) + _v(model.HGOC[t])),
        }
    flow_pen = 0.1 * sum(
        (_v(model.Qpipe['GH2', g, g1, t, c, h]) if (g, g1) in model.Npipe else 0.0)
        + (_v(model.Qpipe['CO2', g, g1, t, c, h]) if (g, g1) in model.N else 0.0)
        for g in G for g1 in G for t in ttt for c in C for h in H)
    rows = []
    names = list(comp_t[T].keys())
    for nme in names:
        kind = comp_t[T][nme][0]
        disc = sum((dfc[t] if kind == 'capex' else dfo[t]) * comp_t[t][nme][1] for t in ttt) / COST_DIV
        ann = comp_t[T][nme][1] / COST_DIV
        rows.append(dict(component=nme, type=kind, discounted_total_GBPbn=disc, annual_in_final_year_GBPbn=ann))
    rows.append(dict(component='Pipeline-flow penalty term in objective (0.1 x flows)', type='other',
                     discounted_total_GBPbn=flow_pen / COST_DIV, annual_in_final_year_GBPbn=float('nan')))
    obj_raw = _p(model.TC)
    tot_components = sum(r['discounted_total_GBPbn'] for r in rows)
    rows.append(dict(component='TOTAL (sum of components)', type='total', discounted_total_GBPbn=tot_components,
                     annual_in_final_year_GBPbn=float('nan')))
    rows.append(dict(component='Objective value (model.TC)', type='total', discounted_total_GBPbn=obj_raw / COST_DIV,
                     annual_in_final_year_GBPbn=float('nan')))
    df_cost = add_meta(pd.DataFrame(rows))

    # ---------------- annual flows (all years) -----------------
    ann = []
    for t in ttt:
        ls = sum(WF[c] * _v(model.LS[g, t, c, h]) for g in G for c in C for h in H)
        lc = sum(WF[c] * _v(model.LC[g, t, c, h]) for g in G for c in C for h in H)
        imp_pos = sum(WF[c] * max(_v(model.IMPe[i, g, t, c, h]), 0.0)
                      for (i, g) in [(i, g) for i in model.i for g in G] for c in C for h in H)
        imp_neg = sum(WF[c] * min(_v(model.IMPe[i, g, t, c, h]), 0.0)
                      for (i, g) in [(i, g) for i in model.i for g in G] for c in C for h in H)
        imph = sum(WF[c] * _v(model.IMPh[g, t, c, h]) for g in G for c in C for h in H)
        w_ind = sum(WF[c] * _v(model.Water[j, g, t, c, h]) for j in WATER_TECHS for g in G for c in C for h in H)
        w_dir = sum(WF[c] * _v(model.Water_DC[g, t, c, h]) for g in G for c in C for h in H)
        ddem = sum(WF[c] * _v(model.TDemandDC[g, t, c, h]) for g in G for c in C for h in H) if t in model.TT else 0.0
        ann.append(dict(year=YEAR_LABEL.get(t, t), t=t,
                        renewable_curtailment_TWh=lc / 1e6, load_shedding_GWh=ls / 1e3,
                        electricity_imports_TWh=imp_pos / 1e6, electricity_exports_TWh=-imp_neg / 1e6,
                        hydrogen_imports_TWh=imph / 1e6, carbon_emissions_Mt=_v(model.Etotal[t]) / 1e6,
                        DC_electricity_demand_TWh=ddem / 1e6,
                        indirect_water_1e9L=w_ind / 1e9, direct_DC_water_1e9L=w_dir / 1e9,
                        total_water_1e9L=(w_ind + w_dir) / 1e9, peak_demand_GW=_v(model.PeakDemand[t]) / 1e3, reserve_shortfall_GW=_v(model.RMslack[t]) / 1e3))
    df_ann = add_meta(pd.DataFrame(ann))

    # ---------------- generation by technology in final year -----------------
    gen = []
    for j in model.jep:
        gen.append(dict(sector='Electricity', technology=j,
                        TWh=sum(WF[c] * _v(model.P[j, g, T, c, h]) for g in G for c in C for h in H) / 1e6))
    for j in model.jes:
        gen.append(dict(sector='Electricity', technology=str(j) + ' (storage discharge)',
                        TWh=sum(WF[c] * _v(model.DC[j, g, T, c, h]) for g in G for c in C for h in H) / 1e6))
    for j in model.jhp:
        gen.append(dict(sector='Hydrogen', technology=j,
                        TWh=sum(WF[c] * _v(model.P[j, g, T, c, h]) for g in G for c in C for h in H) / 1e6))
    df_gen = add_meta(pd.DataFrame(gen))

    # ---------------- heat supply & regional shares in final year -----------------
    heat_e = sum(WF[c] * _v(model.hedem_elec[g, T, c, h]) for g in G for c in C for h in H) / 1e6
    heat_h = sum(WF[c] * _v(model.hedem_hydro[g, T, c, h]) for g in G for c in C for h in H) / 1e6
    heat_g = sum(WF[c] * _v(model.hedem_gas[g, T, c, h]) for g in G for c in C for h in H) / 1e6
    reg = []
    for g in G:
        he = sum(WF[c] * _v(model.hedem_elec[g, T, c, h]) for c in C for h in H)
        hh = sum(WF[c] * _v(model.hedem_hydro[g, T, c, h]) for c in C for h in H)
        hg = sum(WF[c] * _v(model.hedem_gas[g, T, c, h]) for c in C for h in H)
        tot = max(he + hh + hg, 1e-9)
        w_ind = sum(WF[c] * _v(model.Water[j, g, T, c, h]) for j in WATER_TECHS for c in C for h in H)
        w_dir = sum(WF[c] * _v(model.Water_DC[g, T, c, h]) for c in C for h in H)
        dc_cap = _v(model.CapDC[T, g]) if T in model.TT else 0.0
        dc_dem = sum(WF[c] * _v(model.TDemandDC[g, T, c, h]) for c in C for h in H) / 1e6 if T in model.TT else 0.0
        reg.append(dict(region=g,
                        heat_electrification_share=he / tot, heat_hydrogen_share=hh / tot, heat_gas_share=hg / tot,
                        heat_from_electricity_TWh=he / 1e6, heat_from_hydrogen_TWh=hh / 1e6,
                        indirect_water_1e9L=w_ind / 1e9, direct_DC_water_1e9L=w_dir / 1e9,
                        total_water_1e9L=(w_ind + w_dir) / 1e9, DC_capacity_MW=dc_cap, DC_demand_TWh=dc_dem))
    df_reg = add_meta(pd.DataFrame(reg))

    # ---------------- installed capacity in final year (GW) -----------------
    cap = []
    for j in list(model.jre) + list(model.jes):
        cap.append(dict(technology=j, GW=sum(_v(model.CAP[j, g, T]) for g in G) / 1e3))
    for j in model.jth:
        cap.append(dict(technology=j, GW=sum(_v(model.NU[j, g, T]) * _p(model.Capunit[j]) for g in G) / 1e3))
    for j in model.jhp:
        if j not in model.jth:
            cap.append(dict(technology=j, GW=sum(_v(model.NU[j, g, T]) * _p(model.Capunit[j]) for g in G) / 1e3))
    for j in model.jhe:
        cap.append(dict(technology='Heat: ' + str(j), GW=sum(_v(model.CAPheat[j, g, T]) for g in G) / 1e3))
    df_cap = add_meta(pd.DataFrame(cap))

    # ---------------- indirect water by technology (final year) -----------------
    wt = [dict(technology=j, water_1e9L=sum(WF[c] * _v(model.Water[j, g, T, c, h]) for g in G for c in C for h in H) / 1e9)
          for j in WATER_TECHS]
    df_wt = add_meta(pd.DataFrame(wt))

    # ---------------- water audit (reviewer 1, comment 1) -----------------
    it_kwh = sum(WF[c] * _v(model.CapDC[T, g]) * _p(model.DCProfile0[c, h]) * KWH_PER_MWH
                 for g in G for c in C for h in H) if T in model.TT else 0.0
    fac_kwh = sum(WF[c] * _v(model.TDemandDC[g, T, c, h]) * KWH_PER_MWH for g in G for c in C for h in H) if T in model.TT else 0.0
    w_dir_L = sum(WF[c] * _v(model.Water_DC[g, T, c, h]) for g in G for c in C for h in H)
    if cooling in ('air', 'water', 'liquid') and T in model.TT:
        wue_par = {'air': model.WUE_air, 'water': model.WUE_water, 'liquid': model.WUE_Liquid}[cooling]
        pue_par = {'air': model.PUE_air, 'water': model.PUE_water, 'liquid': model.PUE_Liquid}[cooling]
        num = sum(WF[c] * _v(model.CapDC[T, g]) * _p(model.DCProfile0[c, h]) * KWH_PER_MWH * _p(wue_par[c, h, g])
                  for g in G for c in C for h in H)
        pue_w = sum(WF[c] * _v(model.CapDC[T, g]) * _p(model.DCProfile0[c, h]) * _p(pue_par[c, h, g])
                    for g in G for c in C for h in H) / max(sum(WF[c] * _v(model.CapDC[T, g]) * _p(model.DCProfile0[c, h])
                                                                for g in G for c in C for h in H), 1e-9)
    else:
        num, pue_w = 0.0, float('nan')
    audit = dict(year=YEAR_LABEL.get(T, T),
                 DC_installed_IT_capacity_MW=sum(_v(model.CapDC[T, g]) for g in G) if T in model.TT else 0.0,
                 annual_IT_energy_TWh=it_kwh / 1e9, annual_facility_energy_TWh=fac_kwh / 1e9,
                 load_weighted_PUE=pue_w,
                 load_weighted_WUE_from_input_L_per_kWh=(num / it_kwh) if it_kwh > 0 else float('nan'),
                 direct_water_from_model_1e9L=w_dir_L / 1e9,
                 implied_WUE_model_water_over_IT_energy_L_per_kWh=(w_dir_L / it_kwh) if it_kwh > 0 else float('nan'),
                 direct_water_recomputed_1e9L=num / 1e9,
                 check_model_minus_recomputed_1e9L=(w_dir_L - num) / 1e9)
    df_audit = add_meta(pd.DataFrame([audit]))

    # ---------------- key numbers (one row per run) -----------------
    gen_e = sum(r['TWh'] for r in gen if r['sector'] == 'Electricity' and 'storage' not in r['technology'])
    gen_h = sum(r['TWh'] for r in gen if r['sector'] == 'Hydrogen')
    capd = {r['technology']: r['GW'] for r in cap}
    a = ann[-1]
    tot_w = a['total_water_1e9L']
    key = dict(meta)
    key.update(dict(HL_MAX=HL_MAX, roll_step=ROLL_STEP, lookahead=LOOKAHEAD, relax_lookahead_integers=RELAX_LOOKAHEAD_INTEGERS))
    key.update(dict(
        status=status, final_year=YEAR_LABEL.get(T, T), mip_gap_last_step=(gaps[-1] if gaps else float('nan')),
        objective_raw=obj_raw, total_cost_GBPbn=obj_raw / COST_DIV,
        capex_discounted_GBPbn=sum(r['discounted_total_GBPbn'] for r in rows if r['type'] == 'capex'),
        opex_discounted_GBPbn=sum(r['discounted_total_GBPbn'] for r in rows if r['type'] == 'opex'),
        curtailment_penalty_discounted_GBPbn=[r['discounted_total_GBPbn'] for r in rows if 'curtailment penalty' in r['component']][0],
        load_shedding_penalty_discounted_GBPbn=[r['discounted_total_GBPbn'] for r in rows if 'load-shedding' in r['component']][0],
        carbon_cost_discounted_GBPbn=[r['discounted_total_GBPbn'] for r in rows if 'carbon cost' in r['component']][0],
        import_cost_discounted_GBPbn=[r['discounted_total_GBPbn'] for r in rows if 'imports' in r['component']][0],
        renewable_curtailment_TWh=a['renewable_curtailment_TWh'], load_shedding_GWh=a['load_shedding_GWh'],
        electricity_imports_TWh=a['electricity_imports_TWh'], electricity_exports_TWh=a['electricity_exports_TWh'],
        peak_demand_GW=a['peak_demand_GW'], reserve_shortfall_GW=a['reserve_shortfall_GW'],
        electricity_generation_TWh=gen_e, hydrogen_generation_TWh=gen_h,
        DC_electricity_demand_TWh=a['DC_electricity_demand_TWh'],
        heat_from_electricity_TWh=heat_e, heat_from_hydrogen_TWh=heat_h, heat_from_gas_TWh=heat_g,
        heat_electrification_share=heat_e / max(heat_e + heat_h + heat_g, 1e-9),
        indirect_water_1e9L=a['indirect_water_1e9L'], direct_DC_water_1e9L=a['direct_DC_water_1e9L'],
        total_water_1e9L=tot_w,
        direct_share_of_total_water=(a['direct_DC_water_1e9L'] / tot_w) if tot_w > 0 else float('nan'),
        offshore_wind_GW=capd.get('WindOff', float('nan')), onshore_wind_GW=capd.get('WindOn', float('nan')),
        solar_GW=capd.get('Solar', float('nan')), battery_GW=capd.get('LeadBat', float('nan')),
        nuclear_GW=capd.get('Nuclear', float('nan')),
        ASHP_heat_capacity_GW=capd.get('Heat: ASHP', float('nan')),
        HyBoiler_heat_capacity_GW=capd.get('Heat: HyBoiler', float('nan')),
        implied_WUE_L_per_kWh=audit['implied_WUE_model_water_over_IT_energy_L_per_kWh'],
        load_weighted_WUE_input_L_per_kWh=audit['load_weighted_WUE_from_input_L_per_kWh'],
    ))
    df_key = pd.DataFrame([key])

    # total regional water (ML) per (g,t) - used to define the 100 % availability of the Pareto analysis
    water_ML = {}
    for g in G:
        for t in ttt:
            w = sum(WF[c] * (sum(_v(model.Water[j, g, t, c, h]) for j in WATER_TECHS) + _v(model.Water_DC[g, t, c, h]))
                    for c in C for h in H)
            water_ML[(g, t)] = w / 1e6
    return dict(key=df_key, cost=df_cost, annual=df_ann, generation=df_gen, regional=df_reg, capacity=df_cap,
                water_tech=df_wt, audit=df_audit, water_ML=water_ML)


# =========================================================
# 3.  RUN (with cache / resume) HELPERS
# =========================================================
def cache_path(tag):
    safe = "".join(ch if ch.isalnum() or ch in "-_." else "_" for ch in tag)
    return os.path.join(OUT_DIR, "cache", safe + _cfg_suffix() + ".pkl")


def _write_case_workbook(res, tag):
    os.makedirs(os.path.join(OUT_DIR, "cases"), exist_ok=True)
    pc = os.path.join(OUT_DIR, "cases", _safe(tag) + ".xlsx")
    names = {'key': 'Key', 'cost': 'Cost_Breakdown', 'annual': 'Annual_Flows', 'generation': 'Generation_final',
             'regional': 'Regional_final', 'capacity': 'Capacity_final', 'water_tech': 'Water_by_Tech_final',
             'audit': 'Water_Audit', 'steps': 'Solve_Log', 'limits': 'Water_Limits'}
    with pd.ExcelWriter(pc, engine='openpyxl') as xw:
        for k_, nm in names.items():
            if k_ in res and isinstance(res[k_], pd.DataFrame):
                res[k_].to_excel(xw, sheet_name=nm, index=False)
    return pc


def _infer_meta(bn, suffix):
    """Older cache files (made before the 'meta' entry existed) are recognised from their file name."""
    import re
    core = bn[:-len(suffix)]
    if core.endswith("_SMOKE"):
        core = core[:-6]
    m = re.match(r"^Base_(none|liquid)$", core)
    if m:
        return dict(kind='base', cool=m.group(1), factor=1.0)
    m = re.match(r"^Pareto_(air|water)_f(\d{3})$", core)
    if m:
        return dict(kind='pareto', cool=m.group(1), factor=int(m.group(2)) / 100.0)
    m = re.match(r"^Mono_(none|air|water|liquid)$", core)
    if m:
        return dict(kind='mono', cool=m.group(1))
    for case in SENS_CASES:
        for cool in ('none', 'liquid', 'air', 'water'):
            if core == _safe("Sens_%s_%s" % (case, cool)):
                return dict(kind='sens', case=case, cool=cool)
    return None


def _publish(res, tag):
    """After every finished run: (1) one Excel file for this case, (2) rebuild the master workbook from ALL finished runs."""
    try:
        print("   case workbook saved:", _write_case_workbook(res, tag))
    except Exception as e:
        print("   (could not write the single-case workbook: %s)" % e)
    try:
        rebuild_master_excel()
    except Exception as e:
        print("   (could not rebuild the master workbook: %s)" % e)
        traceback.print_exc()


def rebuild_master_excel(also_cases=False):
    """Rebuilds the master workbook from every cached finished run of the CURRENT settings (works at any time, also
    while a long run is still going and after an interruption; run the script with EXCEL_ONLY = True to refresh it)."""
    import glob
    suffix = _cfg_suffix() + ".pkl"
    base, pareto, sens, mono = {}, {}, {}, {}
    n = 0
    for f in sorted(glob.glob(os.path.join(OUT_DIR, "cache", "*" + suffix))):
        bn = os.path.basename(f)
        if bn.startswith("ckpt_") or (bn.endswith("_SMOKE" + suffix) != bool(SMOKE_TEST)):
            continue
        try:
            with open(f, "rb") as fh:
                res = pickle.load(fh)
        except Exception:
            continue
        m = res.get('meta') if isinstance(res, dict) else None
        if not m:
            m = _infer_meta(bn, suffix)
        if not m or not isinstance(res, dict) or 'key' not in res:
            print("   (skipped %s: not recognised)" % bn)
            continue
        n += 1
        if also_cases:
            try:
                _write_case_workbook(res, str(res['key'].loc[0, 'case']))
            except Exception as e:
                print("   (could not write the case workbook for %s: %s)" % (bn, e))
        kind = m.get('kind')
        if kind == 'base':
            base[m['cool']] = res
        elif kind == 'pareto':
            pareto.setdefault(m['cool'], {})[float(m['factor'])] = res
            if abs(float(m['factor']) - 1.0) < 1e-9:
                base[m['cool']] = res
        elif kind == 'sens':
            sens[(m['case'], m['cool'])] = res
        elif kind == 'mono':
            mono[m['cool']] = res
    for cool in SENS_COOLINGS:                           # the sensitivity 'Base' case is the baseline solve
        if cool in base and "Base" in SENS_CASES:
            sens[("Base", cool)] = base[cool]
    out = os.path.join(OUT_DIR, MASTER_XLSX_NAME.replace(".xlsx", "_SMOKE.xlsx") if SMOKE_TEST else MASTER_XLSX_NAME)
    try:
        write_excel(pareto, sens, out, base=base, mono=mono)
    except PermissionError:
        alt = out.replace(".xlsx", "_NEW.xlsx")
        print("   !! %s is open in Excel - writing %s instead (close the file to update the original)" % (out, alt))
        write_excel(pareto, sens, alt, base=base, mono=mono)
    print("   master workbook rebuilt from %d finished runs: %s" % (n, out))
    rows = []
    for d_ in list(base.values()) + [r for dd in pareto.values() for r in dd.values()] + list(sens.values()) + list(mono.values()):
        k_ = d_['key'].iloc[0]
        rows.append((str(k_.get('case')), str(k_.get('status')), k_.get('total_cost_GBPbn', float('nan')), k_.get('max_lookahead_used', float('nan'))))
    if rows:
        print("   ---- run summary (case | status | cost GBP bn | look-ahead used) ----")
        for r_ in sorted(set(rows)):
            print("   %-52s %-12s %10.1f %6s" % (r_[0][:52], r_[1][:12], r_[2] if r_[2] == r_[2] else float('nan'), r_[3]))


def run_case(cfg, tag, factor=1.0, mono=False, meta=None):
    """Solves one case (or loads it from the cache), saves it at once (cache + case workbook + master workbook).
    A case that cannot be solved is recorded as failed and the run simply continues with the next case."""
    p = cache_path(tag + ("_SMOKE" if SMOKE_TEST else ""))
    if os.path.exists(p):
        with open(p, "rb") as f:
            res = pickle.load(f)
        failed = res.get('water_ML') is None
        if not (failed and RETRY_FAILED):
            print("Loading cached result:", tag, "(failed)" if failed else "")
            if 'meta' not in res and meta:
                res['meta'] = meta
                with open(p, "wb") as f:
                    pickle.dump(res, f)
            return res
        print("Retrying the case that failed before:", tag)
    t0 = time.time()
    cool_label = COOLING_LABEL['none'] if cfg.get('dc_scale', 1.0) == 0 else COOLING_LABEL.get(cfg['cooling'], cfg['cooling'])
    try:
        model, status, gaps, step_log = solve_case(cfg, tag, mono)
        if model is None:
            res = dict(status=status, key=pd.DataFrame([dict(case=tag, cooling=cool_label, factor=factor, status=status)]))
        else:
            res = collect(model, cfg, tag, factor, status, gaps)
            res['status'] = status
            print("%s: objective (raw) = %.6g  ->  %.1f GBP bn (COST_DIV=%g) | %.1f min" %
                  (tag, res['key'].loc[0, 'objective_raw'], res['key'].loc[0, 'total_cost_GBPbn'], COST_DIV,
                   (time.time() - t0) / 60))
    except Exception as e:                      # never stop the whole job because of one case
        traceback.print_exc()
        print(">>> %s: unexpected error (%s). Skipping this case and continuing with the next one." % (tag, e))
        res = dict(status='error', meta=meta or dict(kind='other'),
                   key=pd.DataFrame([dict(case=tag, cooling=cool_label, factor=factor, status='error: %s' % str(e)[:120])]))
        res['key']['max_lookahead_used'] = float('nan')
        with open(p, "wb") as f:                # recorded in the Excel file; RETRY_FAILED makes the next start try it again
            pickle.dump(res, f)
        _publish(res, tag)
        return res
    res['key']['max_lookahead_used'] = max([r['look_ahead'] for r in step_log]) if step_log else float('nan')
    sl = pd.DataFrame(step_log)
    if len(sl):
        for k_, v_ in reversed([('case', tag), ('cooling', cool_label), ('factor', factor)]):
            sl.insert(0, k_, v_)
        res['steps'] = sl
    if cfg.get('water_eps') is not None:
        res['limits'] = pd.DataFrame([dict(case=tag, cooling=cool_label, factor=factor, region=g, t=t, year=YEAR_LABEL.get(t, t),
                                           water_limit_1e9L=v / 1000.0) for (g, t), v in cfg['water_eps'].items()])
    res['meta'] = meta or dict(kind='other')
    with open(p, "wb") as f:
        pickle.dump(res, f)
    _publish(res, tag)
    return res


def cool_cfg(cool, **mods):
    """'none' = scenario without data centres (dc_scale = 0); otherwise the cooling architecture."""
    cfg = dict(mods)
    if cool == 'none':
        cfg.update(cooling='liquid', dc_scale=0.0)
    else:
        cfg.update(cooling=cool)
    return cfg


def base_tag(cool):
    """One tag per baseline so that Table-2 baselines, Pareto 100 % and sensitivity 'Base' share the same solve."""
    return "Pareto_%s_f100" % cool if cool in ('air', 'water') else "Base_%s" % cool


def _base_meta(cool):
    return dict(kind='pareto' if cool in ('air', 'water') else 'base', cool=cool, factor=1.0)


def baseline_runs():
    out = {}
    for cool in BASE_COOLINGS:
        out[cool] = run_case(cool_cfg(cool), base_tag(cool), 1.0, meta=_base_meta(cool))
    return out


def pareto_for(cooling):
    """Baseline (100 %) + progressively tighter regional water limits. Returns {factor: result}."""
    out = {}
    base = run_case(cool_cfg(cooling), base_tag(cooling), 1.0, meta=_base_meta(cooling))
    out[1.0] = base
    if base.get('water_ML') is None:
        print("Baseline failed for", cooling)
        return out
    base_water = base['water_ML']
    for f in PARETO_FACTORS:
        if abs(f - 1.0) < 1e-9:
            continue
        eps = {k: f * v for k, v in base_water.items()}
        cfg = dict(cooling=cooling, water_eps=eps)
        res = run_case(cfg, "Pareto_%s_f%03d" % (cooling, round(100 * f)), f, meta=dict(kind='pareto', cool=cooling, factor=f))
        out[f] = res
        if res.get('water_ML') is None:
            print("Infeasible / failed at %.0f %% - stopping the Pareto loop for %s" % (100 * f, cooling))
            break
    return out


def sensitivity_runs():
    out = {}
    for case, mods in SENS_CASES.items():
        for cool in SENS_COOLINGS:
            cfg = cool_cfg(cool, **mods)
            if mods:
                out[(case, cool)] = run_case(cfg, "Sens_%s_%s" % (case, cool), 1.0, meta=dict(kind='sens', case=case, cool=cool))
            else:                                            # 'Base' re-uses the baseline solve
                out[(case, cool)] = run_case(cfg, base_tag(cool), 1.0, meta=_base_meta(cool))
    return out


def monolithic_runs():
    out = {}
    for cool in MONO_COOLINGS:
        out[cool] = run_case(cool_cfg(cool), "Mono_%s" % cool, 1.0, mono=True, meta=dict(kind='mono', cool=cool))
    return out


# =========================================================
# 4.  EXCEL EXPORT
# =========================================================
README_TEXT = [
    ["Sheet", "Content"],
    ["Key_Numbers", "One row per model run (all key numbers for the manuscript and the response letter)."],
    ["Rolling-horizon settings", "Key_Numbers columns HL_MAX, roll_step, lookahead and relax_lookahead_integers record the formulation (fixed ROLL_STEP periods per iteration, LOOKAHEAD further periods optimised but not fixed, their integers relaxed). All runs of one analysis must use the same values."],
    ["Summary_For_Reviewer", "100 % vs tightest feasible water limit: change in cost, cost components, curtailment, load shedding, imports, water."],
    ["F8_Air_*  /  F9_Water_*", "Data to redraw Fig. 8 (air-cooled) and Fig. 9 (water-cooled): cost-water Pareto, electricity mix, hydrogen mix, regional heat electrification / hydrogen shares, 100 % regional water availability."],
    ["Cost_Breakdown", "Discounted cost components (GBP bn) for every run (CAPEX, OPEX, penalties, carbon, imports)."],
    ["Annual_Flows", "Curtailment, load shedding, imports/exports, water (direct + indirect) for every planning year."],
    ["Generation_2050 / Capacity_2050 / Water_by_Tech_2050 / Regional_2050", "Final-year data by technology / region for every run."],
    ["Table2_Style / Increment_vs_NoDC / Config_Differences", "Table-2-style comparison of Without DC, air-cooled, water-cooled and D2C (absolute values, increments vs Without DC, and differences between configurations)."],
    ["Rolling_vs_Monolithic", "Only if RUN_MONOLITHIC = True: rolling-horizon vs monolithic results for every configuration."],
    ["Run_Settings", "All solver / rolling-horizon / unit settings, software versions and input-file stamps of this run."],
    ["Solve_Log", "Every rolling-horizon iteration of every run: status, MIP gap, minutes (infeasible levels are recorded here)."],
    ["Water_Limits", "Regional water limits (1e9 L) applied in every Pareto run."],
    ["Water_Audit", "Dimensional audit of direct DC water: IT energy, load-weighted WUE, implied WUE, recomputed vs model water (must agree)."],
    ["Sensitivity_HP_H2 / Sensitivity_Shift", "Heat-pump / hydrogen-boiler / renewable sensitivity and the D2C-minus-no-DC shift in each case."],
    ["Units", "Water_DC [L/h] = CapDC [MW IT] x Profile x WUE [L/kWh] x 1000 [kWh/MWh];  annual water = sum_c WF[c] x sum_h(...);  "
              "1e9 L = billion litres;  GW / TWh as labelled; costs are discounted model costs in GBP bn (objective / COST_DIV)."],
]


def _stack(results, field):
    dfs = [r[field] for r in results if field in r and isinstance(r[field], pd.DataFrame)]
    return pd.concat(dfs, ignore_index=True) if dfs else pd.DataFrame()


_H2_TECHS = ['SMRCCS', 'ATRCCS', 'BGCCS', 'WE']


def _ok(r):
    return r is not None and r.get('water_ML') is not None


def _metrics_from(res):
    k = res['key'].loc[0]
    au = res['audit'].loc[0] if 'audit' in res else None
    wt = res['water_tech'].set_index('technology')['water_1e9L'] if 'water_tech' in res else pd.Series(dtype=float)
    elec_w = wt[[t for t in wt.index if t not in _H2_TECHS]].sum()
    h2_w = wt[[t for t in wt.index if t in _H2_TECHS]].sum()
    reg = res['regional'].set_index('region')['DC_capacity_MW'] if 'regional' in res else pd.Series(dtype=float)
    tot = reg.sum()
    def share(regs):
        return 100 * reg.reindex(regs).fillna(0).sum() / tot if tot > 0 else float('nan')
    return {
        'Total cost (GBP bn)': k['total_cost_GBPbn'],
        'MIP gap, last step (%)': 100 * k['mip_gap_last_step'],
        'System peak (GW)': k['peak_demand_GW'],
        'Offshore wind (GW)': k['offshore_wind_GW'], 'Onshore wind (GW)': k['onshore_wind_GW'],
        'Solar (GW)': k['solar_GW'], 'Battery (GW)': k['battery_GW'], 'Nuclear (GW)': k['nuclear_GW'],
        'Electricity generation (TWh)': k['electricity_generation_TWh'],
        'Hydrogen generation (TWh)': k['hydrogen_generation_TWh'],
        'Heat from electricity (TWh)': k['heat_from_electricity_TWh'],
        'Heat from hydrogen (TWh)': k['heat_from_hydrogen_TWh'],
        'Heat from gas (TWh)': k['heat_from_gas_TWh'],
        'DC installed IT capacity (MW)': au['DC_installed_IT_capacity_MW'] if au is not None else float('nan'),
        'DC IT energy (TWh)': au['annual_IT_energy_TWh'] if au is not None else float('nan'),
        'DC facility electricity (TWh)': k['DC_electricity_demand_TWh'],
        'Direct DC water (1e9 L)': k['direct_DC_water_1e9L'],
        'Indirect water (1e9 L)': k['indirect_water_1e9L'],
        'Indirect water, electricity sector (1e9 L)': elec_w,
        'Indirect water, hydrogen sector (1e9 L)': h2_w,
        'Total water (1e9 L)': k['total_water_1e9L'],
        'Renewable curtailment (TWh)': k['renewable_curtailment_TWh'],
        'Load shedding (GWh)': k['load_shedding_GWh'],
        'Electricity imports (TWh)': k['electricity_imports_TWh'],
        'DC capacity share NT+SO+SW (%)': share(['NT', 'SO', 'SW']),
        'DC capacity share EA+SE (%)': share(['EA', 'SE']),
        'DC capacity SC (MW)': reg.get('SC', float('nan')),
    }


def _write_table2_style(xw, base):
    order = ['none', 'air', 'water', 'liquid']
    data = {COOLING_LABEL[c]: _metrics_from(base[c]) for c in order if c in base and _ok(base[c])}
    if not data:
        return
    df = pd.DataFrame(data)
    df.to_excel(xw, sheet_name="Table2_Style")
    if 'Without DC' in df.columns and df.shape[1] > 1:
        inc = df.drop(columns='Without DC').sub(df['Without DC'], axis=0)
        inc.to_excel(xw, sheet_name="Increment_vs_NoDC")
    diffs = {}
    for a, b in (('D2C', 'Air-cooled'), ('D2C', 'Water-cooled'), ('Water-cooled', 'Air-cooled')):
        if a in df.columns and b in df.columns:
            diffs["%s minus %s" % (a, b)] = df[a] - df[b]
    if diffs:
        pd.DataFrame(diffs).to_excel(xw, sheet_name="Config_Differences")


def _write_mono(xw, base, mono):
    rows = []
    cools = [c for c in MONO_COOLINGS if c in mono and c in base and _ok(mono[c]) and _ok(base[c])]
    ms = {c: (_metrics_from(base[c]), _metrics_from(mono[c])) for c in cools}
    for c in cools:
        for nme in ms[c][0]:
            r, m = ms[c][0][nme], ms[c][1][nme]
            rows.append(dict(configuration=COOLING_LABEL[c], metric=nme, rolling_horizon=r, monolithic=m, difference_mono_minus_rolling=m - r))
    if 'none' in ms:
        for c in [x for x in cools if x != 'none']:
            for nme in ('Electricity generation (TWh)', 'Indirect water (1e9 L)', 'Heat from electricity (TWh)', 'Total cost (GBP bn)'):
                r = ms[c][0][nme] - ms['none'][0][nme]
                m = ms[c][1][nme] - ms['none'][1][nme]
                rows.append(dict(configuration=COOLING_LABEL[c], metric="Increment vs Without DC: " + nme, rolling_horizon=r, monolithic=m, difference_mono_minus_rolling=m - r))
    for nme in ('Electricity generation (TWh)', 'Indirect water (1e9 L)', 'Heat from electricity (TWh)', 'Total cost (GBP bn)'):
        for a, b in (('liquid', 'air'), ('liquid', 'water')):
            if a in ms and b in ms:
                r = ms[a][0][nme] - ms[b][0][nme]
                m = ms[a][1][nme] - ms[b][1][nme]
                rows.append(dict(configuration="%s minus %s" % (COOLING_LABEL[a], COOLING_LABEL[b]), metric=nme, rolling_horizon=r, monolithic=m, difference_mono_minus_rolling=m - r))
    if rows:
        pd.DataFrame(rows).to_excel(xw, sheet_name="Rolling_vs_Monolithic", index=False)


def _settings_df():
    import platform, datetime
    rows = [("run_time", datetime.datetime.now().strftime("%Y-%m-%d %H:%M")), ("python", sys.version.split()[0]), ("platform", platform.platform())]
    for mod in ("pyomo", "gurobipy", "pandas", "openpyxl"):
        try:
            rows.append((mod + "_version", getattr(__import__(mod), "__version__", "n/a")))
        except Exception:
            rows.append((mod + "_version", "n/a"))
    try:
        import gurobipy as gp
        rows.append(("gurobi_version", ".".join(str(v) for v in gp.gurobi.version())))
    except Exception:
        pass
    for name in ("HL_MAX", "HL_INIT", "ROLLING", "ROLL_STEP", "LOOKAHEAD", "RELAX_LOOKAHEAD_INTEGERS", "MIPGAP", "TIME_LIMIT", "THREADS",
                 "COST_DIV", "KWH_PER_MWH", "SOFT_RESERVE_MARGIN", "RESERVE_PENALTY", "PARETO_FACTORS", "PARETO_COOLINGS", "BASE_COOLINGS", "SENS_COOLINGS", "SMOKE_TEST",
                 "RUN_BASELINES", "RUN_PARETO", "RUN_SENSITIVITY", "RUN_MONOLITHIC"):
        rows.append((name, str(globals().get(name))))
    rows.append(("SENS_CASES", str(globals().get("SENS_CASES"))))
    rows.append(("YEAR_LABEL", str(YEAR_LABEL)))
    for label, path_ in (("input_workbook", file_path), ("cooling_workbook", file_path3)):
        try:
            rows.append((label, "%s | %d bytes | modified %s" % (os.path.basename(path_), os.path.getsize(path_),
                         datetime.datetime.fromtimestamp(os.path.getmtime(path_)).strftime("%Y-%m-%d %H:%M"))))
        except Exception:
            rows.append((label, "n/a"))
    rows.append(("water_equation", "Water_DC [L/h] = CapDC [MW IT] x Profile x WUE [L/kWh] x 1000 (IT energy basis)"))
    return pd.DataFrame(rows, columns=["setting", "value"])


def write_excel(pareto, sens, path, base=None, mono=None):
    allres = []
    for cool, d in pareto.items():
        allres += [d[f] for f in sorted(d, reverse=True)]
    allres += list((base or {}).values()) + list(sens.values()) + list((mono or {}).values())
    seen, uniq = set(), []                       # the same solve can appear as baseline, Pareto 100 % and sensitivity 'Base'
    for r in allres:
        tg = r['key'].loc[0, 'case']
        if tg in seen:
            continue
        seen.add(tg)
        uniq.append(r)
    allres = uniq
    with pd.ExcelWriter(path, engine='openpyxl') as xw:
        pd.DataFrame(README_TEXT[1:], columns=README_TEXT[0]).to_excel(xw, sheet_name="README_Units", index=False)
        _settings_df().to_excel(xw, sheet_name="Run_Settings", index=False)
        key = _stack(allres, 'key')
        key.to_excel(xw, sheet_name="Key_Numbers", index=False)
        fc = [c for c in ('case', 'cooling', 'factor', 'status', 'HL_MAX', 'roll_step', 'lookahead', 'max_lookahead_used', 'mip_gap_last_step') if c in key.columns]
        if len(key) and 'max_lookahead_used' in key.columns:
            fcd = key[fc].copy()
            used = fcd.loc[fcd['status'] == 'optimal', 'max_lookahead_used'].dropna().unique()   # infeasible runs do not count
            fcd['same_lookahead_in_all_runs'] = "YES" if len(used) <= 1 else "NO - re-run the cases with a smaller look-ahead using the largest value"
            fcd.to_excel(xw, sheet_name="Formulation_Check", index=False)

        # ---------- Pareto data sheets (Fig. 8 = air-cooled, Fig. 9 = water-cooled) ----------
        summ_rows = []
        for cool, d in pareto.items():
            fig = "F8_Air" if cool == 'air' else "F9_Water"
            facs = [f for f in sorted(d, reverse=True) if d[f].get('water_ML') is not None]
            if not facs or 1.0 not in d or d[1.0].get('water_ML') is None:
                continue
            base_cost = d[1.0]['key'].loc[0, 'total_cost_GBPbn']
            cost = pd.DataFrame([dict(water_availability_pct=100 * f, total_cost_GBPbn=d[f]['key'].loc[0, 'total_cost_GBPbn'],
                                      cost_increase_pct=100 * (d[f]['key'].loc[0, 'total_cost_GBPbn'] / base_cost - 1),
                                      mip_gap_last_step=d[f]['key'].loc[0, 'mip_gap_last_step'],
                                      total_water_1e9L=d[f]['key'].loc[0, 'total_water_1e9L'],
                                      direct_DC_water_1e9L=d[f]['key'].loc[0, 'direct_DC_water_1e9L']) for f in facs])
            cost.to_excel(xw, sheet_name=fig + "_Cost", index=False)
            # electricity and hydrogen mix by technology (TWh) x availability level
            for sector, nm in (('Electricity', 'ElecMix'), ('Hydrogen', 'H2Mix')):
                tab = {}
                for f in facs:
                    g = d[f]['generation']
                    g = g[g['sector'] == sector].set_index('technology')['TWh']
                    tab["%d%%" % round(100 * f)] = g
                pd.DataFrame(tab).to_excel(xw, sheet_name=fig + "_" + nm)
            # regional heat shares and water by availability level
            for col, nm in (('heat_electrification_share', 'ElecLevel'), ('heat_hydrogen_share', 'H2Level'),
                            ('total_water_1e9L', 'RegionalWater')):
                tab = {}
                for f in facs:
                    r = d[f]['regional'].set_index('region')[col]
                    tab["%d%%" % round(100 * f)] = r
                pd.DataFrame(tab).to_excel(xw, sheet_name=fig + "_" + nm)
            # summary vs reviewer questions
            lo = facs[-1]
            k0, k1 = d[1.0]['key'].loc[0], d[lo]['key'].loc[0]
            c0, c1 = d[1.0]['cost'].set_index('component')['discounted_total_GBPbn'], d[lo]['cost'].set_index('component')['discounted_total_GBPbn']
            items = [("Total cost (GBP bn)", k0['total_cost_GBPbn'], k1['total_cost_GBPbn']),
                     ("CAPEX, discounted (GBP bn)", k0['capex_discounted_GBPbn'], k1['capex_discounted_GBPbn']),
                     ("OPEX, discounted (GBP bn)", k0['opex_discounted_GBPbn'], k1['opex_discounted_GBPbn']),
                     ("Curtailment penalty (GBP bn)", k0['curtailment_penalty_discounted_GBPbn'], k1['curtailment_penalty_discounted_GBPbn']),
                     ("Load-shedding penalty (GBP bn)", k0['load_shedding_penalty_discounted_GBPbn'], k1['load_shedding_penalty_discounted_GBPbn']),
                     ("Carbon cost (GBP bn)", k0['carbon_cost_discounted_GBPbn'], k1['carbon_cost_discounted_GBPbn']),
                     ("Import cost (GBP bn)", k0['import_cost_discounted_GBPbn'], k1['import_cost_discounted_GBPbn']),
                     ("Renewable curtailment (TWh/yr, 2050)", k0['renewable_curtailment_TWh'], k1['renewable_curtailment_TWh']),
                     ("Load shedding (GWh/yr, 2050)", k0['load_shedding_GWh'], k1['load_shedding_GWh']),
                     ("Electricity imports (TWh/yr, 2050)", k0['electricity_imports_TWh'], k1['electricity_imports_TWh']),
                     ("Offshore wind (GW, 2050)", k0['offshore_wind_GW'], k1['offshore_wind_GW']),
                     ("Solar (GW, 2050)", k0['solar_GW'], k1['solar_GW']),
                     ("Battery (GW, 2050)", k0['battery_GW'], k1['battery_GW']),
                     ("Nuclear (GW, 2050)", k0['nuclear_GW'], k1['nuclear_GW']),
                     ("Heat electrification share (2050)", k0['heat_electrification_share'], k1['heat_electrification_share']),
                     ("Indirect water (1e9 L, 2050)", k0['indirect_water_1e9L'], k1['indirect_water_1e9L']),
                     ("Direct DC water (1e9 L, 2050)", k0['direct_DC_water_1e9L'], k1['direct_DC_water_1e9L']),
                     ("Total water (1e9 L, 2050)", k0['total_water_1e9L'], k1['total_water_1e9L'])]
            for nme, a0, a1 in items:
                summ_rows.append(dict(cooling=COOLING_LABEL[cool], metric=nme, at_100pct=a0,
                                      at_lowest_feasible_pct=100 * lo, value_at_lowest_feasible=a1,
                                      change=a1 - a0, change_pct=(100 * (a1 / a0 - 1)) if a0 not in (0, 0.0) else float('nan')))
        if summ_rows:
            pd.DataFrame(summ_rows).to_excel(xw, sheet_name="Summary_For_Reviewer", index=False)

        for field, nm in (('cost', 'Cost_Breakdown'), ('annual', 'Annual_Flows'), ('generation', 'Generation_2050'),
                          ('capacity', 'Capacity_2050'), ('water_tech', 'Water_by_Tech_2050'),
                          ('regional', 'Regional_2050'), ('audit', 'Water_Audit'),
                          ('steps', 'Solve_Log'), ('limits', 'Water_Limits')):
            df = _stack(allres, field)
            if not df.empty:
                df.to_excel(xw, sheet_name=nm, index=False)

        # ---------- sensitivity ----------
        if sens:
            rows = []
            for (case, cool), r in sens.items():
                if r.get('water_ML') is None:
                    rows.append(dict(case=case, cooling=COOLING_LABEL.get(cool, cool), status=r.get('status')))
                    continue
                k = r['key'].loc[0]
                rows.append(dict(case=case, cooling=COOLING_LABEL.get(cool, cool), status=r['status'],
                                 total_cost_GBPbn=k['total_cost_GBPbn'],
                                 electricity_generation_TWh=k['electricity_generation_TWh'],
                                 heat_from_electricity_TWh=k['heat_from_electricity_TWh'],
                                 heat_from_hydrogen_TWh=k['heat_from_hydrogen_TWh'],
                                 heat_from_gas_TWh=k['heat_from_gas_TWh'],
                                 heat_electrification_share=k['heat_electrification_share'],
                                 ASHP_heat_capacity_GW=k['ASHP_heat_capacity_GW'],
                                 HyBoiler_heat_capacity_GW=k['HyBoiler_heat_capacity_GW'],
                                 offshore_wind_GW=k['offshore_wind_GW'], solar_GW=k['solar_GW'],
                                 onshore_wind_GW=k['onshore_wind_GW'], battery_GW=k['battery_GW'],
                                 DC_demand_TWh=k['DC_electricity_demand_TWh'],
                                 mip_gap_last_step=k['mip_gap_last_step']))
            sdf = pd.DataFrame(rows)
            sdf.to_excel(xw, sheet_name="Sensitivity_HP_H2", index=False)
            shift = []
            for case in SENS_CASES:
                a = sdf[(sdf['case'] == case) & (sdf['cooling'] == 'Without DC')]
                for cool in [c for c in SENS_COOLINGS if c != 'none']:
                    b = sdf[(sdf['case'] == case) & (sdf['cooling'] == COOLING_LABEL.get(cool, cool))]
                    if len(a) and len(b) and 'heat_from_electricity_TWh' in sdf.columns:
                        a0, b0 = a.iloc[0], b.iloc[0]
                        shift.append(dict(case=case, comparison="%s minus Without DC" % COOLING_LABEL.get(cool, cool),
                                          d_heat_from_electricity_TWh=b0['heat_from_electricity_TWh'] - a0['heat_from_electricity_TWh'],
                                          d_heat_from_hydrogen_TWh=b0['heat_from_hydrogen_TWh'] - a0['heat_from_hydrogen_TWh'],
                                          d_electrification_share_pp=100 * (b0['heat_electrification_share'] - a0['heat_electrification_share']),
                                          d_ASHP_GW=b0['ASHP_heat_capacity_GW'] - a0['ASHP_heat_capacity_GW'],
                                          d_HyBoiler_GW=b0['HyBoiler_heat_capacity_GW'] - a0['HyBoiler_heat_capacity_GW'],
                                          d_electricity_generation_TWh=b0['electricity_generation_TWh'] - a0['electricity_generation_TWh'],
                                          d_cost_GBPbn=b0['total_cost_GBPbn'] - a0['total_cost_GBPbn']))
            if shift:
                pd.DataFrame(shift).to_excel(xw, sheet_name="Sensitivity_Shift", index=False)
        if base:
            _write_table2_style(xw, base)
        if mono:
            _write_mono(xw, base or {}, mono)
    print("Saved:", path)


# =========================================================
# 4b. FEASIBILITY-RELAXATION DIAGNOSIS OF THE LAST (INFEASIBLE) STEP
# =========================================================
def diagnose_last_step(cooling="air"):
    """Loads the checkpoint of step HL_MAX-1, builds the last step, relaxes integrality and calls Gurobi feasRelaxS
    (minimum total violation of constraints and bounds). Writes feasrelax_<tag>.csv with every violated constraint."""
    import re
    tag = "Pareto_%s_f100" % cooling if cooling in ("air", "water") else "Base_%s" % cooling
    fix_step = HL_MAX - 1 if DIAGNOSE_FIX_STEP is None else DIAGNOSE_FIX_STEP
    if fix_step >= HL_INIT:
        p = _ckpt_path(tag, fix_step)
        if not os.path.exists(p):
            print("No checkpoint %s - set DIAGNOSE_FIX_STEP = 0 to test the whole horizon without any checkpoint." % p)
            return
        with open(p, "rb") as f:
            fixed_values = pickle.load(f)
        print("Diagnosis: periods up to t = %d fixed from the checkpoint, periods %d..%d free (LP relaxation)." % (fix_step, fix_step + 1, HL_MAX))
    else:
        fixed_values = {}
        print("Diagnosis: nothing fixed - the whole horizon 2..%d is checked as one LP relaxation." % HL_MAX)
    model = build_model(HL_MAX, dict(cooling=cooling))
    vars_map = get_vars_map(model)
    for (var_name, idx), val in fixed_values.items():
        if var_name in vars_map and val is not None:
            var_obj = vars_map[var_name]
            if idx in var_obj:
                try:
                    var_obj[idx].fix(val)
                except Exception:
                    pass
    opt = SolverFactory('gurobi_persistent')
    opt.set_instance(model, symbolic_solver_labels=True)
    gm = opt._solver_model
    gm.setParam('Threads', THREADS)
    gm.setParam('LogFile', os.path.join(OUT_DIR, "feasrelax_%s.log" % tag))
    rel = gm.relax()                                   # LP relaxation (integer variables -> continuous)
    rel.feasRelaxS(0, True, True, True)                # relaxobjtype 0 = sum of violations; relax variable bounds and constraints
    rel.optimize()
    print("Relaxation status code:", rel.Status)
    rows = []
    for v in rel.getVars():
        if v.VarName.startswith("Art") and v.X > 1e-6:
            raw = v.VarName
            rest = re.sub(r"^Art[PNLU]_", "", raw)
            m = re.match(r"c_[a-z]_(.*?)\(", rest)
            fam = m.group(1) if m else rest.split("(")[0]
            rows.append(dict(slack_variable=raw, constraint_or_bound=rest, family=fam, violation=v.X))
    df = pd.DataFrame(rows)
    out = os.path.join(OUT_DIR, "feasrelax_%s.csv" % tag)
    if len(df):
        df.sort_values("violation", ascending=False).to_csv(out, index=False)
        print("\nViolated constraint families (sum of violations):")
        print(df.groupby("family")["violation"].agg(["count", "sum", "max"]).sort_values("sum", ascending=False).head(30))
        print("\nSaved:", out)
    else:
        print("No violation found - the relaxed model is feasible without slack (check status code).")


# =========================================================
# 5.  MAIN
# =========================================================
def main():
    if DIAGNOSE_FEASRELAX:
        diagnose_last_step(DIAGNOSE_COOLING)
        return
    if EXCEL_ONLY:
        rebuild_master_excel(also_cases=True)
        return
    # every finished run is saved at once: cache + one Excel file per case + the master workbook is rebuilt
    if RUN_BASELINES:
        baseline_runs()
    if RUN_PARETO:
        for cool in PARETO_COOLINGS:
            pareto_for(cool)
    if RUN_SENSITIVITY:
        sensitivity_runs()
    if RUN_MONOLITHIC:
        monolithic_runs()
    rebuild_master_excel()
    print("\nALL DONE. Master workbook:", os.path.join(OUT_DIR, MASTER_XLSX_NAME))


if __name__ == "__main__":
    main()
