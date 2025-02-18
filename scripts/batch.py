import os
import csv
import glob
import numpy as np
import pandas as pd

level0 = "data/Level0/v3"
file_list = glob.glob("/home/runnalja/Desktop/Temperature_v3/*.dat")
file_list.sort()
df = pd.concat([pd.read_csv(file, header=None) for file in file_list], ignore_index=True)
df["time"] = pd.to_datetime(df[0])
df = df.sort_values(by=["time"]).reset_index(drop=True)
df['date'] = df["time"].dt.date
os.makedirs(level0, exist_ok=True)

def custom_quote(x):
    if isinstance(x, str):
        return f'"{x}"'
    return x

for date, group in df.groupby('date'):
    filename = os.path.join(level0, f"LeXPLORE_EAST_TempChain_{date}.dat")
    group.drop(columns=['date', "time"], inplace=True)  # Remove extra date column
    group = group.applymap(custom_quote)
    print(group)
    group.to_csv(filename, index=False, header=False, sep=",", quoting=3)
