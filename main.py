import streamlit as st
import pandas as pd
import plotly.express as px

# 1. CONFIGURACIÓN DEL DASHBOARD
st.set_page_config(page_title="S-Portal Hexagon | Full Command Center", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #0a0e17; }
    [data-testid="stMetric"] {
        background: rgba(255, 255, 255, 0.05) !important;
        backdrop-filter: blur(10px);
        border: 1px solid rgba(0, 104, 201, 0.3) !important;
        border-radius: 12px !important;
        padding: 15px !important;
    }
    .floating-metric {
        background: rgba(10, 14, 23, 0.8);
        border: 1px solid #0068c9;
        border-radius: 8px;
        padding: 10px;
        position: relative;
        z-index: 100;
        width: fit-content;
        margin-bottom: -65px;
        margin-left: 15px;
        box-shadow: 0px 4px 15px rgba(0,0,0,0.5);
    }
    h1, h2, h3, span, p { color: #ffffff !important; }
    </style>
    """, unsafe_allow_html=True)

# 2. CARGA Y PROCESAMIENTO DE DATOS
URL_CSV = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQzIFyCT2C22Hlrz80szN7J2mEfA8N1R7hiAmFAUXaoorwDTOeWNh-ktv__d0vIBS-AQcuV5ws3ZU4C/pub?gid=229458966&single=true&output=csv"

@st.cache_data(ttl=60)
def load_full_data():
    try:
        df = pd.read_csv(URL_CSV)
        df.columns = df.columns.str.strip()
        
        # Limpieza de tiempos
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
        
        # Cálculo de Positivos (Suma horizontal de las 6 columnas de resultados)
        cols_pos = ['RESULTADO POSITIVO 1', 'RESULTADO POSITIVO 2', 'RESULTADO POSITIVO 3', 
                    'RESULTADO POSITIVO 4', 'RESULTADO POSITIVO 5', 'RESULTADO POSITIVO 6']
        df['Total_Positivos_Fila'] = df[cols_pos].notna().sum(axis=1)
        
        # Corrección de nombres de centros según Ledger de correcciones
        if 'CENTRO' in df.columns:
            df['CENTRO'] = df['CENTRO'].astype(str).str.replace('CONTRA', 'CON').str.strip()
            
        return df
    except: return None

df = load_full_data()

if df is not None:
    # --- CÁLCULO DE MÉTRICAS UNIFICADAS ---
    total_positivos_global = int(df['Total_Positivos_Fila'].sum())
    # Consideramos "Eventos" solo aquellos que tuvieron al menos un resultado positivo
    df_pos = df[df['Total_Positivos_Fila'] > 0].copy()
    total_eventos_reales = len(df_pos) 

    st.title("🛡️ Hexágono S-Portal | Centro de Mando HD")
    
    # --- FILA DE MÉTRICAS SUPERIOR ---
    m1, m2, m3, m4, m5 = st.columns(5)
    # Ahora Eventos Totales refleja los casos con impacto
    m1.metric("📊 EVENTOS CON POSITIVO", f"{total_eventos_reales:,}")
    m2.metric("✅ TOTAL ACUMULADO", f"{total_positivos_global:,}")
    m3.metric("⏱️ VAR. DESPACHO", f"{df_pos['V_DESPACHO'].mean():.1f} min")
    m4.metric("🤝 VAR. ATENCIÓN", f"{df_pos['V_ATENCION'].mean():.1f} min")
    m5.metric("🔐 VAR. CIERRE", f"{df_pos['V_CIERRE'].mean():.1f} min")

    st.markdown("---")

    # --- SECCIÓN GEOGRÁFICA ---
    st.subheader("📍 Mapa de Calor Provincial (Impacto Total)")
    
    prov_stats = df_pos.groupby('PROVINCIA')['Total_Positivos_Fila'].sum().reset_index()
    coords = {
        'Panamá': [8.98, -79.52], 'Chiriquí': [8.43, -82.43], 'Colón': [9.35, -79.90],
        'Panamá Oeste': [8.88, -79.78], 'Coclé': [8.51, -80.35], 'Veraguas': [8.10, -80.97],
        'Los Santos': [7.93, -80.48], 'Herrera': [7.96, -80.70], 'Darién': [8.40, -77.91],
        'Bocas del Toro': [9.33, -82.24]
    }
    prov_stats['lat'] = prov_stats['PROVINCIA'].map(lambda x: coords.get(x, [8.5, -80.0])[0])
    prov_stats['lon'] = prov_stats['PROVINCIA'].map(lambda x: coords.get(x, [8.5, -80.0])[1])

    c_map, c_rank = st.columns([2.5, 1])
    
    with c_map:
        # Etiqueta flotante con la suma total de las provincias
        st.markdown(f"""
            <div class="floating-metric">
                <small style="color: #94a3b8; text-transform: uppercase; font-size: 10px;">Total Positivos Provincias</small><br>
                <span style="font-size: 22px; font-weight: bold; color: #00ebff;">{total_positivos_global:,}</span>
            </div>
        """, unsafe_allow_html=True)
        
        fig_map = px.density_mapbox(
            prov_stats, lat='lat', lon='lon', z='Total_Positivos_Fila', radius=45,
            center=dict(lat=8.5, lon=-80.0), zoom=6.5,
            mapbox_style="carto-darkmatter", color_continuous_scale="Blues"
        )
        fig_map.update_layout(margin={"r":0,"t":0,"l":0,"b":0}, paper_bgcolor='rgba(0,0,0,0)', showlegend=False)
        st.plotly_chart(fig_map, use_container_width=True)
    
    with c_rank:
        st.write("**Ranking de Impacto**")
        st.dataframe(prov_stats[['PROVINCIA', 'Total_Positivos_Fila']].sort_values('Total_Positivos_Fila', ascending=False), 
                     hide_index=True, use_container_width=True)

    st.markdown("---")

    # --- ANÁLISIS DETALLADO ---
    st.subheader("🎯 Distribución de Resultados")
    col1, col2 = st.columns(2)

    with col1:
        st.write("**📱 Por Canal de Entrada**")
        fig_canal = px.pie(df_pos, names='CANAL DE ENTRADA', values='Total_Positivos_Fila', hole=0.6,
                           color_discrete_sequence=px.colors.sequential.Blues_r)
        st.plotly_chart(fig_canal, use_container_width=True)

    with col2:
        st.write("**🏢 Por Centro (CON)**")
        fig_centro = px.pie(df_pos, names='CENTRO', values='Total_Positivos_Fila', hole=0.6,
                            color_discrete_sequence=px.colors.sequential.Tealgrn)
        st.plotly_chart(fig_centro, use_container_width=True)

else:
    st.error("No se pudo sincronizar con la base de datos de S-Portal.")
