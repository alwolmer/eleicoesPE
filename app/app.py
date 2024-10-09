import os
import streamlit as st
import pandas as pd
import geopandas as gpd
import numpy as np
import folium
import branca.colormap as cm
from streamlit_folium import st_folium
from PIL import Image
import requests

# Fetching the 'DEV' environment variable (returns None if not found)
prod_mode = os.getenv('PROD', '0')  # Default to '0' if not set

selected_uf = st.sidebar.selectbox('Escolha o estado', ['PE'])
uf = selected_uf

# Convert the value to integer or boolean as needed
prod = int(prod_mode) == 1

if prod:
    data_path = 'https://raw.githubusercontent.com/alwolmer/eleicoesPE/refs/heads/main/data_pipeline/render/'
else:
    data_path = os.path.abspath(os.path.join('.', 'data_pipeline', 'render'))

@st.cache_data
def load_data(uf):
    if prod:
        cand_UF_abrev = pd.read_csv(f'{data_path}cand_abrev_{uf}_2022.csv')
        voto_mun_valido = pd.read_csv(f'{data_path}voto_mun_valido_{uf}_2022.csv')
        voto_mun_valido_total = pd.read_csv(f'{data_path}voto_mun_valido_{uf}_total_2022.csv')
        malha_UF_mun = gpd.read_file(f'{data_path}malha_{uf}_mun.geojson')
    else:
        cand_UF_abrev = pd.read_csv(os.path.join(data_path, f'cand_abrev_{uf}_2022.csv'))
        voto_mun_valido = pd.read_csv(os.path.join(data_path, f'voto_mun_valido_{uf}_2022.csv'))
        voto_mun_valido_total = pd.read_csv(os.path.join(data_path, f'voto_mun_valido_{uf}_total_2022.csv'))
        malha_UF_mun = gpd.read_file(os.path.join(data_path, f'malha_{uf}_mun.geojson'))
    
    voto_mun_valido['CD_MUN'] = voto_mun_valido['CD_MUN'].astype('Int64')
    voto_mun_valido_total['CD_MUN'] = voto_mun_valido_total['CD_MUN'].astype('Int64')
    malha_UF_mun['CD_MUN'] = malha_UF_mun['CD_MUN'].astype('Int64')
    
    return cand_UF_abrev, voto_mun_valido, voto_mun_valido_total, malha_UF_mun

cand_UF_abrev, voto_mun_valido, voto_mun_valido_total, malha_UF_mun = load_data(uf)

# if dev:
#     preloaded_images = preload_images(f'{data_path}foto_cand2022_PE_div')
# else:
#     preloaded_images = preload_images()

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
cand_selected_cargo_turno = cand_UF_abrev[(cand_UF_abrev['CD_CARGO'] == cargo_turno_key[selected_cargo_turno][0]) & (cand_UF_abrev['NR_TURNO'] == cargo_turno_key[selected_cargo_turno][1]) & ((cand_UF_abrev['CD_SITUACAO_CANDIDATURA'] == 12))] # 12 means able candidate, who actually did run

partido_list = ['TODOS'] + sorted(cand_selected_cargo_turno['SG_PARTIDO'].unique().tolist())
selected_partido = st.sidebar.selectbox('Escolha o partido', partido_list)

if 'TODOS' == selected_partido:
    candidates = cand_selected_cargo_turno['NM_URNA_CANDIDATO'].sort_values()
else:
    candidates = cand_selected_cargo_turno[cand_selected_cargo_turno['SG_PARTIDO'] == selected_partido]['NM_URNA_CANDIDATO'].sort_values()
selected_candidate = st.sidebar.selectbox('Escolha o candidato', candidates)

