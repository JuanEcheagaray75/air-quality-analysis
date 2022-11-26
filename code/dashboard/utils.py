import pandas as pd
import altair as alt
from prep.cleaning import *


def miss_vals_graph(miss_vals_report: pd.DataFrame) -> alt.Chart:

    report = miss_vals_report.copy()
    meteo_miss =  report[report.parameter.isin(meteo_params)]
    cont_miss = report[report.parameter.isin(cont_params)]
    # Map the station names to the actual station names
    meteo_miss.station = meteo_miss.station.map(locations)
    cont_miss.station = cont_miss.station.map(locations)

    chart1 = alt.Chart(meteo_miss).mark_bar().encode(
        x='station:N',
        y='missing_values:Q',
        color='parameter:N',
        tooltip=['station', 'parameter', 'missing_values']
    ).properties(
        title='Meteorological parameters',
        height=300,
        width=300
    )

    chart2 = alt.Chart(cont_miss).mark_bar().encode(
        x='station:N',
        y='missing_values:Q',
        color='parameter:N',
        tooltip=['parameter', 'missing_values']
    ).properties(
        title='Contaminant parameters',
        height=300,
        width=300
    )

    gen_chart = alt.hconcat(chart1, chart2)

    return gen_chart


def metric_calculator(df: pd.DataFrame, day_range: int, type: str) -> pd.DataFrame:

    range_max = df.date.max()
    try:
        range_between = range_max - pd.Timedelta(days=day_range)
        range_min = range_max - pd.Timedelta(days=2 * day_range)
    except TypeError:
        return TypeError('The day_range must be an integer')

    last = df[(df.date >= range_between) & (df.date <= range_max)]
    last_last = df[(df.date >= range_min) & (df.date <= range_between)]

    if type == 'cont':
        last = last[last.parameter.isin(cont_params)]
        last_last = last_last[last_last.parameter.isin(cont_params)]

    elif type == 'meteo':
        last = last[last.parameter.isin(meteo_params)]
        last_last = last_last[last_last.parameter.isin(meteo_params)]

    last.value = pd.to_numeric(last.value, errors='coerce')
    last_last.value = pd.to_numeric(last_last.value, errors='coerce')

    # Calculate average of each parameter across all stations
    means = last.groupby('parameter')['value'].mean().reset_index()
    means_last = last_last.groupby('parameter')['value'].mean().reset_index()

    diffs = means.value - means_last.value
    diffs.index = means.parameter

    # Merge means and diffs
    means = means.merge(diffs.reset_index(), on='parameter')
    means.columns = ['parameter', 'mean', 'diff']
    means.set_index('parameter', inplace=True)

    return means


def create_time_series(df: pd.DataFrame, station: str, param: str, time_range: str, type: str) -> alt.Chart:
    df = df.copy()
    num_cols = df.select_dtypes(include='number').columns
    # add the date column
    num_cols = num_cols.insert(0, 'date')
    data = df[num_cols][['date', f'{locations[station]}-{param}']]

    try:
        data = data.groupby(pd.Grouper(key='date', freq=time_range)).mean().reset_index()
    except ValueError:
        return ValueError('The time_range must be a valid pandas frequency string')

    # Make a time series plot
    if type == 'cont':
        units = cont_units
    elif type == 'meteo':
        units = meteo_units

    # Consult https://altair-viz.github.io/user_guide/compound_charts.html for more info
    nearest = alt.selection(type='single', nearest=True, on='mouseover', fields=['date'], empty='none')

    line = alt.Chart(data).mark_line(point=True, color='#1c9133').encode(
        x='date:T',
        y=alt.Y(f'{locations[station]}-{param}', title=f'{param} ({units[param]})'),
        # Set digits shown in tooltip
        tooltip=[
            alt.Tooltip('date:T', title='Date', format='%Y-%m-%d'),
            alt.Tooltip(f'{locations[station]}-{param}', title=f'{param} ({units[param]})', format='.3f')],
    )
    selectors = alt.Chart(data).mark_point(color='#084d15').encode(
        x='date:T',
        opacity=alt.value(0),
    ).add_selection(
        nearest
    )
    points = line.mark_point(color='#084d15').encode(
        opacity=alt.condition(nearest, alt.value(1), alt.value(0)),
    )
    rules = alt.Chart(data).mark_rule(color='gray').encode(
        x='date:T',
    ).transform_filter(
        nearest
    )
    chart = alt.layer(line, selectors, rules, points).properties(
        title=f'{locations[station]}-{param}',
        height=300,
        width=900
    ).interactive()

    return chart

def create_box_plot(df: pd.DataFrame, station: str, param: str, time_range: str, type: str):

    df = df.copy()
    num_cols = df.select_dtypes(include='number').columns
    num_cols = num_cols.insert(0, 'date')
    data = df[num_cols] [['date', f'{locations[station]}-{param}']]
    data = data.groupby(pd.Grouper(key='date', freq='D')).mean().reset_index()
    # Create a new column with the month of the observation
    data['month'] = data.date.dt.month

    chart = alt.Chart(data).mark_boxplot(size=60).encode(
        x='month:O',
        y=alt.Y(f'{locations[station]}-{param}', title=f'{param}'),
        color=alt.Color('month:O', legend=None)
    ).properties(
        title=f'{locations[station]}-{param}',
        height=300,
        width=900
    ).interactive()

    return chart