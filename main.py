import streamlit as st
import pandas as pd
import plotly.express as px

# 1. CONFIGURACIÓN DEL DASHBOARD
st.set_page_config(page_title="S-Portal Hexagon | Command Center", layout="wide")

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

# 2. CARGA DE DATOS ROBUSTA
URL_CSV = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQzIFyCT2C22Hlrz80szN7J2mEfA8N1R7hiAmFAUXaoorwDTOeWNh-ktv__d0vIBS-AQcuV5ws3ZU4C/pub?gid=229458966&single=true&output=csv"

@st.cache_data(ttl=60)
def load_full_data():
    try:
        df = pd.read_csv(URL_CSV)
        df.columns = df.columns.str.strip()
        
        col_fecha = next((c for c in df.columns if 'FECHA' in c.upper()), None)
        if col_fecha:
            df['FECHA_DT'] = pd.to_datetime(df[col_fecha], dayfirst=True, errors='coerce').dt.date
            df = df.dropna(subset=['FECHA_DT'])
        
        col_hora = next((c for c in df.columns if 'HORA' in c.upper()), None)
        if col_hora:
            df['HORA_NUM'] = pd.to_datetime(df[col_hora], errors='coerce').dt.hour.fillna(0).astype(int)
        else:
            df['HORA_NUM'] = 0

        def to_minutes(val):
            try:
                if pd.isna(val) or str(val).strip() in ['', '0:00']: return 0.0
                parts = str(val).split(':')
                return float(int(parts[0]) * 60 + int(parts[1]))
            except: return 0.0

        df['V_DESPACHO'] = df['VARIANZA DE DESPACHO'].apply(to_minutes) if 'VARIANZA DE DESPACHO' in df.columns else 0
        df['V_ATENCION'] = df['VARIANZA DE LA ATENCION'].apply(to_minutes) if 'VARIANZA DE LA ATENCION' in df.columns else 0
        df['V_CIERRE'] = df['VARIANZA DEL CIERRE'].apply(to_minutes) if 'VARIANZA DEL CIERRE' in df.columns else 0

        cols_pos = [c for c in df.columns if 'RESULTADO POSITIVO' in c.upper()]
        df['Total_Positivos_Fila'] = df[cols_pos].notna().sum(axis=1)
        
        if 'CENTRO' in df.columns:
            df['CENTRO'] = df['CENTRO'].astype(str).str.replace('CONTRA', 'CON').str.strip()
            
        return df[df['Total_Positivos_Fila'] > 0].copy()
    except: return None

df_raw = load_full_data()

