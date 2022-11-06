import streamlit as st
import pandas as pd
import altair as alt


df_cont = pd.read_csv('data/SD_TecMTY_contaminantes_2021_2022.csv')
df_meteo = pd.read_csv('data/SD_TecMTY_meteorologia_2021_2022.csv')

locations = {
            "Guadalupe, La Pastora" : "SE",
            "San Nicolás de los Garzas, San Nicolás" : "NE",
            "Monterrey, Obispado" : "CE",
            "Monterrey, San Bernabé": "NO",
            "Santa Catarina, Santa Catarina": "SO",
            "García, García" : "NO2",
            "Escobedo, Escobedo": "NTE",
            "Apodaca, Apodaca" : "NE2",
            "Juárez, Juárez" : "SE2",
            "San Pedro Garza García, San Pedro": "SO2"
            }
pollutants = ["PM10", "PM2.5", "O3", "NO2", "SO2", "CO"]

meteo_parameters = {
    "Temperatura": "TOUT",
    "Humedad relativa": "RH",
    "Radiación Solar": "SR",
    "Precipitación": "RAINF",
    "Presión Atmosférica": "PRES",
    "Velocidad del viento": "WSR",
    "Dirección del viento": "WDR"
}

meteo_params = ['TOUT', 'RH', 'SR', 'RAINF', 'PRS', 'WSR', 'WDR']
cont_params = ['PM10', 'PM2.5', 'O3', 'NO2', 'SO2', 'CO']

def clean_data(station: str, dataframe: pd.DataFrame, type: str) -> pd.DataFrame:

    # Get value of key
    # Try and catch in case the station is not in the dictionary
    try:
        location = locations[station]
    except:
        raise ValueError('Station not found')

    # Columns
    dataframe.parameter = dataframe.parameter.str.strip()
    dataframe = pd.pivot(dataframe, index='date', columns=['parameter'], values=[location, f'{location}_b'])
    dataframe.columns = [f'{location}-' + col[1] if col[0] == location else f'{location}_b-' + col[1] for col in dataframe.columns]
    dataframe.reset_index(inplace=True)
    dataframe.date = pd.to_datetime(dataframe.date)

    if type == 'meteo':
        for param in meteo_params:
            dataframe[f'{location}-{param}'] = dataframe[f'{location}-{param}'].astype(float)

    elif type == 'cont':

        for param in cont_params:
            dataframe[f'{location}-{param}'] = pd.to_numeric(dataframe[f'{location}-{param}'], errors='coerce')

    else:
        raise ValueError('Type must be meteo or cont')

    return dataframe



def main():
    st.set_page_config(layout="wide")
    st.title("Análisis de calidad el aire en ZMM de Monterrey")
    st.write("Sistema Integral de Monitoreo de la Calidad del Aire | Tec de Monterrey")

    st.sidebar.header("User Input Parameters")

    tabs = ["Home", "Time Series", "About"]
    tabs = st.tabs(tabs)

    with tabs[0]:
        st.header("Home")

    with tabs[1]:
        st.header("Time Series")
        st.write("Select the location and the pollutant to see the time series")
        location = st.selectbox("Location", list(locations.keys()))
        pollutant = st.selectbox("Pollutant", pollutants)

        dfc = clean_data(location, df_cont, 'cont')

        st.write("Time series of pollutant concentration")
        alt.data_transformers.disable_max_rows()
        scales = alt.selection_interval(bind='scales')
        chart = alt.Chart(dfc).mark_line(width=40).encode(
            x='date',
            y=f'{locations[location]}-{pollutant}',
        ).properties(width=alt.Step(30)).add_selection(
            scales
        ).interactive()
        st.altair_chart(chart, use_container_width=True)


    with tabs[2]:
        st.header("About")
        st.write("En esta sección se muestra información sobre el proyecto.")


if __name__ == "__main__":
    main()