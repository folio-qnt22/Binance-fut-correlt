import dash
import schedule
from scipy import signal
import plotly
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
import time

from datetime import timedelta, datetime
from dateutil import parser
import urllib.request, json
import requests
from dash import Dash, dcc, html, Input, Output
import plotly
from dash.dependencies import Input, Output
import paramiko
#test

def recent_price(symbol="BTCUSDT", interval="1m", limit=1):
    data = requests.get(
        "https://fapi.binance.com/fapi/v1/klines",
        params={
            "symbol": symbol,
            "interval": interval,
            # "startTime" : startTime,
            "limit": limit,
        },
    ).json()
    data = pd.DataFrame(
        data,
        columns=[
            "timestamp",
            "open",
            "high",
            "low",
            "close",
            "volume",
            "close_time",
            "quote_vol",
            "no_of_trades",
            "tb_base_vol",
            "tb_quote_vol",
            "ignore",
        ],
    )
    data.iloc[:, 1:] = data.iloc[:, 1:].astype(float)
    data["time"] = pd.to_datetime(data["timestamp"], unit="ms")
    return data


tickers = [
    "BTCUSDT",
    "ETHUSDT",
    "BCHUSDT",
    "XRPUSDT",
    "EOSUSDT",
    "LTCUSDT",
    "TRXUSDT",
    "ETCUSDT",
    "LINKUSDT",
    "XLMUSDT",
    "ADAUSDT",
    "XMRUSDT",
    "DASHUSDT",
    "ZECUSDT",
    "XTZUSDT",
    "BNBUSDT",
    "ATOMUSDT",
    "ONTUSDT",
    "IOTAUSDT",
    "BATUSDT",
    "VETUSDT",
    "NEOUSDT",
    "QTUMUSDT",
    "IOSTUSDT",
    "THETAUSDT",
    "ALGOUSDT",
    "ZILUSDT",
    "KNCUSDT",
    "ZRXUSDT",
    "COMPUSDT",
    "OMGUSDT",
    "DOGEUSDT",
    "SXPUSDT",
    "KAVAUSDT",
    "BANDUSDT",
    "RLCUSDT",
    "WAVESUSDT",
    "MKRUSDT",
    "SNXUSDT",
    "DOTUSDT",
    "DEFIUSDT",
    "YFIUSDT",
    "BALUSDT",
    "CRVUSDT",
    "TRBUSDT",
    "YFIIUSDT",
    "RUNEUSDT",
    "SUSHIUSDT",
    "SRMUSDT",
    "EGLDUSDT",
    "SOLUSDT",
    "ICXUSDT",
    "STORJUSDT",
    "BLZUSDT",
    "UNIUSDT",
    "AVAXUSDT",
    "FTMUSDT",
    "HNTUSDT",
    "ENJUSDT",
    "FLMUSDT",
    "TOMOUSDT",
    "RENUSDT",
    "KSMUSDT",
    "NEARUSDT",
    "AAVEUSDT",
    "FILUSDT",
    "RSRUSDT",
    "LRCUSDT",
    "MATICUSDT",
    "OCEANUSDT",
    "CVCUSDT",
    "BELUSDT",
    "CTKUSDT",
    "AXSUSDT",
    "ALPHAUSDT",
    "ZENUSDT",
    "SKLUSDT",
    "GRTUSDT",
    "1INCHUSDT",
    "BTCBUSD",
    "AKROUSDT",
    "CHZUSDT",
    "SANDUSDT",
    "ANKRUSDT",
    "LUNAUSDT",
    "BTSUSDT",
    "LITUSDT",
    "UNFIUSDT",
    "DODOUSDT",
    "REEFUSDT",
    "RVNUSDT",
    "SFPUSDT",
    "XEMUSDT",
    "BTCSTUSDT",
    "COTIUSDT",
    "CHRUSDT",
    "MANAUSDT",
    "ALICEUSDT",
    "HBARUSDT",
    "ONEUSDT",
    "LINAUSDT",
    "STMXUSDT",
    "DENTUSDT",
    "CELRUSDT",
    "HOTUSDT",
    "MTLUSDT",
    "OGNUSDT",
    "NKNUSDT",
    "SCUSDT",
    "DGBUSDT",
    "1000SHIBUSDT",
    "ICPUSDT",
    "BAKEUSDT",
    "GTCUSDT",
    "ETHBUSD",
    "BTCDOMUSDT",
    "TLMUSDT",
    "BNBBUSD",
    "ADABUSD",
    "XRPBUSD",
    "IOTXUSDT",
    "DOGEBUSD",
    "AUDIOUSDT",
    "RAYUSDT",
    "C98USDT",
    "MASKUSDT",
    "ATAUSDT",
    "SOLBUSD",
    "FTTBUSD",
    "DYDXUSDT",
    "1000XECUSDT",
    "GALAUSDT",
    "CELOUSDT",
    "ARUSDT",
    "KLAYUSDT",
    "ARPAUSDT",
    "CTSIUSDT",
    "LPTUSDT",
    "ENSUSDT",
    "PEOPLEUSDT",
    "ANTUSDT",
    "ROSEUSDT",
    "DUSKUSDT",
    "1000BTTCUSDT",
    "FLOWUSDT",
    "IMXUSDT",
    "API3USDT",
    "ANCUSDT",
    "GMTUSDT",
    "APEUSDT",
    "BTCUSDT_220624",
    "ETHUSDT_220624",
    "BNXUSDT",
]