if df_raw is not None:
    # --- FILTROS LATERALES ---
    st.sidebar.header("🔎 Filtros")
    f_inicio = st.sidebar.date_input("Fecha Desde:", value=df_raw['FECHA_DT'].min())
    f_fin = st.sidebar.date_input("Fecha Hasta:", value=df_raw['FECHA_DT'].max())
    
    lista_horas = list(range(24))
    h_inicio = st.sidebar.selectbox("Hora Desde:", lista_horas, index=0)
    h_fin = st.sidebar.selectbox("Hora Hasta:", lista_horas, index=23)

    df = df_raw[
        (df_raw['FECHA_DT'] >= f_inicio) & (df_raw['FECHA_DT'] <= f_fin) &
        (df_raw['HORA_NUM'] >= h_inicio) & (df_raw['HORA_NUM'] <= h_fin)
    ].copy()

    # --- MÉTRICAS ---
    st.title("🛡️ Hexágono S-Portal | Command Center")
    t_pos = int(df['Total_Positivos_Fila'].sum())
    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("📊 EVENTOS", f"{len(df):,}")
    m2.metric("✅ POSITIVOS", f"{t_pos:,}")
    m3.metric("⏱️ DESPACHO", f"{df['V_DESPACHO'].mean():.1f} min")
    m4.metric("🤝 ATENCIÓN", f"{df['V_ATENCION'].mean():.1f} min")
    m5.metric("🔐 CIERRE", f"{df['V_CIERRE'].mean():.1f} min")

    st.markdown("---")

    # --- MAPA DE CALOR (RESTAURADO) ---
    st.subheader("📍 Mapa de Calor Provincial")
    if 'PROVINCIA' in df.columns:
        prov_stats = df.groupby('PROVINCIA')['Total_Positivos_Fila'].sum().reset_index()
        coords = {'Panamá': [8.98, -79.52], 'Chiriquí': [8.43, -82.43], 'Colón': [9.35, -79.90],
                  'Panamá Oeste': [8.88, -79.78], 'Coclé': [8.51, -80.35], 'Veraguas': [8.10, -80.97],
                  'Los Santos': [7.93, -80.48], 'Herrera': [7.96, -80.70], 'Darién': [8.40, -77.91],
                  'Bocas del Toro': [9.33, -82.24]}
        prov_stats['lat'] = prov_stats['PROVINCIA'].map(lambda x: coords.get(x, [8.5, -80.0])[0])
        prov_stats['lon'] = prov_stats['PROVINCIA'].map(lambda x: coords.get(x, [8.5, -80.0])[1])

        c_map, c_rank = st.columns([2, 1])
        with c_map:
            st.markdown(f"""<div class="floating-metric"><small style="color:#94a3b8; font-size:10px;">Total Filtrado</small><br><span style="font-size:22px; font-weight:bold; color:#00ebff;">{t_pos:,}</span></div>""", unsafe_allow_html=True)
            fig_map = px.density_mapbox(prov_stats, lat='lat', lon='lon', z='Total_Positivos_Fila', radius=40, center=dict(lat=8.5, lon=-80.0), zoom=6, mapbox_style="carto-darkmatter", color_continuous_scale="Blues")
            fig_map.update_layout(margin={"r":0,"t":0,"l":0,"b":0}, paper_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig_map, use_container_width=True)
        with c_rank:
            st.write("**Ranking Provincial**")
            st.dataframe(prov_stats[['PROVINCIA', 'Total_Positivos_Fila']].sort_values('Total_Positivos_Fila', ascending=False), hide_index=True, use_container_width=True)
    
    st.markdown("---")

    # --- PASTELES ---
    col_p1, col_p2 = st.columns(2)
    with col_p1:
        st.write("**📱 Por Canal de Entrada**")
        st.plotly_chart(px.pie(df, names='CANAL DE ENTRADA', values='Total_Positivos_Fila', hole=0.5), use_container_width=True)
    with col_p2:
        st.write("**🏢 Por Centro**")
        st.plotly_chart(px.pie(df, names='CENTRO', values='Total_Positivos_Fila', hole=0.5, color_discrete_sequence=px.colors.sequential.Tealgrn), use_container_width=True)

    st.markdown("---")

    # --- TABLA TÁCTICA ORIGINAL (ORDENADA Y CON TOTALES) ---
    st.subheader("📋 Detalle de Positivos: Tipos vs Centros")
    cols_p = [c for c in df.columns if 'RESULTADO POSITIVO' in c.upper()]
    df_l = pd.melt(df, id_vars=['CENTRO'], value_vars=cols_p, value_name='Tipo').dropna()
    if not df_l.empty:
        tab_centros = df_l.groupby(['Tipo', 'CENTRO']).size().unstack(fill_value=0)
        tab_centros = tab_centros[tab_centros.sum(axis=0).sort_values(ascending=False).index]
        tab_centros['TOTAL IMPACTO'] = tab_centros.sum(axis=1)
        tab_centros = tab_centros.sort_values('TOTAL IMPACTO', ascending=False)
        tot_v = tab_centros.sum(axis=0).to_frame().T
        tot_v.index = ['TOTAL GENERAL']
        st.dataframe(pd.concat([tab_centros, tot_v]), use_container_width=True)

    st.markdown("---")

    # --- LOS DOS CUADROS NUEVOS ---
    col_n1, col_n2 = st.columns(2)
    with col_n1:
        st.subheader("📉 CIERRE DEL INCIDENTES-SUBTIPO")
        col_c = next((c for c in df.columns if 'SUBTIPO' in c.upper() or 'TIPO' == c.upper()), None)
        if col_c:
            tab_sub = df.groupby([col_c, 'CENTRO']).size().unstack(fill_value=0)
            tab_sub = tab_sub[tab_sub.sum(axis=0).sort_values(ascending=False).index]
            tab_sub['TOTAL'] = tab_sub.sum(axis=1)
            tab_sub = tab_sub.sort_values('TOTAL', ascending=False)
            sum_s = tab_sub.sum(axis=0).to_frame().T
            sum_s.index = ['TOTAL GENERAL']
            st.dataframe(pd.concat([tab_sub, sum_s]), use_container_width=True, height=400)

    with col_n2:
        st.subheader("🚔 ZP., SERVICIO POLICIAL O ENLACE")
        col_zp = next((c for c in df.columns if any(k in c.upper() for k in ['ZONA', 'ZP', 'SERVICIO'])), None)
        if col_zp:
            zp_stats = df.groupby(col_zp)['Total_Positivos_Fila'].sum().reset_index().sort_values('Total_Positivos_Fila', ascending=False)
            total_z = pd.DataFrame({col_zp: ['TOTAL GENERAL'], 'Total_Positivos_Fila': [zp_stats['Total_Positivos_Fila'].sum()]})
            st.dataframe(pd.concat([zp_stats, total_z]), use_container_width=True, height=400, hide_index=True)
else:
    st.error("Fallo al cargar base de datos.")
