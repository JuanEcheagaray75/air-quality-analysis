import pandas as pd
from os.path import exists
import altair as alt


# GENERAL VARIABLES
# -------------------------------------------------------------------
locations = {
        "Guadalupe, La Pastora" : "SE",
        "San Nicolás de los Garzas, San Nicolás" : "NE",
        "Monterrey, Obispado" : "CE",
        "Monterrey, San Bernabé": "NO",
        "Santa Catarina, Santa Catarina": "SO",
        "García, García" : "NO2",
        "Escobedo, Escobedo": "Norte",
        "Apodaca, Apodaca" : "NE2",
        "Juárez, Juárez" : "SE2",
        "San Pedro Garza García, San Pedro": "SO2"
        }

meteo_params = ['TOUT', 'RH', 'SR', 'RAINF', 'PRS', 'WSR', 'WDR']
meteo_units = {'TOUT': '°C', 'RH': '%', 'SR': 'kW/m2', 'RAINF': 'mm/Hr', 'PRS': 'mm Hg', 'WSR': 'km/hr', 'WDR': '°'}
cont_params = ['PM10', 'PM2.5', 'O3', 'NO2', 'SO2', 'CO']
cont_units = {'PM10': 'µg/m3', 'PM2.5': 'µg/m3', 'O3': 'ppb', 'NO2': 'ppb', 'SO2': 'ppb', 'CO': 'ppm'}
# -------------------------------------------------------------------


def melt_data(df: pd.DataFrame) -> pd.DataFrame:

    columns = df.columns
    columns = columns.drop(['date', 'parameter'])
    df.parameter = df.parameter.str.strip()
    df.date = pd.to_datetime(df.date)
    df = df.melt(id_vars=['date', 'parameter'], value_vars=columns, var_name='station', value_name='value')

    return df


def save_data(df, name):

    if exists(f'data/clean/{name}.csv'):
        print(f'{name} already exists')

        if input(f'{name} already exists. Overwrite? (y/n)') == 'y':
            df.to_csv(f'data/clean/{name}.csv', index=False)


def clean_data(df, station):

    try:
        location = locations[station]

    except KeyError:
        print(f'Location {station} not found')
        return

    df = df.query(f'station == "{location}" or station == "{location}_b"')
    df = pd.pivot(df, index='date', columns=['station', 'parameter'], values='value')
    df.reset_index(inplace=True)
    df.columns = [col[0] + '-' + col[1] if col[0] != 'date' else col[0] for col in df.columns]

    num_columns = df.columns[~df.columns.str.contains('_b')]
    num_columns = num_columns.drop('date')
    df[num_columns] = df[num_columns].astype(float)

    return df

def merge_df(meteo_df, cont_df):
    df = pd.merge(meteo_df, cont_df, how='inner', on='date')

    return df


def diagnose_missing(general_meteo, general_cont):
    missing_vals_report = pd.DataFrame(index=locations.keys(), columns=meteo_params + cont_params)


    for station in locations.keys():
        meteo_df = clean_data(general_meteo, station)
        cont_df = clean_data(general_cont, station)

        meteo_num_cols = meteo_df.columns[~meteo_df.columns.str.contains('_b')]
        meteo_num_cols = meteo_num_cols.drop('date')

        cont_num_cols = cont_df.columns[~cont_df.columns.str.contains('_b')]
        cont_num_cols = cont_num_cols.drop('date')

        missing_vals_report.loc[station, meteo_params] = meteo_df[meteo_num_cols].isna().sum().values / meteo_df.shape[0]
        missing_vals_report.loc[station, cont_params] = cont_df[cont_num_cols].isna().sum().values / cont_df.shape[0]

    missing_vals_report.reset_index(inplace=True)
    missing_vals_report.rename(columns={'index': 'station'}, inplace=True)

    missing_vals_report = missing_vals_report.melt(id_vars='station',
                                                    value_vars=meteo_params + cont_params,
                                                    var_name='parameter',
                                                    value_name='missing_values')

    # Multiply by 100 to get percentage
    missing_vals_report.missing_values = missing_vals_report.missing_values * 100

    return missing_vals_report


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


def create_time_series(df: pd.DataFrame, station: str, param: str, time_range: str, type: str):
    df = df.copy()
    num_cols = df.select_dtypes(include='number').columns
    # add the date column
    num_cols = num_cols.insert(0, 'date')
    data = df[num_cols] [['date', f'{locations[station]}-{param}']]

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