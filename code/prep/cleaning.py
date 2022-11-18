import pandas as pd
import numpy as np
from os.path import exists


# GENERAL VARIABLES
# -------------------------------------------------------------------
locations = {
    "Guadalupe, La Pastora": "SE",
    "San Nicolás de los Garzas, San Nicolás": "NE",
    "Monterrey, Obispado": "CE",
    "Monterrey, San Bernabé": "NO",
    "Santa Catarina, Santa Catarina": "SO",
    "García, García": "NO2",
    "Escobedo, Escobedo": "Norte",
    "Apodaca, Apodaca": "NE2",
    "Juárez, Juárez": "SE2",
    "San Pedro Garza García, San Pedro": "SO2"
}

meteo_params = ['TOUT', 'RH', 'SR', 'RAINF', 'PRS', 'WSR', 'WDR']
meteo_units = {'TOUT': '°C', 'RH': '%', 'SR': 'kW/m2',
               'RAINF': 'mm/Hr', 'PRS': 'mm Hg', 'WSR': 'km/hr', 'WDR': '°'}
cont_params = ['PM10', 'PM2.5', 'O3', 'NO2', 'SO2', 'CO']
cont_units = {'PM10': 'µg/m3', 'PM2.5': 'µg/m3',
              'O3': 'ppb', 'NO2': 'ppb', 'SO2': 'ppb', 'CO': 'ppm'}
# -------------------------------------------------------------------


def melt_data(df: pd.DataFrame) -> pd.DataFrame:
    """Melt the data to get a long format.

    Args:
        df (pd.DataFrame): Raw dataset to be melted

    Returns:
        pd.DataFrame: Melted dataset
    """
    df.drop(columns=['Unnamed: 0'], inplace=True)
    columns = df.columns
    columns = columns.drop(['date', 'parameter'])
    df.parameter = df.parameter.str.strip()
    df.date = pd.to_datetime(df.date)
    df = df.melt(id_vars=['date', 'parameter'], value_vars=list(
        columns), var_name='station', value_name='value')

    return df


def save_data(df: pd.DataFrame, name: str) -> None:
    """Save a clean dataset to processed directory.

    Args:
        df (pd.DataFrame): Clean dataset to be saved in the data/processed folder
        name (str): Name to be given to the file, without extension
    """
    print(f'Saving {name} data...')
    if exists(f'../../data/processed/{name}.csv'):

        if input(f'{name} already exists. Overwrite? (y/n): \n') == 'y':
            df.to_csv(f'../../data/processed/{name}.csv', index=False)
            print(f'{name} overwritten')

    else:
        df.to_csv(f'../../data/processed/{name}.csv', index=False)
        print(f'{name} saved')


def clean_data(df: pd.DataFrame, station: str) -> pd.DataFrame:
    """Perform cleaning operations on the data.

    Args:
        df (pd.DataFrame): Long format dataset
        station (str): Station to be cleaned, must be in the locations dictionary

    Raises:
        KeyError: If the station is not in the locations dictionary

    Returns:
        pd.DataFrame: Cleaned dataset of the specified station
    """
    try:
        location = locations[station]

    except KeyError:
        print(f'Location {station} not found')
        raise KeyError(f'Location {station} not found')

    df = df.query(f'station == "{location}" or station == "{location}_b"')
    df = pd.pivot(df, index='date', columns=[
                  'station', 'parameter'], values='value')
    df.reset_index(inplace=True)
    df.columns = [col[0] + '-' + col[1] if col[0]
                  != 'date' else col[0] for col in df.columns]

    num_columns = df.columns[~df.columns.str.contains('_b')]
    num_columns = num_columns.drop('date')
    df[num_columns] = df[num_columns].astype(float)

    return df


def merge_df(meteo_df: pd.DataFrame, cont_df: pd.DataFrame) -> pd.DataFrame:
    """Generate a merged dataset from the meteorology and contaminants datasets.

    Args:
        meteo_df (pd.DataFrame): Meteorolical dataframe in long format
        cont_df (pd.DataFrame): Contaminants dataframe in long format

    Returns:
        pd.DataFrame: General dataset with all the information
    """
    df = pd.merge(meteo_df, cont_df, how='inner', on='date')

    return df


def diagnose_missing(general_meteo: pd.DataFrame, general_cont: pd.DataFrame) -> pd.DataFrame:
    """Generate a report of the percentage of missing values in the datasets.

    Args:
        general_meteo (pd.DataFrame): Meteorology dataset in long format
        general_cont (pd.DataFrame): Contaminants dataset in long format

    Returns:
        pd.DataFrame: Report of the percentage of missing values in the datasets
    """
    missing_vals_report = pd.DataFrame(index=list(
        locations.keys()), columns=meteo_params + cont_params)

    for station in locations.keys():
        meteo_df = clean_data(general_meteo, station)
        cont_df = clean_data(general_cont, station)

        meteo_num_cols = meteo_df.columns[~meteo_df.columns.str.contains('_b')]
        meteo_num_cols = meteo_num_cols.drop('date')

        cont_num_cols = cont_df.columns[~cont_df.columns.str.contains('_b')]
        cont_num_cols = cont_num_cols.drop('date')

        missing_vals_report.loc[station, meteo_params] = np.divide(
            meteo_df[meteo_num_cols].isna().sum().values, meteo_df.shape[0])
        missing_vals_report.loc[station, cont_params] = np.divide(
            cont_df[cont_num_cols].isna().sum().values, cont_df.shape[0])

    missing_vals_report.reset_index(inplace=True)
    missing_vals_report.rename(columns={'index': 'station'}, inplace=True)

    missing_vals_report = missing_vals_report.melt(id_vars='station',
                                                   value_vars=meteo_params + cont_params,
                                                   var_name='parameter',
                                                   value_name='missing_values')

    # Multiply by 100 to get percentage
    missing_vals_report.missing_values = missing_vals_report.missing_values * 100

    return missing_vals_report


def main():
    """Main function to be executed when the script is run.
    """
    print('Loading data...')
    df_cont = pd.read_csv(
        '../../data/raw/SD_TecMTY_contaminantes_2021_2022.csv')
    df_meteo = pd.read_csv(
        '../../data/raw/SD_TecMTY_meteorologia_2021_2022.csv')

    big_cont = melt_data(df_cont)
    big_meteo = melt_data(df_meteo)

    save_data(big_cont, 'contaminants')
    save_data(big_meteo, 'meteorology')


main()
