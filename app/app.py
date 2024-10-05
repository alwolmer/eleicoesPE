import os
import streamlit as st
import pandas as pd
import geopandas as gpd
import folium
import branca.colormap as cm
from streamlit_folium import st_folium


data_path = os.path.abspath('./data_pipeline/render')

# print(pd.read_csv(f'{data_path}\cand_2022_PE_abrev.csv'))

@st.cache_data
def load_data():
    cand_PE_abrev = pd.read_csv(fr'{data_path}\cand_2022_PE_abrev.csv')  # Replace with your data source
    # malha_PE_abrev = gpd.read_file(f'{data_path}\malha_PE_abrev.geojson')  # GeoJSON or shapefile with municipios
    return cand_PE_abrev

def load_picture():
    pass

cand_PE_abrev = load_data()

cargo_turno_key = {
    'GOVERNADOR - 1 TURNO': (3, 1),
    'GOVERNADOR - 2 TURNO': (3, 2),
    'SENADOR': (5, 1),
    'DEPUTADO FEDERAL': (6, 1),
    'DEPUTADO ESTADUAL': (7, 1)
}

sit_elec_key = {
    5: "SUPLENTE",
    4: "NÃO ELEITO",
    2: "ELEITO",
    3: "ELEITO",
    1: "ELEITO",
    6: "2o TURNO"
}

selected_cargo_turno = st.sidebar.selectbox('Escolha o cargo', cargo_turno_key.keys())
cand_selected_cargo_turno = cand_PE_abrev[(cand_PE_abrev['CD_CARGO'] == cargo_turno_key[selected_cargo_turno][0]) & (cand_PE_abrev['NR_TURNO'] == cargo_turno_key[selected_cargo_turno][1]) & ((cand_PE_abrev['CD_SITUACAO_CANDIDATURA'] == 12))] # 12 means able candidate, who actually did run

partido_list = ['TODOS'] + sorted(cand_selected_cargo_turno['SG_PARTIDO'].unique().tolist())
selected_partido = st.sidebar.selectbox('Escolha o partido', partido_list)

if 'TODOS' == selected_partido:
    candidates = cand_selected_cargo_turno['NM_URNA_CANDIDATO'].sort_values()
else:
    candidates = cand_selected_cargo_turno[cand_selected_cargo_turno['SG_PARTIDO'] == selected_partido]['NM_URNA_CANDIDATO'].sort_values()
selected_candidate = st.sidebar.selectbox('Escolha o candidato', candidates)

cand_details = cand_PE_abrev[(cand_PE_abrev['CD_CARGO'] == cargo_turno_key[selected_cargo_turno][0]) & (cand_PE_abrev['NR_TURNO'] == cargo_turno_key[selected_cargo_turno][1]) & (cand_PE_abrev['NM_URNA_CANDIDATO'] == selected_candidate)]

c1 = st.container()

col1, col2 = c1.columns([2, 1])  # Adjust the numbers to change the width

with col1:
    st.write(f"Nome de urna: {cand_details['NM_URNA_CANDIDATO'].values[0]}")
    st.write(f"Nome completo: {cand_details['NM_CANDIDATO'].values[0]}")
    st.write(f"Partido: {cand_details['SG_PARTIDO'].values[0]}")
    st.write(f"Número eleitoral: {cand_details['NR_CANDIDATO'].values[0]}")
    st.write(f"Situação: {sit_elec_key[cand_details['CD_SIT_TOT_TURNO'].values[0]]}")

# Add image to the second column
with col2:
    try:
        st.image(fr"{data_path}\foto_cand2022_PE_div\FPE{cand_details['SQ_CANDIDATO'].values[0]}_div.jpg")
    except:
        st.image(fr"{data_path}\foto_cand2022_PE_div\FPE{cand_details['SQ_CANDIDATO'].values[0]}_div.jpeg")