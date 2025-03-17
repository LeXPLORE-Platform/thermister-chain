import os
import sys
import numpy as np
import pandas as pd
import xarray as xr
from datetime import datetime, date
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from dash import Dash, dcc, html, Input, Output, callback_context

app = Dash(__name__)
app.layout = html.Div([
    html.Div([
        dcc.DatePickerRange(
            id='date-picker-range',
            start_date=date(2022, 1, 1),
            end_date=date(2022, 1, 14)
        )
    ], style={'marginLeft': '60px', 'marginTop': '20px'}),
    dcc.Graph(id='data-graph', style={'height': '700px'})
])
x_slice_index = 0
y_slice_index = 0

@app.callback(
    Output('data-graph', 'figure'),
    [Input('data-graph', 'clickData')],
    Input('date-picker-range', 'start_date'),
    Input('date-picker-range', 'end_date')
)
def update_figure(click_data, start_date, end_date):
    global x_slice_index, y_slice_index
    start = datetime.strptime(start_date.split('T')[0], '%Y-%m-%d')
    end = datetime.strptime(end_date.split('T')[0], '%Y-%m-%d')
    folder = os.path.abspath(os.path.join(os.path.dirname(sys.argv[0]), "..", "data", "Level2"))
    files = [os.path.join(folder, f) for f in os.listdir(folder)]
    files.sort()
    with xr.open_mfdataset(files) as ds:
        ds = ds.sel(time=slice(start, end))
        x = ds.time.values
        y = -ds.depth.values
        z = np.array(ds.temp.values)
        if "temp_qual" in ds:
            z_qual = ds.temp_qual.values
            z[z_qual > 0] = np.nan
        mask = ~np.all(np.isnan(z), axis=1)
        y = y[mask]
        z = z[mask]

    x_numeric = pd.Series(x).astype(np.int64).values
    x_slice_index = 0
    y_slice_index = 0

    if click_data is not None and 'points' in click_data and len(click_data['points']) > 0:
        point = click_data['points'][0]
        if 'x' in point and 'y' in point:
            click_x = point['x']
            if isinstance(click_x, str):
                try:
                    click_x_dt = pd.to_datetime(click_x)
                    click_x_numeric = click_x_dt.value
                    x_slice_index = np.abs(x_numeric - click_x_numeric).argmin()
                except:
                    pass
            else:
                try:
                    click_x_numeric = pd.to_datetime(click_x).value
                    x_slice_index = np.abs(x_numeric - click_x_numeric).argmin()
                except:
                    pass
            y_slice_index = np.abs(y - point['y']).argmin()

    fig = make_subplots(
        rows=2, cols=2,
        column_widths=[0.2, 0.8],
        row_heights=[0.8, 0.2],
        shared_xaxes=True,
        shared_yaxes=True,
        horizontal_spacing=0.02,
        vertical_spacing=0.05,
        subplot_titles=(x[x_slice_index].astype(str), "", "", str(-y[y_slice_index]) + "m")
    )

    heatmap = go.Heatmap(
        z=z,
        x=x,
        y=y,
        colorscale='RdBu_r',
        colorbar=dict(title=''),
        hovertemplate='Time: %{x}<br>Depth: %{y}<br>Temperature: %{z:.2f}°C<extra></extra>'
    )
    fig.add_trace(heatmap, row=1, col=2)

    if len(x) > 0 and len(y) > 0:
        x_clean = z[:, x_slice_index]
        y_clean = y

        valid_indices = ~np.isnan(x_clean) & ~np.isnan(y_clean)
        x_clean = x_clean[valid_indices]
        y_clean = y_clean[valid_indices]

        v_slice = go.Scatter(
            x=x_clean,
            y=y_clean,
            mode='lines',
            name=f'Vertical Slice',
        )
        fig.add_trace(v_slice, row=1, col=1)

    if len(x) > 0 and len(y) > 0 and y_slice_index < len(y):
        h_slice = go.Scatter(
            x=x,
            y=z[y_slice_index, :],
            mode='lines',
            name=f'Horizontal Slice'
        )
        fig.add_trace(h_slice, row=2, col=2)

    fig.update_layout(
        height=700,
        legend=dict(orientation="h", y=-0.1),
        margin=dict(l=60, r=30, t=50, b=60),
    )
    return fig

if __name__ == '__main__':
    app.run_server(debug=True, use_reloader=False, port=8050)
