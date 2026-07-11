#%%
import pandas as pd
import numpy as np
from numpy import unravel_index
from sklearn.cluster import KMeans
from collections import Counter, defaultdict
from scipy.stats import gaussian_kde
from scipy.interpolate import interp1d
import tkinter as tk
from tkinter import simpledialog, messagebox
import subprocess
import concurrent.futures
from tkinter import simpledialog
import threading
from tkinter import filedialog
import os
file_path = os.path.join(os.path.dirname(__file__), "Whole UK 5 year.xlsx")

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
#Reservoir_data = excel_data.parse('Emissions')
Pipelines_data= excel_data.parse('Pipelines')

df_eta=excel_data.parse('TechData', header=None, usecols="A:G", skiprows=101, nrows=24)
df_BR=excel_data.parse('TechData', header=None, usecols="A:G", skiprows=153, nrows=29)
df_cc_Heat=excel_data.parse('HeatTech', header=None, usecols="A:G", skiprows=2, nrows=5)
df_eta_Heat=excel_data.parse('HeatTech', header=None, usecols="A:G", skiprows=11, nrows=5)
df_cc_fix=excel_data.parse('CostTech', header=None, usecols="A:G", skiprows=2, nrows=24)
df_oc_fix=excel_data.parse('CostTech', header=None, usecols="L:R", skiprows=2, nrows=24)
df_LandAvailability=excel_data.parse('LandAvailability', header=None, usecols="A:N", skiprows=2, nrows=3)
df_NUint=excel_data.parse('InitCap', header=None, usecols="A:N", skiprows=2, nrows=4)
df_Capinit=excel_data.parse('InitCap', header=None, usecols="A:N", skiprows=10, nrows=7)
df_NUf=excel_data.parse('InitCap', header=None, usecols="A:O", skiprows=21, nrows=2)
df_Capf=excel_data.parse('InitCap', header=None, usecols="A:O", skiprows=27, nrows=2)
df_ICap=excel_data.parse('Trans_Inter', header=None, usecols="A:H", skiprows=6, nrows=12)
df_pim_y=excel_data.parse('Trans_Inter', header=None, usecols="A:G", skiprows=57, nrows=6)
df_ipe=excel_data.parse('ClusteredDataSTOR', header=None, usecols="A:H", skiprows=2, nrows=144)
df_ElecDem=excel_data.parse('ClusteredDataSTOR', header=None, usecols="I:K", skiprows=2, nrows=144)
df_Ind=excel_data.parse('ClusteredDataSTOR', header=None, usecols="AP:BD", skiprows=2, nrows=144)
df_Com=excel_data.parse('ClusteredDataSTOR', header=None, usecols="AA:AO", skiprows=2, nrows=144)
df_Dom=excel_data.parse('ClusteredDataSTOR', header=None, usecols="L:Z", skiprows=2, nrows=144)
df_AV=excel_data.parse('ClusteredDataSTOR', header=None, usecols="BE:CS", skiprows=2, nrows=144)
df_temp=excel_data.parse('ClusteredDataSTOR', header=None, usecols="CT:DH", skiprows=2, nrows=144)
df_fuel=excel_data.parse('Fuels', header=None, usecols="A:G", skiprows=3, nrows=5)

df_DistRes = excel_data.parse('Distances', header=None, usecols="B:D", skiprows=23, nrows=3)
df_DistSt = excel_data.parse('Distances', header=None, usecols="B:D", skiprows=31, nrows=4)
df_Dist = excel_data.parse('Distances', header=None, usecols="B:N", skiprows=4, nrows=13)
df_DistPipe = excel_data.parse('Distances', header=None, usecols="R:AD", skiprows=4, nrows=13)
df_ExT = excel_data.parse('Trans_Inter', header=None, usecols="B:N", skiprows=80, nrows=13)
df_DCProfile=excel_data.parse('DC', header=None, usecols="A:C", skiprows=2, nrows=144)
df_DCCap=excel_data.parse('DC', header=None, usecols="F:S", skiprows=7, nrows=5)
year_data2 = excel_data.parse('DC')
Water_data1 = excel_data.parse('Water')








