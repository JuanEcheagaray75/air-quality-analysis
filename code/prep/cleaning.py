import pandas as pd
from os.path import exists



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

    if exists(f'../data/processed/{name}.csv'):
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

