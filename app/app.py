import os
import streamlit as st
import pandas as pd
import geopandas as gpd
import numpy as np
import folium
import branca.colormap as cm
from streamlit_folium import st_folium


data_path = os.path.abspath('./data_pipeline/render')

# print(pd.read_csv(f'{data_path}\cand_2022_PE_abrev.csv'))

@st.cache_data
def load_data():
   
    cand_PE_abrev = pd.read_csv(fr'{data_path}\cand_2022_PE_abrev.csv')
    voto_PE_nominal = pd.read_csv(fr'{data_path}\votacao_mun_2022_PE_nominal.csv')
    voto_PE_valido = pd.read_csv(fr'{data_path}\votacao_mun_2022_PE_valido.csv')
    malha_PE_mun = gpd.read_file(f'{data_path}\malha_PE_mun.geojson')
    
    voto_PE_nominal['CD_MUN'] = voto_PE_nominal['CD_MUN'].astype('Int64')
    voto_PE_valido['CD_MUN'] = voto_PE_valido['CD_MUN'].astype('Int64')
    malha_PE_mun['CD_MUN'] = malha_PE_mun['CD_MUN'].astype('Int64')
    return cand_PE_abrev, voto_PE_nominal, voto_PE_valido, malha_PE_mun

cand_PE_abrev, voto_PE_nominal, voto_PE_valido, malha_PE_mun = load_data()

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

cargo_cand = cand_details['CD_CARGO'].values[0]
turno_cand = cand_details['NR_TURNO'].values[0]
nome_urna_cand = cand_details['NM_URNA_CANDIDATO'].values[0]
nome_completo_cand = cand_details['NM_CANDIDATO'].values[0]
partido_cand = cand_details['SG_PARTIDO'].values[0]
numero_cand = cand_details['NR_CANDIDATO'].values[0]
situacao_cand = cand_details['CD_SIT_TOT_TURNO'].values[0]
sq_cand = cand_details['SQ_CANDIDATO'].values[0]

with col1:
    st.write(f"Nome de urna: {nome_urna_cand}")
    st.write(f"Nome completo: {nome_completo_cand}")
    st.write(f"Partido: {partido_cand}")
    st.write(f"Número eleitoral: {numero_cand}")
    st.write(f"Situação: {sit_elec_key[situacao_cand]}")

# Add image to the second column
with col2:
    try:
        st.image(fr"{data_path}\foto_cand2022_PE_div\FPE{sq_cand}_div.jpg")
    except:
        st.image(fr"{data_path}\foto_cand2022_PE_div\FPE{sq_cand}_div.jpeg")


voto_select = voto_PE_nominal[(voto_PE_nominal['NR_TURNO'] == turno_cand) & (voto_PE_nominal['CD_CARGO'] == cargo_cand) & (voto_PE_nominal['NR_VOTAVEL'] == numero_cand)].copy()
voto_cand_total = voto_select['QT_VOTOS'].sum()
voto_select = voto_select.merge(voto_PE_valido[(voto_PE_valido['NR_TURNO'] == turno_cand) & (voto_PE_valido['CD_CARGO'] == cargo_cand)][['CD_MUN', 'QT_VOTOS']], on='CD_MUN', how='left', suffixes=('_CAND_LOCAL', '_VALIDOS_LOCAL')).fillna(0)
voto_select['FREQ_LOCAL'] = np.round(voto_select['QT_VOTOS_CAND_LOCAL'] / voto_select['QT_VOTOS_VALIDOS_LOCAL'] * 100, 2)
voto_select['INCID_LOCAL'] = np.round(voto_select['QT_VOTOS_CAND_LOCAL'] / voto_cand_total * 100, 2)

voto_display = gpd.GeoDataFrame(voto_select.merge(malha_PE_mun, on='CD_MUN', how='outer').fillna(0))

c2 = st.container()

c2.write(f"Número total de votos: {voto_cand_total}")

# Frequency of votes per location

cmap_freq = cm.linear.YlOrRd_04.scale(voto_display['FREQ_LOCAL'].min(), voto_display['FREQ_LOCAL'].max())
cmap_freq.caption = '% dos votos no município'

# Frequency Map
freq_map = folium.Map([-8.319639, -37.635917], zoom_start=7.3)
folium.GeoJson(voto_display,
                style_function=lambda feature: {
                    'fillColor': cmap_freq(feature['properties']['FREQ_LOCAL']),
                    'fillOpacity': 0.9,
                    'color': 'black',
                    'weight': 0.7,
                    'opacity': 0.5,
                },
                tooltip=folium.GeoJsonTooltip(
                    fields=['NM_MUN', 'QT_VOTOS_CAND_LOCAL', 'FREQ_LOCAL', 'INCID_LOCAL'],
                    aliases=['Município', 'N. votos', '% no Município', '% dos votos cand.']
                )
                ).add_to(freq_map)
cmap_freq.add_to(freq_map)

# Incidence of votes per location

# Incidence colormap
cmap_incid = cm.linear.YlOrRd_04.scale(voto_display['INCID_LOCAL'].min(), voto_display['INCID_LOCAL'].max())
cmap_incid.caption = '% dos votos da candidatura'

# Frequency Map
incid_map = folium.Map([-8.319639, -37.635917], zoom_start=7.3)
folium.GeoJson(voto_display,
                style_function=lambda feature: {
                    'fillColor': cmap_incid(feature['properties']['INCID_LOCAL']),
                    'fillOpacity': 0.9,
                    'color': 'black',
                    'weight': 0.7,
                    'opacity': 0.5,
                },
                tooltip=folium.GeoJsonTooltip(
                    fields=['NM_MUN', 'QT_VOTOS_CAND_LOCAL', 'FREQ_LOCAL', 'INCID_LOCAL'],
                    aliases=['Município', 'N. votos', '% no Município', '% dos votos cand.']
                )
                ).add_to(incid_map)
cmap_incid.add_to(incid_map)

with st.container():
    st.write("Frequência")
    st_folium(freq_map, width=700, height=500)

with st.container():
    st.write("Incidência")
    st_folium(incid_map, width=700, height=500)