file_path3 = os.path.join(os.path.dirname(__file__), "Cooling.xlsx")
excel_data3 = pd.ExcelFile(file_path3, engine='openpyxl')

df_AirCooled=excel_data3.parse('Air_Cooled', header=None, usecols="A:AB", skiprows=2, nrows=144)
df_WaterCooled=excel_data3.parse('Water-Cooled', header=None, usecols="A:AB", skiprows=2, nrows=144)
df_Liquid=excel_data3.parse('Liquid_Cooling', header=None, usecols="A:AB", skiprows=2, nrows=144)

#%%

from pyomo.environ import *
from pyomo.environ import SolverFactory
def build_model(hl_max):
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
            )#+0.001*sum(
                #model.DACCC[t]*model.CAPDACnew[g,t] for g in model.g) #This term should be added for DAC scenario
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
                #+
                #sum(
                    #model.WF[c] * 0.00025 * model.DACCC[t]*model.CAPDAC[g,t]
                    #for g in model.g
                    #for c in model.c
                    
                    #)  #This term should be added under DAC sceanrio
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
        
          return model.TOC[t]==model.POC[t]+model.FOC[t]+model.CEC[t]+model.IIC[t]+model.HGDC[t]+model.HGOC[t]
        
    model.TOCConstraint=Constraint(model.ttt,rule=TOC_rule)


    def TC_rule(model):
        return sum(model.dfc[t]*model.TCC[t] +  model.dfo[t]*model.TOC[t] for t in model.ttt)+ 0.1 * sum(
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

    def DC_Profile_rule(model,g,t,c,h):
        #if t in model.TT and c in model.c and h in model.h:
            return model.TDemandDC[g,t,c,h]==model.CapDC[t, g]*model.DCProfile0[c,h]*model.PUE_air[c,h,g]
        #return Constraint.Skip
    model.DCProfileCON=Constraint(model.g,model.ttt, model.c,model.h, rule=DC_Profile_rule)
    
    
    
    def DC_Water_rule(model,g,t,c,h):
        #if t in model.TT and c in model.c and h in model.h:
            return model.Water_DC[g,t,c,h]==model.CapDC[t, g]*model.DCProfile0[c,h]*model.WUE_air[c,h,g]
        #return Constraint.Skip
    model.DCWaterCON=Constraint(model.g,model.ttt, model.c,model.h, rule=DC_Water_rule)
        

    
     
    def MaxDC_rule1(model,t):
          #if t in model.TT:
              return sum (model.CapDC[t,g] for g in model.g)>=sum(model.DCCap_max[t,g] for g in model.g)
          #return Constraint.Skip
    model.MaxCapDCCON1=Constraint(model.ttt,rule=MaxDC_rule1)
     


           

    #%%DAC   This section should be actived when the DAC scneario is run
    '''
    def heat_refuce_rule(model,g,t,c,h):
        return model.TDemandDC[g,t,c,h]*0.6>=model.H_DAC[g,t,c,h]
    model.HeatRefuceCon=Constraint(model.g,model.ttt, model.c,model.h, rule=heat_refuce_rule)



    def heatDemand_DAC_rule(model,g,t,c,h):
        return model.H_DAC[g,t,c,h]==model.hc_dac[t]*model.DAC[g,t,c,h]
    model.HeatDACCon=Constraint(model.g,model.ttt, model.c,model.h, rule=heatDemand_DAC_rule)

    def ElecDemand_DAC_rule(model,g,t,c,h):
        return model.E_DAC[g,t,c,h]==model.ec_dac[t]*model.DAC[g,t,c,h]
    model.ElecDACCon=Constraint(model.g,model.ttt, model.c,model.h, rule=ElecDemand_DAC_rule)


    def DACMax_rule(model,g,t):
        return sum (model.WF[c]*model.DAC[g,t,c,h] for c in model.c for h in model.h)<=model.CAPDAC[g,t]
    model.DACMAXCon=Constraint(model.g,model.ttt, rule=DACMax_rule)


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
     
    model.CAPDACCON = Constraint(model.g, model.ttt, rule=CAPDAC_rule)
   '''



    #%% The term E_DAC shoudl be considered when DAC scenario is run
    def total_elec_demand_rule(model, g, t, c, h):
        #if t in model.TT and c in model.c and h in model.h:
            return model.totdem_elec[g,t,c,h] == (
                model.TPowerDem[g,t,c,h]+model.TDemandDC[g,t,c,h]+#model.E_DAC[g,t,c,h]+
                + sum(model.P[j,g,t,c,h]/model.eta[j,t] for j in model.j if ('Elec', j) in model.jf)
                + model.hedem_elec[g,t,c,h]/model.COP[g,c,h]
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
                sum(model.yc[jccs] * model.P[jccs, g, t, c, h] for jccs in model.jccs)#+model.DAC[g,t,c,h]  This term should be considered when DAC scenario is run
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
                        >= (1+model.CM)*model.PeakDemand[t]                  
        #return Constraint.Skip
    model.ReserveCon= Constraint(model.ttt, rule=Reserve_ruel)



    #%%
   

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

     #When DAC is run the last term should be activated
    def TotEmissions_rule(model, t):
        #if t in model.TT:
            return model.Etotal[t] == model.Ee[t] + model.Eh[t] + model.Eg[t]#-sum(model.WF[c]*model.DAC[g,t,c,h] for g in model.g for c in model.c for h in model.h)
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
# SETTINGS
# =========================================================
hl_init = 2
hl_max  = 6 # If you want to ger result for 2040 or 2045, you can change this value : 2:2030, 3:2035, 4: 2040, 5: 2045, 6: 2050
step    = 1

fixed_values = {}

hl = hl_init


# =========================================================
# ROLLING HORIZON LOOP
# =========================================================
while hl <= hl_max:

    print(f"\n===================================")
    print(f"Rolling Horizon Solve | hl = {hl}")
    print(f"===================================\n")

    # =====================================================
    # BUILD MODEL
    # =====================================================
    model = build_model(hl)

    vars_map = get_vars_map(model)

    # =====================================================
    # APPLY FIXED VALUES
    # =====================================================
    for (var_name, idx), val in fixed_values.items():

        if var_name in vars_map:

            var_obj = vars_map[var_name]

            if idx in var_obj:

                if val is not None:

                    try:
                        var_obj[idx].fix(val)

                    except:
                        pass

    # =====================================================
    # SOLVER
    # =====================================================
    opt = SolverFactory('gurobi')

    opt.options['Threads'] = 30
    opt.options['Presolve'] = 2
    opt.options['MIPGap'] = 0.05
    opt.options['LogFile'] = "opt.log"
    opt.options['BarHomogeneous'] = 1
    opt.options['NumericFocus'] = 1
    opt.options['IntegralityFocus'] = 1

    results = opt.solve(model, tee=True)

    print("Termination Condition:",
          results.solver.termination_condition)

    # =====================================================
    # SAVE SOLUTION
    # =====================================================
    if results.solver.termination_condition in [
        TerminationCondition.optimal,
        TerminationCondition.feasible
    ]:

        # ---------------------------------------------
        # LOOP OVER VARIABLES
        # ---------------------------------------------
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

                except:
                    continue

 
                if t <= hl:

                    # ---------------------------------
                    # SAFE VALUE
                    # ---------------------------------
                    val = safe_value(var_obj[idx])

                    # ignore undefined variables
                    if val is not None:

                        fixed_values[(var_name, idx)] = val

    # =====================================================
    # SAVE LAST MODEL
    # =====================================================
    last_model = model

    # =====================================================
    # NEXT HORIZON
    # =====================================================
    hl += step

# =========================================================
# FINAL MODEL
# =========================================================
model = last_model

from openpyxl import Workbook


wb = Workbook()

all_variables = []

objective_value = model.TC()  
all_variables.append({"Name": "Objective", "Index": "-", "Value": objective_value})

for var in model.component_objects(Var, active=True):
    var_name = var.name
    for index in var:
        value = var[index]()
        if value is not None and abs(value) > 1e-6:  
            all_variables.append({
                "Name": var_name,
                "Index": index,
                "Value": value
            })

df = pd.DataFrame(all_variables)
df.to_excel("Scenario1 Air_Cooled.xlsx", index=False, sheet_name="All Data")

#%%
import pandas as pd
from pyomo.environ import value

# ---------- PeakDemand (t) ----------
data_peak = []
for t in [2,3,4,5]:
    data_peak.append({
        't': t,
        'PeakDemand': value(model.PeakDemand[t])
    })
df_peak = pd.DataFrame(data_peak)

# ---------- CAP (j,c,t) ----------
data_cap = []
for j in model.jre or model.jhe or model.jes:
    for g in model.g:
        for t in [2,3,4,5]:
            data_cap.append({
                'j': j,
                'g': g,
                't': t,
                'CAP': value(model.CAP[j, g, t])
            })
df_cap = pd.DataFrame(data_cap)

# ---------- DCAP (j,c,t) ----------
data_dcap = []
for j in model.jre or model.jhe or model.jes:
    for g in model.g:
        for t in [2,3,4,5]:
            data_dcap.append({
                'j': j,
                'g': g,
                't': t,
                'DCAP': value(model.DCAP[j, g, t])
            })
df_dcap = pd.DataFrame(data_dcap)

# ---------- CAPnew (j,c,t) ----------
data_capnew = []
for j in model.jre or model.jes:
    for g in model.g:
        for t in [2,3,4,5]:
            data_capnew.append({
                'j': j,
                'g': g,
                't': t,
                'CAPnew': value(model.CAPnew[j, g, t])
            })
df_capnew = pd.DataFrame(data_capnew)


# ---------- CAPheatnew (j,c,t) ----------
data_capheatnew = []
for j in model.jhe:
    for g in model.g:
        for t in [2,3,4,5]:
            data_capheatnew.append({
                'j': j,
                'g': g,
                't': t,
                'CAPheat_new': value(model.CAPheat_new[j, g, t])
            })
df_capheatnew = pd.DataFrame(data_capheatnew)

# ---------- Save to Excel ----------
with pd.ExcelWriter('Result_AirCooled.xlsx', engine='openpyxl') as writer:
    df_peak.to_excel(writer, sheet_name='PeakDemand', index=False)
    df_cap.to_excel(writer, sheet_name='CAP', index=False)
    df_dcap.to_excel(writer, sheet_name='DCAP', index=False)
    df_capnew.to_excel(writer, sheet_name='CAPnew', index=False)
    df_capheatnew.to_excel(writer, sheet_name='CAPheatnew', index=False)

from pyomo.environ import value




data_NU = []
for j in model.jhp or model.jth:
    for g in model.g:
        for t in [2,3,4,5]:
            data_NU.append({
                'j': j,
                'g': g,
                't': t,
                'NU': value(model.NU[j, g, t])
            })
df_NU = pd.DataFrame(data_NU)

with pd.ExcelWriter('Result_AirCooled.xlsx', engine='openpyxl', mode='a') as writer:
    df_NU.to_excel(writer, sheet_name='Thermal Capacity', index=False)









# ---------- CH weighted by WF[k] ----------
data_ch = []

for j in model.jes:
    for g in model.g:
        for t in [2,3,4,5]:
            for c in model.c:
                for h in model.h:
                    data_ch.append({
                        'j': j,
                        'g': g,
                        't': t,
                        'c': c,
                        'h': h,
                        'Storage Charge': value(model.CH[j, g, t, c, h]) * value(model.WF[c])
                    })

df_ch = pd.DataFrame(data_ch)

# ---------- Save to Excel ----------
with pd.ExcelWriter('Result_AirCooled.xlsx', engine='openpyxl', mode='a') as writer:
    df_ch.to_excel(writer, sheet_name='Storage Charge', index=False)





data_dis = []

for j in model.jes:
    for g in model.g:
        for t in [2,3,4,5]:
            for c in model.c:
                for h in model.h:
                    data_dis.append({
                        'j': j,
                        'g': g,
                        't': t,
                        'c': c,
                        'h': h,
                        'Storage DisCharge': value(model.DC[j, g, t, c, h]) * value(model.WF[c])
                    })

df_dis = pd.DataFrame(data_dis)

# ---------- Save to Excel ----------
with pd.ExcelWriter('Result_AirCooled.xlsx', engine='openpyxl', mode='a') as writer:
    df_dis.to_excel(writer, sheet_name='Storage Discharge', index=False)
    


data_SOC = []   
for j in model.jes:
    for g in model.g:
        for t in [2,3,4,5]:
            for c in model.c:
                for h in model.h:
                    data_SOC.append({
                        'j': j,
                        'g': g,
                        't': t,
                        'c': c,
                        'h': h,
                        'Storage SOC': value(model.S[j, g, t, c, h]) * value(model.WF[c])
                    })

df_SOC = pd.DataFrame(data_SOC)

# ---------- Save to Excel ----------
with pd.ExcelWriter('Result_AirCooled.xlsx', engine='openpyxl', mode='a') as writer:
    df_SOC.to_excel(writer, sheet_name='Storage SOC', index=False)    
    
from pyomo.environ import value

# ---------- PG weighted by WF[k] ----------
data_pg = []

for j in model.j:
    if j not in model.jes and j not in model.jhs and j not in model.jhe:
        for g in model.g:
            for t in [2,3,4,5]:
                for c in model.c:
                    for h in model.h:
                        data_pg.append({
                            'j': j,
                            'g': g,
                            't': t,
                            'c': c,
                            'h': h,
                            'Generation': value(model.P[j, g, t, c, h]) * value(model.WF[c])
                        })
    

df_pg = pd.DataFrame(data_pg)

# ---------- Save to Excel ----------
with pd.ExcelWriter('Result_AirCooled.xlsx', engine='openpyxl', mode='a') as writer:
    df_pg.to_excel(writer, sheet_name='Generation', index=False)   

data_water = []
for j in model.j:
    if j  in ['FC', 'H2CCGT', 'Nuclear', 'OCGT', 'CCGTCCS', 'BECCS', 'Biomass', 'CCGT', 'SMRCCS', 'ATRCCS', 'BGCCS', 'WE']:
        for g in model.g:
            for t in [2,3,4,5]:
                for c in model.c:
                    for h in model.h:
                        data_water.append({
                            'j': j,
                            'g': g,
                            't': t,
                            'c': c,
                            'h': h,
                            'Water': value(model.Water[j, g, t, c, h]) * value(model.WF[c])
                        })
    

df_water = pd.DataFrame(data_water)

# ---------- Save to Excel ----------
with pd.ExcelWriter('Result_AirCooled.xlsx', engine='openpyxl', mode='a') as writer:
    df_water.to_excel(writer, sheet_name='Water Consumption', index=False)   




import pandas as pd
from pyomo.environ import value

# ---------- TDem parameter weighted by WF[k] ----------
data_TotalDem = []

for g in model.g:
    for t in [2,3,4,5]:
        for c in model.c:
            for h in model.h:
                data_TotalDem.append({
                    'g': g,
                    't': t,
                    'c': c,
                    'h': h,
                    'Base Demand1': value(model.totdem_elec[g, t, c, h]) * value(model.WF[c])
                })

df_TotalDem = pd.DataFrame(data_TotalDem)

# ---------- Save to Excel ----------
with pd.ExcelWriter('Result_AirCooled.xlsx', engine='openpyxl', mode='a') as writer:
    df_TotalDem.to_excel(writer, sheet_name='Total Elec Demand', index=False)



data_TotalAI = []

for g in model.g:
    for t in [2,3,4,5]:
        for c in model.c:
            for h in model.h:
                data_TotalAI.append({
                    'g': g,
                    't': t,
                    'c': c,
                    'h': h,
                    'AI Demand1': value(model.TDemandDC[g,t,c,h]) * value(model.WF[c])
                })

df_TotalAI = pd.DataFrame(data_TotalAI)

# ---------- Save to Excel ----------
with pd.ExcelWriter('Result_AirCooled.xlsx', engine='openpyxl', mode='a') as writer:
    df_TotalAI.to_excel(writer, sheet_name='Total Elec DC', index=False)


data_WaterAI = []

for g in model.g:
    for t in [2,3,4,5]:
        for c in model.c:
            for h in model.h:
                data_WaterAI.append({
                    'g': g,
                    't': t,
                    'c': c,
                    'h': h,
                    'AI Water': value(model.Water_DC[g,t,c,h]) * value(model.WF[c])
                })

df_WaterAI = pd.DataFrame(data_WaterAI)

# ---------- Save to Excel ----------
with pd.ExcelWriter('Result_AirCooled.xlsx', engine='openpyxl', mode='a') as writer:
    df_WaterAI.to_excel(writer, sheet_name='Total Water DC', index=False)


data_TotalH2Dem = []

for g in model.g:
    for t in [2,3,4,5]:
        for c in model.c:
            for h in model.h:
                data_TotalH2Dem.append({
                    'g': g,
                    't': t,
                    'c': c,
                    'h': h,
                    'Base Demand2': value(model.totdem_hydro[g, t, c, h]) * value(model.WF[c])
                })

df_TotalH2Dem = pd.DataFrame(data_TotalH2Dem)

# ---------- Save to Excel ----------
with pd.ExcelWriter('Result_AirCooled.xlsx', engine='openpyxl', mode='a') as writer:
    df_TotalH2Dem.to_excel(writer, sheet_name='Total H2 Demand', index=False)


data_TotalgasDem = []

for g in model.g:
    for t in [2,3,4,5]:
        for c in model.c:
            for h in model.h:
                data_TotalgasDem.append({
                    'g': g,
                    't': t,
                    'c': c,
                    'h': h,
                    'Base Demand3': value(model.hedem_elec[g, t, c, h]) * value(model.WF[c])
                })

df_TotalgasDem = pd.DataFrame(data_TotalgasDem)

# ---------- Save to Excel ----------
with pd.ExcelWriter('Result_AirCooled.xlsx', engine='openpyxl', mode='a') as writer:
    df_TotalgasDem.to_excel(writer, sheet_name='Heat Demand by Elec', index=False)



data_TotalgasDem_h2 = []

for g in model.g:
    for t in [2,3,4,5]:
        for c in model.c:
            for h in model.h:
                data_TotalgasDem_h2.append({
                    'g': g,
                    't': t,
                    'c': c,
                    'h': h,
                    'Base Demand5': value(model.hedem_hydro[g, t, c, h]) * value(model.WF[c])
                })

df_TotalgasDem_h2 = pd.DataFrame(data_TotalgasDem_h2)

# ---------- Save to Excel ----------
with pd.ExcelWriter('Result_AirCooled.xlsx', engine='openpyxl', mode='a') as writer:
    df_TotalgasDem_h2.to_excel(writer, sheet_name='Heat Demand by H2', index=False)


data_TotalgasDem_gas = []

for g in model.g:
    for t in [2,3,4,5]:
        for c in model.c:
            for h in model.h:
                data_TotalgasDem_gas.append({
                    'g': g,
                    't': t,
                    'c': c,
                    'h': h,
                    'Base Demand4': value(model.hedem_gas[g, t, c, h]) * value(model.WF[c])
                })

df_TotalgasDem_gas = pd.DataFrame(data_TotalgasDem_gas)

# ---------- Save to Excel ----------
with pd.ExcelWriter('Result_AirCooled.xlsx', engine='openpyxl', mode='a') as writer:
    df_TotalgasDem.to_excel(writer, sheet_name='Heat Demand by Gas', index=False)


data_curt = []
    
for g in model.g:
    for t in [2,3,4,5]:
        for c in model.c:
            for h in model.h:
                data_curt.append({
                    'g': g,
                    't': t,
                    'c': c,
                    'h': h,
                    'Curtailment': value(model.LC[g, t, c, h]) * value(model.WF[c])
                })

df_curt = pd.DataFrame(data_curt)

# ---------- Save to Excel ----------
with pd.ExcelWriter('Result_AirCooled.xlsx', engine='openpyxl', mode='a') as writer:
    df_curt.to_excel(writer, sheet_name='Curtailment', index=False) 

data_shed = []
    
for g in model.g:
    for t in [2,3,4,5]:
        for c in model.c:
            for h in model.h:
                data_shed.append({
                    'g': g,
                    't': t,
                    'c': c,
                    'h': h,
                    'Shed': value(model.LS[g, t, c, h]) * value(model.WF[c])
                })

df_shed = pd.DataFrame(data_shed)

# ---------- Save to Excel ----------
with pd.ExcelWriter('Result_AirCooled.xlsx', engine='openpyxl', mode='a') as writer:
    df_shed.to_excel(writer, sheet_name='Shed', index=False) 
    
    
    
data_Carbon = []

for g in model.g:
    for t in [2,3,4,5]:

        total_generation = sum(
            value(model.P[j, g, t, c, h]) * value(model.WF[c])
            for j in model.jth or model.jre
            for c in model.c
            for h in model.h
        )

        carbon_intensity = (
            value(model.Ee1[t, g]) / total_generation
            if total_generation > 0 else 0
        )

        data_Carbon.append({
            'g': g,
            't': t,
            'Carbon': carbon_intensity
        })


df_Carbon = pd.DataFrame(data_Carbon)

# ---------- Save to Excel ----------
with pd.ExcelWriter('Result_AirCooled.xlsx', engine='openpyxl', mode='a') as writer:
    df_Carbon.to_excel(writer, sheet_name='Carbon', index=False)  
    
    
data_DAC_Elec = []

for g in model.g:
    for t in [2,3,4,5]:
        for c in model.c:
            for h in model.h:
                data_DAC_Elec.append({
                    'g': g,
                    't': t,
                    'c': c,
                    'h': h,
                    'DAC Elec': value(model.E_DAC[g,t,c,h]) * value(model.WF[c])
                })

df_DAC_Elec = pd.DataFrame(data_DAC_Elec)

# ---------- Save to Excel ----------
with pd.ExcelWriter('Result_AirCooled.xlsx', engine='openpyxl', mode='a') as writer:
    df_DAC_Elec.to_excel(writer, sheet_name='Total Elec DAC', index=False)    
   

data_DAC_Heat = []

for g in model.g:
    for t in [2,3,4,5]:
        for c in model.c:
            for h in model.h:
                data_DAC_Heat.append({
                    'g': g,
                    't': t,
                    'c': c,
                    'h': h,
                    'DAC Elec': value(model.H_DAC[g,t,c,h]) * value(model.WF[c])
                })

df_DAC_Heat = pd.DataFrame(data_DAC_Heat)

# ---------- Save to Excel ----------
with pd.ExcelWriter('Result_AirCooled.xlsx', engine='openpyxl', mode='a') as writer:
    df_DAC_Heat.to_excel(writer, sheet_name='Total Heat DAC', index=False) 



data_DAC_Capture = []

for g in model.g:
    for t in [2,3,4,5]:
        for c in model.c:
            for h in model.h:
                data_DAC_Capture.append({
                    'g': g,
                    't': t,
                    'c': c,
                    'h': h,
                    'DAC Elec': value(model.DAC[g,t,c,h]) * value(model.WF[c])
                })

df_DAC_Capture = pd.DataFrame(data_DAC_Capture)

# ---------- Save to Excel ----------
with pd.ExcelWriter('Result_AirCooled.xlsx', engine='openpyxl', mode='a') as writer:
    df_DAC_Capture.to_excel(writer, sheet_name='Total DAC Capture', index=False) 