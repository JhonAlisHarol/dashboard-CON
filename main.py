import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, time

# 1. CONFIGURACIÓN DEL DASHBOARD
st.set_page_config(page_title="S-Portal Hexagon | Full Command Center", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #0a0e17; }
    .stMetric {
        background: rgba(255, 255, 255, 0.05) !important;
        backdrop-filter: blur(10px);
        border: 1px solid rgba(0, 104, 201, 0.3) !important;
        border-radius: 12px !important;
        padding: 15px !important;
    }
    .floating-metric {
        background: rgba(10, 14, 23, 0.9);
        border: 1px solid #00ebff;
        border-radius: 8px;
        padding: 10px;
        position: relative;
        z-index: 100;
        width: fit-content;
        margin-bottom: -65px;
        margin-left: 15px;
        box-shadow: 0px 4px 15px rgba(0,0,0,0.5);
    }
    h1, h2, h3, span, p, label { color: #ffffff !important; }
    </style>
    """, unsafe_allow_html=True)

# 2. CARGA DE DATOS
URL_CSV = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQzIFyCT2C22Hlrz80szN7J2mEfA8N1R7hiAmFAUXaoorwDTOeWNh-ktv__d0vIBS-AQcuV5ws3ZU4C/pub?gid=229458966&single=true&output=csv"

@st.cache_data(ttl=60)
def load_full_data():
    try:
        df = pd.read_csv(URL_CSV)
        df.columns = df.columns.str.strip()
        
        # Procesamiento de Fechas (Formato Día/Mes/Año)
        if 'FECHA' in df.columns:
            df['FECHA_DT'] = pd.to_datetime(df['FECHA'], dayfirst=True, errors='coerce').dt.date
            df = df.dropna(subset=['FECHA_DT'])
        
        # Procesamiento de Horas
        if 'HORA' in df.columns:
            # Extraemos la hora numérica (0-23) para el filtrado rápido
            df['HORA_NUM'] = pd.to_datetime(df['HORA'], errors='coerce').dt.hour
            df = df.dropna(subset=['HORA_NUM'])
        else:
            df['HORA_NUM'] = 0

        def to_minutes(val):
            try:
                if pd.isna(val) or str(val).strip() in ['', '0:00']: return 0.0
                parts = str(val).split(':')
                return float(int(parts[0]) * 60 + int(parts[1]))
            except: return 0.0

        df['V_DESPACHO'] = df['VARIANZA DE DESPACHO'].apply(to_minutes)
        df['V_ATENCION'] = df['VARIANZA DE LA ATENCION'].apply(to_minutes)
        col_cierre = 'VARIANZA DEL CIERRE' if 'VARIANZA DEL CIERRE' in df.columns else 'VARIANZA DE CIERRE'
        df['V_CIERRE'] = df[col_cierre].apply(to_minutes)
        
        cols_pos = ['RESULTADO POSITIVO 1', 'RESULTADO POSITIVO 2', 'RESULTADO POSITIVO 3', 
                    'RESULTADO POSITIVO 4', 'RESULTADO POSITIVO 5', 'RESULTADO POSITIVO 6']
        df['Total_Positivos_Fila'] = df[cols_pos].notna().sum(axis=1)
        
        if 'CENTRO' in df.columns:
            df['CENTRO'] = df['CENTRO'].astype(str).str.replace('CONTRA', 'CON').str.strip()
            
        return df[df['Total_Positivos_Fila'] > 0].copy()
    except: return None

df_raw = load_full_data()

if df_raw is not None:
    # --- BARRA LATERAL: FILTROS TIPO "DESDE - HASTA" ---
    st.sidebar.header("🔎 Filtros de Periodo")
    
    # Filtro de Fechas
    min_date = df_raw['FECHA_DT'].min()
    max_date = df_raw['FECHA_DT'].max()
    
    st.sidebar.subheader("📅 Fechas")
    f_col1, f_col2 = st.sidebar.columns(2)
    with f_col1:
        fecha_inicio = st.date_input("Desde:", value=min_date, key="f_ini")
    with f_col2:
        fecha_fin = st.date_input("Hasta:", value=max_date, key="f_fin")

    st.sidebar.markdown("---")
    
    # Filtro de Horas (Similar a la fecha)
    st.sidebar.subheader("⏰ Horas")
    h_col1, h_col2 = st.sidebar.columns(2)
    
    # Generamos lista de horas 00 a 23
    lista_horas = [i for i in range(24)]
    
    with h_col1:
        hora_inicio = st.selectbox("Hora Inicio:", lista_horas, index=0, format_func=lambda x: f"{x:02d}:00")
    with h_col2:
        hora_fin = st.selectbox("Hora Fin:", lista_horas, index=23, format_func=lambda x: f"{x:02d}:59")

    # Filtrado dinámico (Fecha + Hora)
    df = df_raw[
        (df_raw['FECHA_DT'] >= fecha_inicio) & 
        (df_raw['FECHA_DT'] <= fecha_fin) &
        (df_raw['HORA_NUM'] >= hora_inicio) &
        (df_raw['HORA_NUM'] <= hora_fin)
    ].copy()

    # --- TÍTULO ---
    st.title("🛡️ Hexágono S-Portal | Centro de Mando HD")
    st.info(f"Filtro aplicado: **{fecha_inicio.strftime('%d/%m/%Y')}** ({hora_inicio:02d}:00) hasta **{fecha_fin.strftime('%d/%m/%Y')}** ({hora_fin:02d}:59)")

    if not df.empty:
        # --- MÉTRICAS ---
        total_eventos_con_pos = len(df)
        total_positivos_suma = int(df['Total_Positivos_Fila'].sum())

        m1, m2, m3, m4, m5 = st.columns(5)
        m1.metric("📊 EVENTOS POSITIVOS", f"{total_eventos_con_pos:,}")
        m2.metric("✅ TOTAL POSITIVOS", f"{total_positivos_suma:,}")
        m3.metric("⏱️ VAR. DESPACHO", f"{df['V_DESPACHO'].mean():.1f} min")
        m4.metric("🤝 VAR. ATENCIÓN", f"{df['V_ATENCION'].mean():.1f} min")
        m5.metric("🔐 VAR. CIERRE", f"{df['V_CIERRE'].mean():.1f} min")

        st.markdown("---")

        # --- MAPA ---
        st.subheader("📍 Mapa de Calor Provincial")
        prov_stats = df.groupby('PROVINCIA')['Total_Positivos_Fila'].sum().reset_index()
        coords = {'Panamá': [8.98, -79.52], 'Chiriquí': [8.43, -82.43], 'Colón': [9.35, -79.90],
                  'Panamá Oeste': [8.88, -79.78], 'Coclé': [8.51, -80.35], 'Veraguas': [8.10, -80.97],
                  'Los Santos': [7.93, -80.48], 'Herrera': [7.96, -80.70], 'Darién': [8.40, -77.91],
                  'Bocas del Toro': [9.33, -82.24]}
        prov_stats['lat'] = prov_stats['PROVINCIA'].map(lambda x: coords.get(x, [8.5, -80.0])[0])
        prov_stats['lon'] = prov_stats['PROVINCIA'].map(lambda x: coords.get(x, [8.5, -80.0])[1])

        c_map, c_rank = st.columns([2, 1])
        with c_map:
            st.markdown(f"""<div class="floating-metric"><small style="color: #94a3b8; text-transform: uppercase; font-size: 10px;">Filtro Actual</small><br>
                <span style="font-size: 22px; font-weight: bold; color: #00ebff;">{total_positivos_suma:,}</span></div>""", unsafe_allow_html=True)
            fig_map = px.density_mapbox(prov_stats, lat='lat', lon='lon', z='Total_Positivos_Fila', radius=40,
                center=dict(lat=8.5, lon=-80.0), zoom=6, mapbox_style="carto-darkmatter", color_continuous_scale="Blues")
            fig_map.update_layout(margin={"r":0,"t":0,"l":0,"b":0}, paper_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig_map, use_container_width=True)
        
        with c_rank:
            st.write("**Ranking Provincial**")
            st.dataframe(prov_stats[['PROVINCIA', 'Total_Positivos_Fila']].sort_values('Total_Positivos_Fila', ascending=False), hide_index=True, use_container_width=True)

        st.markdown("---")

        # --- PASTELES ---
        st.subheader("🎯 Análisis de Distribución")
        col_p1, col_p2 = st.columns(2)
        with col_p1:
            st.write("**📱 Positivos por Canal de Entrada**")
            canal_data = df.groupby('CANAL DE ENTRADA')['Total_Positivos_Fila'].sum().sort_values(ascending=False).reset_index()
            fig_canal = px.pie(canal_data, names='CANAL DE ENTRADA', values='Total_Positivos_Fila', hole=0.6, color_discrete_sequence=px.colors.sequential.Blues_r)
            st.plotly_chart(fig_canal, use_container_width=True)
        with col_p2:
            st.write("**🏢 Positivos por Centro**")
            centro_data = df.groupby('CENTRO')['Total_Positivos_Fila'].sum().sort_values(ascending=False).reset_index()
            fig_centro = px.pie(centro_data, names='CENTRO', values='Total_Positivos_Fila', hole=0.6, color_discrete_sequence=px.colors.sequential.Tealgrn)
            st.plotly_chart(fig_centro, use_container_width=True)

        st.markdown("---")

        # --- TABLA TÁCTICA ---
        st.subheader("📋 Detalle de Positivos por Centro (Filtrado)")
        cols_pos_list = ['RESULTADO POSITIVO 1', 'RESULTADO POSITIVO 2', 'RESULTADO POSITIVO 3', 
                        'RESULTADO POSITIVO 4', 'RESULTADO POSITIVO 5', 'RESULTADO POSITIVO 6']
        df_long = pd.melt(df, id_vars=['CENTRO'], value_vars=cols_pos_list, value_name='Tipo').dropna()
        
        if not df_long.empty:
            tabla_final = df_long.groupby(['Tipo', 'CENTRO']).size().unstack(fill_value=0)
            orden_centros = tabla_final.sum(axis=0).sort_values(ascending=False).index
            tabla_final = tabla_final[orden_centros]
            tabla_final['TOTAL IMPACTO'] = tabla_final.sum(axis=1)
            tabla_final = tabla_final.sort_values('TOTAL IMPACTO', ascending=False)
            
            sumatoria_centros = tabla_final.sum(axis=0).to_frame().T
            sumatoria_centros.index = ['TOTAL CENTRO']
            tabla_completa = pd.concat([tabla_final, sumatoria_centros])
            tabla_completa.iloc[-1, -1] = total_positivos_suma
            st.dataframe(tabla_completa, use_container_width=True, height=400)
        else:
            st.warning("No hay detalles disponibles para este horario.")
    else:
        st.warning("No se encontraron eventos en el rango de fecha y hora seleccionado.")
else:
    st.error("No se pudo sincronizar con la base de datos.")
