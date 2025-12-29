#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Dec 21 18:10:04 2025

@author: oliverlindblom
blankningsregistret - historiska positioner

detta inkluderar bara big money, ungefär hälften av den totala blankningspositionen försvinner i och med massa
mindre transaktioner. Placera publicerar topp tio blankade varje fredag dockj blir det också vrickat eftersom
att topp tio ändras hela tiden. Det kan dock användas som en indikator på bolagen som är mest blankade
"""
import pandas as pd
# pip install odf

file_path = "HistoriskaPositioner.ods" 

df = pd.read_excel(file_path, engine="odf") 

#%%
df.drop(columns=["Unnamed: 5"], inplace=True)

#%%
df = df.drop(4)

df = df.dropna()
#%%
df.columns = ["Innehavare", "Emittent", "ISIN", "Summa blankning", "Datum"]
#%%
df.set_index('Datum', inplace=True)

#%%
df.index = pd.to_datetime(df.index)

#%% bara test
df["Innehavare"].nunique()
df["Emittent"].nunique()
df["ISIN"].nunique()

#%%

em = df["Emittent"].astype("string")

df["Emittent"] = (
    em.str.replace("\u00a0", " ", regex=False) 
    .str.normalize("NFKC")
    .str.strip()
    .str.lower()
    .str.replace(r"\s*\(pu?bl\)", "", regex=True)
    .str.replace(r"^(ab|aktiebolag|aktiebolaget|akteebolag|akteebolaget)\s+", "", regex=True)
    .str.replace(r"\s+(ab|aktiebolag|aktiebolaget|akteebolag|akteebolaget)$", "", regex=True)
    .str.replace(r"\b(pharma|professional|gaming group|services sweden|of sweden|justitia|international|abp|plc)\b","",regex=True)

    .str.replace(r"\s+", " ", regex=True)
    .str.strip()
    )


#%%

df["Innehavare"] = (
    df["Innehavare"]
    .astype("string")
    .str.replace(r"\s*\(pu?bl\)", "", regex=True)
    .str.strip()
)

df["Innehavare"] = (
    df["Innehavare"]
    .astype("string")
    .str.replace("\u00a0", " ", regex=False)
    .str.strip()
    .str.lower()
)


df["Summa blankning"] = df["Summa blankning"].replace("<0,5", 0.25)

df["Summa blankning"] = (
    df["Summa blankning"]
    .astype("string")
    .str.replace(",", ".", regex=False)
    .astype(float)
)

#%%
# gör analysen på tre olika set: "<0.5" = [0, 0.25, 0.5]

# df = 0.25
df0 = df.copy() #0
df50 = df.copy() #50

df0["Summa blankning"] = df0["Summa blankning"].replace(0.25, 0)
df50["Summa blankning"] = df50["Summa blankning"].replace(0.25, 0.5)


#%%
un_innehavare = df["Innehavare"].unique()
un_emittent = df["Emittent"].unique()

#%%
un_holders = (
    df.groupby("Emittent")["Innehavare"]
      .unique()       
)

#%% # detta är 0.25, gör resten senare. skoja det är för mycket positioner som stängdes för flera år sedan som
# fortfarande räknas in vilket skewer datat ännu mer. så jag kör nollan

holder_tx = {}

for emittent, holders in un_holders.items():
    e_dict = {}
    for holder in holders:
        subset = df0[(df0["Emittent"] == emittent) & (df0["Innehavare"] == holder)]
        if not subset.empty:
            e_dict[holder] = subset.copy()
    if e_dict:
        holder_tx[emittent] = e_dict

#%%
daily_emittent = {}

for emittent, holders in holder_tx.items():
    holder_series = []
    for innehavare, dataf in holders.items():
        dataf = dataf.sort_index()
        s = dataf['Summa blankning']
        s = s.groupby(s.index).last()
        s.name = innehavare
        holder_series.append(s)
        
    holders_df = pd.concat(holder_series, axis=1)
    holders_df = holders_df.ffill().fillna(0)
    total_blank = holders_df.sum(axis=1)
    
    daily_total = total_blank.resample("D").last()
    daily_emittent[emittent] = daily_total
    
daily_df = pd.DataFrame(daily_emittent)
daily_df = daily_df.sort_index()
daily_df = daily_df.ffill().fillna(0)
#%%
daily_df['Average_Positions'] = daily_df.mean(axis=1)
daily_df['Average_Positions_no0'] = daily_df.replace(0, pd.NA).mean(axis=1)
daily_df = daily_df[daily_df.index >= '2012-11-01 00:00:00']


#%%

#%%
import yfinance as yf

omx = yf.download('^OMX', start='2012-11-01', end='2025-12-19',interval='1d')
#%%
X = daily_df.iloc[:,0:-2]
#%%
y_index = omx.index.sort_values().unique()
X = X.reindex(y_index) 
    