cand_details = cand_UF_abrev[(cand_UF_abrev['CD_CARGO'] == cargo_turno_key[selected_cargo_turno][0]) & (cand_UF_abrev['NR_TURNO'] == cargo_turno_key[selected_cargo_turno][1]) & (cand_UF_abrev['NM_URNA_CANDIDATO'] == selected_candidate)]

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
        if prod:
            image_url = f"https://raw.githubusercontent.com/alwolmer/eleicoesPE/main/data_pipeline/render/fotos{uf}2022/{sq_cand}.jpg"
            st.image(Image.open(requests.get(image_url, stream=True).raw))
        else:
            image_path = os.path.join(data_path, f'fotos{uf}2022/{sq_cand}.jpg')
            st.image(image_path)
    except:
        st.write(f"Não foi possível encontar imagem para o candidato {sq_cand}")
            

@st.cache_data
def generate_voto_display(voto_mun_valido, voto_mun_valido_total, _malha_UF_mun, turno_cand, cargo_cand, numero_cand):
    voto_select = voto_mun_valido[(voto_mun_valido['NR_TURNO'] == turno_cand) & 
                                  (voto_mun_valido['CD_CARGO'] == cargo_cand) & 
                                  (voto_mun_valido['NR_VOTAVEL'] == numero_cand)].copy()

    voto_cand_total = voto_select['QT_VOTOS'].sum()

    voto_select = voto_select.merge(
        voto_mun_valido_total[(voto_mun_valido_total['NR_TURNO'] == turno_cand) & 
                       (voto_mun_valido_total['CD_CARGO'] == cargo_cand)][['CD_MUN', 'QT_VOTOS']], 
        on='CD_MUN', 
        how='left', 
        suffixes=('_CAND_LOCAL', '_VALIDOS_LOCAL')
    ).fillna(0)

    # Calculate percentages
    voto_select['FREQ_LOCAL'] = np.round(voto_select['QT_VOTOS_CAND_LOCAL'] / voto_select['QT_VOTOS_VALIDOS_LOCAL'] * 100, 2)
    voto_select['INCID_LOCAL'] = np.round(voto_select['QT_VOTOS_CAND_LOCAL'] / voto_cand_total * 100, 2)

    # Merge with GeoDataFrame
    voto_display = gpd.GeoDataFrame(voto_select.merge(_malha_UF_mun, on='CD_MUN', how='outer').fillna(0))
    
    return voto_display, voto_cand_total

# Generate and cache voto_display
voto_display, voto_cand_total = generate_voto_display(voto_mun_valido, voto_mun_valido_total, malha_UF_mun, turno_cand, cargo_cand, numero_cand)

c2 = st.container()

c2.write(f"Número total de votos: {voto_cand_total}")

def style_function(feature, cmap, column):
    return {
        'fillColor': cmap(feature['properties'][column]),
        'fillOpacity': 0.9,
        'color': 'black',
        'weight': 0.7,
        'opacity': 0.5,
    }

def create_tooltip():
    return folium.GeoJsonTooltip(
        fields=['NM_MUN', 'QT_VOTOS_CAND_LOCAL', 'FREQ_LOCAL', 'INCID_LOCAL'],
        aliases=['Município', 'N. votos', '% no Município', '% dos votos cand.']
    )

from functools import partial

# Generate the maps
def generate_choromap(_voto_display, column):
    cmap = cm.linear.YlOrRd_04.scale(_voto_display[column].min(), _voto_display[column].max())
    cmap.caption = '% dos votos no município' if column == 'FREQ_LOCAL' else '% dos votos da candidatura'

    # Frequency Map
    choromap = folium.Map([-8.319639, -37.635917], zoom_start=7.3)
    
    # Add GeoJson to the map using the regular function instead of lambda
    style_func = partial(style_function, cmap=cmap, column=column)
    folium.GeoJson(
        _voto_display,
        # style_function=lambda feature: style_function(feature, cmap, column),  # Apply styling per feature
        style_function=style_func,
        tooltip=create_tooltip()
    ).add_to(choromap)
    
    cmap.add_to(choromap)
    
    return choromap

freq_map = generate_choromap(voto_display, 'FREQ_LOCAL')
incid_map = generate_choromap(voto_display, 'INCID_LOCAL')

with st.container():
    st.write("Frequência")
    st_folium(freq_map, use_container_width=True, height=500, returned_objects=[])

with st.container():
    st.write("Incidência")
    st_folium(incid_map, use_container_width=True, height=500, returned_objects=[])