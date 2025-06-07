import pandas as pd
import numpy as np
import os
import matplotlib.pyplot as plt


import statsmodels.api as sm
from functools import reduce

import geopandas as gpd
import matplotlib.patches as mpatches

import zipfile
import statsmodels.api as sm
import shapely
from shapely import Point, LineString, Polygon

# A. assembling the data
# importing the data
sfa1011 = pd.read_csv("/Users/Swaggy-LYX/Downloads/data task_Yuxi Liang/sfa1011.csv")
sfa1112 = pd.read_csv("/Users/Swaggy-LYX/Downloads/data task_Yuxi Liang/sfa2223.csv")
sfa1213 = pd.read_csv("/Users/Swaggy-LYX/Downloads/data task_Yuxi Liang/sfa2223.csv")
sfa1314 = pd.read_csv("/Users/Swaggy-LYX/Downloads/data task_Yuxi Liang/sfa2223.csv")
sfa1415 = pd.read_csv("/Users/Swaggy-LYX/Downloads/data task_Yuxi Liang/sfa2223.csv")
sfa1516 = pd.read_csv("/Users/Swaggy-LYX/Downloads/data task_Yuxi Liang/sfa2223.csv")
hd2023 = pd.read_csv("/Users/Swaggy-LYX/Downloads/data task_Yuxi Liang/hd2023.csv", encoding="latin1")



years = range(2010, 2016)
path = "/Users/Swaggy-LYX/Downloads/data task_Yuxi Liang"
exclude_states = ['DC', 'FM', 'MH', 'MP', 'PR', 'PW', 'VI', 'GU', 'AS']

dfs = []

for year in years:
    sfa_suffix = str(year)[-2:] + str(year + 1)[-2:]  # e.g., 10 + 11 = 1011
    sfa_file = f"{path}/sfarv_{sfa_suffix}.csv"
    hd_file = f"{path}/hd{year + 1}.csv"  # use fall term year for hd (e.g., 2010–11 -> hd2011.csv)

    try:
        sfa = pd.read_csv(sfa_file, encoding='latin1', low_memory=False)
        hd = pd.read_csv(hd_file, encoding='latin1', low_memory=False)
    except FileNotFoundError as e:
        print(f"Missing file for year {year}: {e}")
        continue

    sfa_sub = sfa[['UNITID', 'SCUGFFN','AIDFSIN']].copy()
    hd_sub = hd[['UNITID', 'DEGGRANT', 'OPENPUBL', 'STABBR']].copy()

    df = pd.merge(hd_sub, sfa_sub, on='UNITID', how='inner')
    df = df[~df['STABBR'].isin(exclude_states)]
    df = df[df['DEGGRANT'].isin([1, 2, 3])]

    df['year'] = year
    df['ID_IPEDS'] = df['UNITID']
    df['degree_bach'] = (df['DEGGRANT'] == 3).astype(int)
    df['public'] = (df['OPENPUBL'] == 1).astype(int)
    df['enroll_ftug'] = df['SCUGFFN']
    df['grant_federal'] = df['AIDFSIN']

    df = df[['ID_IPEDS', 'STABBR', 'year', 'degree_bach', 'public', 'enroll_ftug', 'grant_federal']]
    dfs.append(df)

# Combine years and filter to balanced panel
panel = pd.concat(dfs)
keep_ids = panel['ID_IPEDS'].value_counts()[lambda x: x == 6].index
panel_balanced = panel[panel['ID_IPEDS'].isin(keep_ids)].reset_index(drop=True)

# Save
panel_balanced.to_csv("/Users/Swaggy-LYX/Downloads/clean_ipeds_panel.csv", index=False)


# B

# Filter the panel
df_filtered = panel_balanced[(panel_balanced['public'] == 1) & (panel_balanced['degree_bach'] == 0)]

# Group by year and sum enrollments
enroll_by_year = df_filtered.groupby('year')['enroll_ftug'].sum().reset_index()

# Plot
plt.figure(figsize=(8, 5))
plt.plot(enroll_by_year['year'], enroll_by_year['enroll_ftug'], marker='o', linestyle='-')
plt.title('Total First-Time, Full-Time Enrollment at Public Two-Year Colleges\n(2010–11 to 2015–16)')
plt.xlabel('Academic Year')
plt.ylabel('Enrollment')
plt.grid(True)
plt.tight_layout()
plt.show()

# C

# filtering 
df_2015 = panel_balanced[panel_balanced['year'] == 2015].copy()

# 1
# Compute per-student aid at the institution level
df_2015['aid_per_student'] = df_2015['grant_federal'] / df_2015['enroll_ftug']

# Compute state averages
state_avg = df_2015.groupby('STABBR')['aid_per_student'].mean().reset_index()
vt_ny = state_avg[state_avg['STABBR'].isin(['VT', 'NY'])]
print(vt_ny)

# 2

summary_stats = state_avg['aid_per_student'].describe()
print(summary_stats)

# 3
df_2015['grant_federal_new'] = 1750 * df_2015['enroll_ftug'] + 0.15 * (df_2015['enroll_ftug'] ** 2)
df_2015['aid_per_student_new'] = df_2015['grant_federal_new'] / df_2015['enroll_ftug']

# Recompute state averages under the new system
state_avg_new = df_2015.groupby('STABBR')['aid_per_student_new'].mean().reset_index()

# Compare spread before and after
spread_before = state_avg['aid_per_student'].std()
spread_after = state_avg_new['aid_per_student_new'].std()

print(f"Standard deviation before: {spread_before:.2f}")
print(f"Standard deviation after: {spread_after:.2f}")

