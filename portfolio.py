#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Dec 29 07:36:36 2025

@author: oliverlindblom
"""

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from blankning_stat import make_train_test_split, train_random_forest, make_threshold_signal
from blankningsregister import X, omx
import matplotlib.pyplot as plt

horizon = 5
thresh = 0.55

avkt1, X_train, X_test, y_train, y_test = make_train_test_split(omx, X, horizon)
y_pred_forest, proba = train_random_forest(X_train, y_train, X_test)
results = make_threshold_signal(proba, X_test, avkt1, thresh)

signal          = results["signal"]

class Omxs30Portfolio:
    def __init__(
        self,
        dates,
        index_returns,          # pd.Series of daily returns for OMXS30 (enkel return)
        start_value=100.0,
        start_invested_pct=0.0, # initial exposure (t.ex. 0 = flat)
        position_size_pct=1.0,  # sätt till 1.0 om du vill hoppa direkt till target
        horizon=1               # antal dagar en position ska hållas
    ):
        self.dates = pd.Index(dates)
        self.index_returns = index_returns.reindex(self.dates).fillna(0.0)
        self.start_value = float(start_value)
        self.start_invested_pct = float(start_invested_pct)
        self.position_size_pct = float(position_size_pct)
        self.horizon = int(horizon)

        self.values = pd.Series(index=self.dates, dtype=float)
        self.exposure = pd.Series(index=self.dates, dtype=float)
        self.benchmark = pd.Series(index=self.dates, dtype=float)

    def _clip_exposure(self, x):
        return np.clip(x, -1, 1)

    def run(self, signal):
        signal = signal.reindex(self.dates).fillna(0.0)

        V = float(self.start_value)
        bench = float(self.start_value)

        exp = self._clip_exposure(self.start_invested_pct)
        days_left = 0

        for dt in self.dates:
            if days_left == 0:
                target = self._clip_exposure(float(signal.loc[dt]))
                delta = target - exp
                step = np.sign(delta) * min(abs(delta), self.position_size_pct)
                exp = self._clip_exposure(exp + step)
                days_left = self.horizon if exp != 0 else 0
            else:
                days_left -= 1

            r_idx = self.index_returns.loc[dt]
            if isinstance(r_idx, (pd.Series, pd.DataFrame)):
                r_idx = float(r_idx.squeeze())

            V = float(V) * (1.0 + exp * float(r_idx))
            bench = float(bench) * (1.0 + float(r_idx))

            self.values.loc[dt] = V
            self.exposure.loc[dt] = exp
            self.benchmark.loc[dt] = bench

    def plot_value_vs_index(self):
        plt.figure(figsize=(10, 5))
        plt.plot(self.values, label="Portfölj")
        plt.plot(self.benchmark, label="OMXS30")
        plt.title("Portföljvärde vs OMXS30")
        plt.legend()
        plt.grid(True)
        plt.show()

    def plot_net_exposure(self):
        plt.figure(figsize=(10, 3))
        plt.plot(self.exposure, label="Nettoexponering (long-short)")
        plt.axhline(0.0, color="black", linewidth=1)
        plt.title("Portföljens nettoexponering över tid")
        plt.legend()
        plt.grid(True)
        plt.show()








