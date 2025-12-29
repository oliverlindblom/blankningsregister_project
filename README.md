#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Dec 29 11:36:00 2025

@author: oliverlindblom
"""

# Blankningsregister Portfolio Backtester

Machine-learning–driven short-selling and portfolio backtesting framework built on Swedish short sale register 
data and OMXS30 index prices. The project includes data processing, model training (Random Forest), a simple 
portfolio simulator, and an interactive Dash dashboard. Big improvements can be made to the machine learning part
and the portfolio part which would benifit from leverage and a more sophisticated risk management system.

Recommended starting setting: Horizon: 5, Threshold: 51, Position size: 50

The portfolio seems to have an edge when the underlying index is weaker, but when it is bullish it just goes to 100%
exposure and follows it 1:1. This could maybe be solved with the addition of leverage and changing it to more of a 
hedgingstretegy. Right now it reverts back to 100% cash if there are no singals. If it instead reverted back to 
a benchmark (for example 50/50 index and cash or 100% index) I believe it would be much more effective.

## Project structure

- `blankningsregister.py`  
  Loads and cleans the Swedish short-selling register (`HistoriskaPositioner.ods`), normalizes issuer/holder 
  names, and builds a daily time series of short positions per stock. The script then:
  - Aggregates short positions per issuer and holder.
  - Resamples to daily frequency and forward-fills.
  - Computes average short interest metrics.
  - Downloads OMXS30 index data from Yahoo Finance.
  - Aligns the features (`X`) with the OMXS30 date index.[file:174]

- `blankning_stat.py`  
  Contains core modelling utilities:
  - `make_train_test_split(omx, X, horizon)`  
    Creates log returns for OMXS30, builds a binary target (up/down), and returns a 70/30 time-ordered 
    train/test split for a given forecast horizon.[file:175]
  - `train_random_forest(X_train, y_train, X_test)`  
    Trains a `RandomForestClassifier` and returns predictions and class probabilities on the test set.[file:175]
  - `make_threshold_signal(proba, X_test, avkt1, thresh)`  
    Converts predicted probabilities into trading signals (long / short / flat) based on a probability 
    threshold, and computes performance metrics for long and short trades.[file:175]

- `portfolio.py`  
  - Re-runs the modelling pipeline (train/test split, Random Forest, threshold signal).  
  - Defines the `Omxs30Portfolio` class, which:
    - Simulates a portfolio invested in OMXS30 with time‑varying net exposure in \([-1, 1]\).
    - Uses a `horizon` parameter to hold each position for a fixed number of days.
    - Tracks portfolio value, exposure, and a buy‑and‑hold OMXS30 benchmark.[file:176]

- `dashboard.py`  
  Dash/Plotly web application that wraps the full pipeline:
  - User inputs:
    - Forecast horizon (days)
    - Probability threshold
    - Position size (percent per step)
  - On “Kör Backtest”, it:
    - Rebuilds the dataset and train/test split.
    - Trains the Random Forest and generates signals.
    - Runs the `Omxs30Portfolio` simulator.
    - Displays:
      - Portfolio value vs OMXS30
      - Net exposure over time.[file:177]


