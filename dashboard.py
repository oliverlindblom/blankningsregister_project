#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Dec 29 07:15:35 2025

@author: oliverlindblom
"""
"""
porfölj function gör en class kanske?
1. start innehav, 2. storlek per position, 3. allow margin, 
4. graf funktion för både vanliga jämförelsen och 5. portföljens
fördelning
"""


import dash
from dash import html, dcc, Input, Output, State
import plotly.graph_objs as go
from threading import Timer
import webbrowser

from blankning_stat import make_train_test_split, train_random_forest, make_threshold_signal
from blankningsregister import X, omx
from portfolio import Omxs30Portfolio

# Styling
colors = {
    'background': '#1a1a1a',
    'paper': '#2d2d2d',
    'text': '#ffffff',
    'accent': '#3b82f6'
}

def create_value_figure(portfolio_values, benchmark_values):
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=portfolio_values.index,
        y=portfolio_values.values,
        name='Portfölj',
        line=dict(color=colors['accent'], width=2)
    ))
    
    fig.add_trace(go.Scatter(
        x=benchmark_values.index,
        y=benchmark_values.values,
        name='OMXS30',
        line=dict(color='#f59e0b', width=2, dash='dash')
    ))
    
    fig.update_layout(
        title='Portföljvärde vs OMXS30',
        xaxis_title='Datum',
        yaxis_title='Värde',
        plot_bgcolor=colors['background'],
        paper_bgcolor=colors['paper'],
        font=dict(color=colors['text']),
        hovermode='x unified',
        height=500
    )
    
    return fig

def create_exposure_figure(exposure_series):
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=exposure_series.index,
        y=exposure_series.values,
        fill='tozeroy',
        line=dict(color=colors['accent'], width=2),
        name='Nettoexponering'
    ))
    
    fig.add_hline(y=0, line_dash="dash", line_color="white", line_width=1)
    
    fig.update_layout(
        title='Nettoexponering över tid',
        xaxis_title='Datum',
        yaxis_title='Exponering',
        plot_bgcolor=colors['background'],
        paper_bgcolor=colors['paper'],
        font=dict(color=colors['text']),
        yaxis=dict(tickformat='.0%'),
        height=400
    )
    
    return fig

# Initialize app
app = dash.Dash(__name__)
app.title = "Portfolio Dashboard"

# Layout
app.layout = html.Div(
    style={'backgroundColor': colors['background'], 'padding': '20px', 'minHeight': '100vh'},
    children=[
        html.H1('Blankningsregister Portfolio', style={'color': colors['text'], 'textAlign': 'center'}),
        
        # Controls
        html.Div(
            style={'backgroundColor': colors['paper'], 'padding': '20px', 'borderRadius': '5px', 'marginBottom': '20px'},
            children=[
                html.Div(
                    style={'display': 'grid', 'gridTemplateColumns': 'repeat(3, 1fr)', 'gap': '20px'},
                    children=[
                        html.Div([
                            html.Label('Horizon (dagar)', style={'color': colors['text']}),
                            dcc.Input(
                                id='horizon-input',
                                type='number',
                                value=5,
                                min=1,
                                max=30,
                                style={'width': '100%', 'padding': '8px', 'marginTop': '5px'}
                            )
                        ]),
                        html.Div([
                            html.Label('Threshold', style={'color': colors['text']}),
                            dcc.Input(
                                id='thresh-input',
                                type='number',
                                value=0.55,
                                min=0.5,
                                max=0.95,
                                step=0.01,
                                style={'width': '100%', 'padding': '8px', 'marginTop': '5px'}
                            )
                        ]),
                        html.Div([
                            html.Label('Position Size (%)', style={'color': colors['text']}),
                            dcc.Input(
                                id='position-size-input',
                                type='number',
                                value=100,
                                min=1,
                                max=100,
                                style={'width': '100%', 'padding': '8px', 'marginTop': '5px'}
                            )
                        ])
                    ]
                ),
                html.Button(
                    'Kör Backtest',
                    id='run-button',
                    n_clicks=0,
                    style={
                        'marginTop': '20px',
                        'padding': '10px 30px',
                        'backgroundColor': colors['accent'],
                        'color': 'white',
                        'border': 'none',
                        'borderRadius': '5px',
                        'cursor': 'pointer',
                        'width': '100%'
                    }
                )
            ]
        ),
        
        # Graphs
        dcc.Loading(
            children=[
                html.Div(
                    style={'backgroundColor': colors['paper'], 'padding': '20px', 'borderRadius': '5px', 'marginBottom': '20px'},
                    children=[dcc.Graph(id='value-graph')]
                ),
                html.Div(
                    style={'backgroundColor': colors['paper'], 'padding': '20px', 'borderRadius': '5px'},
                    children=[dcc.Graph(id='exposure-graph')]
                )
            ]
        )
    ]
)

@app.callback(
    [Output('value-graph', 'figure'),
     Output('exposure-graph', 'figure')],
    [Input('run-button', 'n_clicks')],
    [State('horizon-input', 'value'),
     State('thresh-input', 'value'),
     State('position-size-input', 'value')],
    prevent_initial_call=True
)
def update_dashboard(n_clicks, horizon, thresh, position_size_pct):
    horizon = int(horizon)
    thresh = float(thresh)
    position_size_pct = float(position_size_pct) / 100.0
    
    # Run model
    avkt1, X_train, X_test, y_train, y_test = make_train_test_split(omx, X, horizon)
    y_pred_forest, proba = train_random_forest(X_train, y_train, X_test)
    results = make_threshold_signal(proba, X_test, avkt1, thresh)
    
    signal = results["signal"]
    
    # Calculate returns
    omx_test = omx['Close'].reindex(X_test.index)
    index_returns = omx_test.pct_change().fillna(0.0)
    
    # Run portfolio
    portfolio = Omxs30Portfolio(
        dates=X_test.index,
        index_returns=index_returns,
        start_value=100.0,
        start_invested_pct=0.0,
        position_size_pct=position_size_pct,
        horizon=horizon
    )
    
    portfolio.run(signal)
    
    # Create figures
    value_fig = create_value_figure(portfolio.values, portfolio.benchmark)
    exposure_fig = create_exposure_figure(portfolio.exposure)
    
    return value_fig, exposure_fig

def open_browser():
    webbrowser.open_new('http://localhost:8050')

if __name__ == '__main__':
    Timer(1, open_browser).start()
    app.run(debug=True, host='localhost', port=8050)


