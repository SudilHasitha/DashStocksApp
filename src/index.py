import dash
from dash import dcc, Input, Output, State, callback, Dash, html
import plotly.graph_objs as go
import pandas_datareader.data as web
from datetime import datetime 
from dotenv import load_dotenv
import os as os
import pandas as pd

load_dotenv()
app = dash.Dash(__name__)

# getting index list for input dropdown
df = pd.read_csv('DashStocksApp\\data\\NASDAQcompanylist.csv')

# get the list of tickers
tickers = [{'label':j + " " + i, 'value':i} for i,j in zip(df['Symbol'].tolist(),df['Name'].tolist())]

# Make layout
app.layout = html.Div([

    html.H1('Stock Ticker Dashboard'),
    html.Div([
        html.H3('Enter a stock symbol:', style={'paddingRight':'30px'}),
        dcc.Dropdown(
            id='stock_picker',
            options=tickers,
            value=['TSLA'],
            multi=True
        )

    ],  style={'display':'inline-block', 'verticalAlign':'top', 'witdh':'30%'}),

     html.Div([
        html.H3('Select start and end dates:'),
        dcc.DatePickerRange(
            id='date_picker',
            start_date = datetime(2015, 1, 1),
            end_date = datetime.today()
        )
    ], style={'display':'inline-block'}),

    html.Div([
        html.Button(
            id='submit_button',
            n_clicks=0,
            children='Submit',
            style={'fontSize':'24', 'marginLeft':'30px'}
        )
    ], style={'display':'inline-block'}),


   dcc.Graph(
        id='graph-content',
        figure={
            'data': [
                {'x': [ datetime(2015, 1, 1), datetime.today()], 'y': [3,1]}
            ]
        }
    ),

    html.Div([
        html.H3('Live flight data :'),
        html.Iframe(src='http://www.flightradar24.com/simple_index.php?lat=43.9&lon=0.3&z=8', height=500, width=1200),
        html.Div([
            html.Pre(id='counter_text', children='Active flights worldwide:'),
             dcc.Graph(
            id='live-update-graph',
            style={'width':1200}
        ),
            dcc.Interval(
                id='interval-component',
                interval=12000,
                n_intervals=0
            )
       ])
    ])
])

# Make callback
@callback(
    Output('graph-content', 'figure'),
    Input('submit_button', 'n_clicks'),
    State('stock_picker', 'value'),
    State('date_picker', 'start_date'),
    State('date_picker', 'end_date'),

)
def update_graph(n_clicks,stock_ticker, start_date, end_date):

    start_date = datetime.strptime(start_date[:10], '%Y-%m-%d')
    end_date = datetime.strptime(end_date[:10], '%Y-%m-%d')

    ticker = []

    for tic in stock_ticker:
        df = web.DataReader(tic, 'quandl', start=start_date, end=end_date, api_key=os.environ.get('api_key'))
        ticker.append({'x':df.index.tolist(),'y':df.Close,'name':tic})
    
    fig = {
        'data': ticker,
        'layout': go.Layout(
            title=f'Scatter Plot for {", ".join(stock for stock in stock_ticker)}',
            hovermode='closest'
        )
        
    }
    return fig

@callback(
    Output('counter_text', 'figure'),
    Input('interval-component', 'n_intervals')
)
def update_fligt_count(n):
    # get data from website
    url = 'https://data-live.flightradar24.com/zones/fcgi/feed.js?faa=1'
    df = pd.read_json(url)
    return df['full_count']

# update graph
@callback(
    Output('live-update-graph', 'figure'),
    Input('interval-component', 'n_intervals')
)
def update_graph_live(n):
    # get data from website
    url = 'https://data-live.flightradar24.com/zones/fcgi/feed.js?faa=1'
    df = pd.read_json(url)
    # clean data
    data = df.reset_index()
    data = data.rename(columns={'index':'flight'})
    data = data.dropna(subset=['lat','lon'],axis=0)
    # create graph
    fig = go.Figure(data=go.Scattergeo(
        lon = data['lon'],
        lat = data['lat'],
        text = data['flight'],
        mode = 'markers',
        marker_color = data['altitude'],
        ))

    fig.update_layout(
        title_text = 'Live flight data',
        showlegend = False,
        geo = dict(
            scope = 'europe',
            landcolor = 'rgb(217, 217, 217)',
        )
    )
    return fig


if __name__ == '__main__':
    app.run_server(debug=True)