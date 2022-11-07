import streamlit as st
import pandas as pd
import altair as alt
from utils import clean_data, metric_calculator, melt_data, create_time_series
from utils import locations, cont_params, cont_units, meteo_params, meteo_units
import requests
from streamlit_lottie import st_lottie
from PIL import Image


# DATA ASSETS
# ------------------------------------------------------------------
df_cont = pd.read_csv('data/SD_TecMTY_contaminantes_2021_2022.csv')
df_meteo = pd.read_csv('data/SD_TecMTY_meteorologia_2021_2022.csv')

df_cont.drop(columns=['Unnamed: 0'], inplace=True)
df_meteo.drop(columns=['Unnamed: 0'], inplace=True)

big_cont = melt_data(df_cont)
big_meteo = melt_data(df_meteo)
# ------------------------------------------------------------------

# IMAGE ASSETS
# ------------------------------------------------------------------
def load_lottieurl(url):
    """Load a Lottie animation from a URL."""
    r = requests.get(url)

    if r.status_code != 200:
        return None

    return r.json()
home_anim = load_lottieurl("https://assets10.lottiefiles.com/packages/lf20_EyJRUV.json")



def main():
    st.set_page_config(layout="wide")
    st.title("Análisis de calidad el aire en ZMM de Monterrey")
    st.write("Sistema Integral de Monitoreo de la Calidad del Aire | Tec de Monterrey")

    # st.sidebar.header("User Input Parameters")

    tabs = ["Home", "Análisis temporal", "Acerca de"]
    tabs = st.tabs(tabs)

    with tabs[0]:
        st.header("Home")

        with st.container():
            st.write('---')
            st.header('Calidad del Aire')
            col1, col2 = st.columns([1.5,2])
            with col1:
                st.write(
                    '''
                    Las actividades diarias de los ciudadanos generan una gran cantidad de contaminantes que modifican la composición natural
                    del aire que respiramos. Estos contaminantes pueden ser nocivos para la salud humana y el medio ambiente y vienen de diversas
                    fuentes, como:
                    - Tráfico
                    - Industria
                    - Agricultura
                    - Quema de combustibles fósiles.
                    '''
                )
            with col2:
                st_lottie(home_anim, height=300)

            num_input = st.number_input(
                label="Number of days to calculate metrics",
                min_value=1,
                max_value=365,
                value=7,
                step=1,
                format="%i",
            )
            mean_scores = metric_calculator(big_cont, num_input, 'contaminant')

            cols = st.columns(len(cont_params))

            for idx, param in enumerate(cont_params):
                mean = mean_scores.loc[param]['mean']
                diff = mean_scores.loc[param]['diff']
                cols[idx].metric(label=f'{param} [{cont_units[param]}]',
                                value=f'{mean:.2f}',
                                delta=f'{diff:.2f}',
                                delta_color="inverse")

    # Análisis temporal
    with tabs[1]:
        st.header("Series de tiempo")
        st.write("Selecciona la estación y el parámetro que deseas visualizar")
        # db_conv = {'Contaminantes': 'cont', 'Meteorología': 'meteo'}
        param_conv = {'Contaminantes': cont_params, 'Meteorológicos': meteo_params}

        cols = st.columns(2)
        with cols[0]:
            db_type = st.radio("Select the type of data", ('Contaminantes', 'Meteorológicos'))
            time_window = st.selectbox("Time window", ('D', 'W', 'M', 'Y'))
            # Map db_type to either 'cont' or 'meteo'

        with cols[1]:
            location = st.selectbox("Location", list(locations.keys()))
            params = param_conv[db_type]
            parameter = st.selectbox("Parameter", params)

        if db_type == 'Contaminantes':
            df = clean_data(big_cont, location)
            type = 'cont'
        elif db_type == 'Meteorológicos':
            df = clean_data(big_meteo, location)
            type = 'meteo'

        st.write("Time series of pollutant concentration")
        chart = create_time_series(df, location, parameter, time_window, type)
        st.altair_chart(chart, use_container_width=True)

    with tabs[2]:
        st.header("About")

        # Developers
        with st.container():
            st.write('---')
            st.header('Equipo')

            with st.container():

                col1, col2 = st.columns([1,1])
                with col1:
                    st.markdown(
                        """
                        #### Juan Pablo Echeagaray González
                        - Email: pablowechg@gmail.com
                        - LinkedIn: [Juan Echeagaray](https://www.linkedin.com/in/juan-echeagaray-b2a5661a3/)
                        - GitHub: [JuanEcheagaray75](https://github.com/JuanEcheagaray75)
                        """)

                with col2:
                    prof_pic = Image.open('assets/dev_pics/jpeg-pic.jpg')
                    st.image(prof_pic, width=200)

            with st.container():
                st.markdown(
                    """
                    #### Verónica Victoria García De la Fuente
                    """)

            with st.container():
                st.markdown(
                    """
                    #### Ricardo de Jesús Balam Ek
                    """)

            with st.container():
                st.markdown(
                    """
                    #### Emily Rebeca Méndez Cruz
                    """)

            with st.container():
                st.markdown(
                    """
                    #### Eugenio Santisteban Zolezzi
                    """)

if __name__ == "__main__":
    main()