app = Dash(__name__)

server = app.server

app.layout = html.Div(
    [
        dcc.Dropdown(
            id="Altcoins",
            options=tickers,
            multi=True,
            value=tickers,
            className="Altcoins",
        ),
        dcc.Dropdown(
            id="Correlation Window",
            options=[15, 30, 60, 90, 120, 180],
            multi=False,
            value=[15, 30, 60, 90, 120, 180],
            placeholder="Correlation Window",
            className="crr_window",
        ),
        dcc.Interval(id="refresh", interval=10000, n_intervals=0),
        dcc.Graph(id="live-update-graph_1"),
    ]
)


@app.callback(
    Output(component_id="live-update-graph_1", component_property="figure"),
    [
        Input("refresh", "n_intervals"),
        Input("Altcoins", "value"),
        Input("Correlation Window", "value"),
    ],
)
def update_graph(refresh, Altcoins, crr_window):
    def price_plot(altcoin, color="#00b6ff", corr_win=30):
        altcoin_kline = recent_price(symbol=altcoin, interval="1m", limit="1000")
        fig.add_trace(
            go.Scatter(
                x=BTC["time"],
                y=BTC["close"].rolling(corr_win).corr(altcoin_kline["close"]),
                mode="lines",
                name=f"{altcoin}",
            )
        )

    ###################################################################################################################################################
    BTC = recent_price(symbol="BTCUSDT", interval="1m", limit="1000")
    ###################################################################################################################################################

    layout = dict(
        # height = 600,
        mapbox=dict(uirevision="no reset of zoom", style="light"),
    )
    fig = make_subplots(rows=1, cols=1)
    for name in Altcoins:
        price_plot(altcoin=name, corr_win=crr_window)

    fig.update_layout(showlegend=True)
    fig.update_layout(height=800, width=1600, margin=dict(b=30))
    fig.update_layout(
        autosize=True,
        # scaleratio=1
        # width=1200,
        # height=800,
        yaxis=dict(
            title_text="Correlation",
            # titlefont=dict(size=30),
        ),
    )
    fig.update_layout(xaxis_rangeslider_visible=False)
    fig.update_layout(uirevision=True)
    fig.update_layout(
        title={
            "text": f"BTC-ALT correlations 1m Timeframe",
            #'y':0.9,
            #'x':0.5,
            "xanchor": "left",
            "yanchor": "top",
        }
    )
    return fig

    return  # price_plot(altcoin=Altcoins)


if __name__ == "__main__":
    app.run_server(debug=False)
