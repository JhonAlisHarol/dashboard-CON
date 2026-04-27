import streamlit as st
import pandas as pd
import plotly.express as px
import time

# 1. Configuración de la interfaz
st.set_page_config(page_title="Dashboard Operativo Panamá", layout="wide")

# URL del CSV de Google Sheets
CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQzIFyCT2C22Hlrz80szN7J2mEfA8N1R7hiAmFAUXaoorwDTOeWNh-ktv__d0vIBS-AQcuV5ws3ZU4C/pub?gid=972728265&single=true&output=csv"

# Coordenadas Zonas Policiales para el mapa
COORD_PANAMA = {
    "Z P - COLÓN": [9.34, -79.89], "Z P - CHIRIQUÍ": [8.43, -82.43],
    "Z P - PANAMÁ OESTE": [8.88, -79.72], "Z P - SAN MIGUELITO": [9.03, -79.47],
    "Z P - ARRAIJÁN": [8.94, -79.65], "Z P - NORTE": [9.15, -79.50],
    "Z P - CANAL": [8.98, -79.55], "Z P - PACORA": [9.08, -79.28],
    "Z P - COCLÉ": [8.43, -80.35], "Z P - LOS SANTOS": [7.78, -80.25],
    "Z P - VERAGUAS": [8.10, -80.96], "Z P - HERRERA": [7.95, -80.63],
    "Z P - BOCAS DEL TORO": [9.33, -82.25], "Z P - CHORRERA": [8.88, -79.75]
}

@st.cache_data(ttl=5)
def cargar_todo():
    try:
        # Carga del archivo con un parámetro de tiempo para refrescar
        df_raw = pd.read_csv(f"{CSV_URL}&t={time.time()}", header=None).fillna(0)
        
        def buscar_v(label):
            try:
                mask = df_raw.apply(lambda x: x.astype(str).str.contains(label, case=False, na=False))
                r, c = mask.values.nonzero()
                if len(r) > 0:
                    val = pd.to_numeric(df_raw.iloc[r[0], c[0] + 1], errors='coerce')
                    return val if pd.notnull(val) else 0
            except: return 0
            return 0

        # --- Bloque 1: Pasteles ---
        df_p1 = pd.DataFrame({
            'Métrica': ["SEGURIDAD VIAL", "CAPTURAS", "RECUPERACIONES", "EMERGENCIAS"],
            'Cantidad': [buscar_v("SEGURIDAD VIAL"), buscar_v("CAPTURAS"), buscar_v("RECUPERACIONES"), buscar_v("EMERGENCIAS")]
        })
        
        df_p2 = pd.DataFrame({
            'Fuente': ["Video Vigilancia", "CLL-104", "Otras Fuentes", "Enlace SENAFRONT"],
            'Cantidad': [buscar_v("Video Vigilancia"), buscar_v("CLL-104"), buscar_v("Otras Fuentes"), buscar_v("Enlace SENAFRONT")]
        })

        # --- Bloque 2: Mapa y Ranking ---
        lista_z = []
        for nombre in COORD_PANAMA.keys():
            v = buscar_v(nombre)
            if v > 0:
                lista_z.append({'ZONA': nombre, 'TOTAL': v, 'lat': COORD_PANAMA[nombre][0], 'lon': COORD_PANAMA[nombre][1]})
        
        df_zonas = pd.DataFrame(lista_z)
        if not df_zonas.empty:
            df_zonas.columns = ['ZONA', 'TOTAL', 'lat', 'lon']

        # --- Bloque 3: Tabla Detallada (MODIFICADO PARA LOS 151 SUBTIPOS) ---
        try:
            # Buscamos donde empieza la tabla de subtipos
            idx = df_raw[df_raw.iloc[:, 1].astype(str).str.contains("S-01|APOYO AL CIUDADANO", case=False, na=False)].index[0]
            # CAMBIO: Ahora toma 160 filas para asegurar los 151 subtipos
            df_s = df_raw.iloc[idx:idx+160, [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]].copy()
            df_s.columns = ['SUBTIPO', 'CON', 'CORCOL', 'COMCH', 'COMAR', 'COMDA', 'COMCHEP', 'CEVIBO', 'COMSAM', 'TOTAL']
            
            # Limpieza de datos
            for col in df_s.columns[1:]:
                df_s[col] = pd.to_numeric(df_s[col], errors='coerce').fillna(0)
            
            # Filtrar filas vacías o con ceros en el nombre del subtipo
            df_s = df_s[df_s['SUBTIPO'] != 0]
        except:
            df_s = pd.DataFrame()

        return df_zonas, df_s, df_p1, df_p2
    except:
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

# Cargar los datos
df_z, df_s, df_p1, df_p2 = cargar_todo()

# --- INTERFAZ ---
st.title("📊 Control Integral de Incidentes - Panamá")

# Fila 1: Pasteles
col1, col2 = st.columns(2)
with col1:
    if not df_p1.empty and df_p1['Cantidad'].sum() > 0:
        st.plotly_chart(px.pie(df_p1, values='Cantidad', names='Métrica', title="Gestión de Análisis", hole=0.4, template="plotly_dark"), use_container_width=True)
with col2:
    if not df_p2.empty and df_p2['Cantidad'].sum() > 0:
        st.plotly_chart(px.pie(df_p2, values='Cantidad', names='Fuente', title="Fuentes de Entrada", hole=0.4, template="plotly_dark"), use_container_width=True)

# Fila 2: Mapa y Ranking
st.markdown("---")
c_map, c_rank = st.columns([2, 1])

with c_map:
    st.subheader("📍 Mapa de Calor (Incidentes)")
    if not df_z.empty and 'TOTAL' in df_z.columns:
        fig = px.density_mapbox(df_z, lat='lat', lon='lon', z='TOTAL', radius=35,
                                center=dict(lat=8.6, lon=-79.8), zoom=6.2,
                                mapbox_style="carto-darkmatter")
        fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0}, height=450)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Esperando datos válidos para generar el mapa...")

with c_rank:
    st.subheader("🏆 Ranking Z.P.")
    if not df_z.empty:
        st.dataframe(df_z.sort_values('TOTAL', ascending=False)[['ZONA', 'TOTAL']], hide_index=True, use_container_width=True, height=400)

# Fila 3: Tabla (MODIFICADO: ALTURA FIJA Y SCROLL)
st.markdown("---")
st.subheader("📋 Detalle General de Subtipos")
if not df_s.empty:
    # height=600 permite ver los primeros 20 y activar la barra desplazadora
    st.dataframe(df_s, use_container_width=True, hide_index=True, height=600)

# Refresco
st.components.v1.html("<script>setTimeout(function(){window.location.reload();}, 120000);</script>", height=0)