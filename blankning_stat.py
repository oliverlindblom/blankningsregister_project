#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Dec 22 20:16:20 2025

@author: oliverlindblom
"""

import numpy as np

def make_train_test_split(omx, X, horizon):
    # log-pris
    omxt0 = np.log(omx['Close'])
    omxt1 = omxt0.shift(-horizon)
    avkt1 = omxt1 - omxt0

    # ta bort sista 'horizon' raderna
    avkt1 = avkt1[0:-horizon]
    X = X[0:-horizon]

    # binär target
    y = (avkt1 > 0).astype(int)
    y = y.values.ravel()

    # 70/30-split
    n = len(X)
    split_idx = int(n * 0.7)

    X_train = X.iloc[:split_idx]
    X_test  = X.iloc[split_idx:]

    y_train = y[:split_idx]
    y_test  = y[split_idx:]

    return avkt1, X_train, X_test, y_train, y_test


#%%
from sklearn.ensemble import RandomForestClassifier

def train_random_forest(X_train, y_train, X_test):
    forest = RandomForestClassifier(
        n_estimators=10000,
        random_state=42,
        n_jobs=-1
    )

    forest.fit(X_train, y_train)

    y_pred_forest = forest.predict(X_test)
    proba = forest.predict_proba(X_test)

    return y_pred_forest, proba



#%%

import numpy as np
import pandas as pd

def make_threshold_signal(proba, X_test, avkt1, thresh):
    """
    proba : ndarray från predict_proba(X_test), shape (n_samples, 2)
    X_test: DataFrame med index som ska användas för signalen
    avkt1 : pd.Series med logavkastning (t.ex. 1-dag eller h-dag)
    thresh: tröskel för sannolikhet (t.ex. 0.55)
    """

    proba_up = proba[:, 1]
    proba_down = proba[:, 0]

    proba_series = pd.Series(proba_up, index=X_test.index, name='proba_up')
    san = proba_series >= thresh
    high_conf_days = proba_series[san]

    proba_down_series = pd.Series(proba_down, index=X_test.index, name='proba_down')
    san_down = proba_down_series >= thresh
    high_conf_down_days = proba_down_series[san_down]

    # signal: 1 = long, -1 = short, 0 = neutral
    signal = pd.Series(0, index=X_test.index, dtype=int)
    signal[proba_up >= thresh] = 1
    signal[proba_down >= thresh] = -1

    # matcha avkastning mot testindex
    avkt1_test = avkt1.loc[X_test.index]

    # long-dagar
    long_ret = avkt1_test[signal == 1]
    # short-dagar
    short_ret = avkt1_test[signal == -1]

    # total logavkastning
    sum_long_log = long_ret.sum()
    sum_short_log = short_ret.sum()

    # omvandlat till procent
    tot_long = np.exp(sum_long_log) - 1
    tot_short = np.exp(sum_short_log) - 1

    return {
        "signal": signal,
        "high_conf_up": high_conf_days,
        "high_conf_down": high_conf_down_days,
        "tot_long": tot_long,
        "tot_short": tot_short,
        "avkt1_test": avkt1_test
    }





