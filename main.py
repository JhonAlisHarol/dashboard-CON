import streamlit as st
import pandas as pd
import plotly.express as px
import time

# 1. CONFIGURACIÓN Y ESTILO DEL DASHBOARD
st.set_page_config(page_title="S-Portal Hexagon | Command Center", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #0a0e17; }
    .stMetric { background: rgba(255, 255, 255, 0.05); border: 1px solid #00ebff; border-radius: 10px; }
    h1, h2, h3, span, p, label { color: #ffffff !important; }
    .timer-box {
        position: fixed; top: 10px; right: 80px;
        background: rgba(0, 235, 255, 0.1); border: 1px solid #00ebff;
        padding: 5px 15px; border-radius: 20px; z-index: 999; font-family: monospace;
    }
    .map-overlay-total {
        position: relative; top: 60px; left: 20px;
        background: rgba(10, 14, 23, 0.85); border: 2px solid #00ebff;
        padding: 10px 20px; border-radius: 10px; z-index: 100;
        width: fit-content; margin-bottom: -70px;
    }
    </style>
    """, unsafe_allow_html=True)

# 2. SISTEMA DE RECARGA AUTOMÁTICA
if 'last_update' not in st.session_state:
    st.session_state.last_update = time.time()

elapsed = int(time.time() - st.session_state.last_update)
remaining = max(0, 60 - elapsed)
st.markdown(f'<div class="timer-box">🔄 Refresco en: {remaining}s</div>', unsafe_allow_html=True)

if remaining <= 0:
    st.session_state.last_update = time.time()
    st.rerun()

# 3. CARGA Y PROCESAMIENTO DE DATOS
URL_CSV = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQzIFyCT2C22Hlrz80szN7J2mEfA8N1R7hiAmFAUXaoorwDTOeWNh-ktv__d0vIBS-AQcuV5ws3ZU4C/pub?gid=229458966&single=true&output=csv"

@st.cache_data(ttl=60)
def load_full_data():
    try:
        df = pd.read_csv(URL_CSV)
        df.columns = df.columns.str.strip()
        
        col_f = next((c for c in df.columns if 'FECHA' in c.upper()), None)
        if col_f: 
            df['FECHA_DT'] = pd.to_datetime(df[col_f], dayfirst=True, errors='coerce')
            df['MES_NOMBRE'] = df['FECHA_DT'].dt.strftime('%m - %B')
        
        col_h = next((c for c in df.columns if 'HORA' in c.upper()), None)
        if col_h: 
            df['HORA_NUM'] = pd.to_datetime(df[col_h], errors='coerce').dt.hour.fillna(0).astype(int)

        def to_m(v):
            try:
                if pd.isna(v) or v == "" or v == 0: return 0.0
                p = str(v).split(':')
                return float(int(p[0])*60 + int(p[1])) if len(p) >= 2 else float(v)
            except: return 0.0

        for c in ['VARIANZA DE DESPACHO', 'VARIANZA DE LA ATENCION', 'VARIANZA DEL CIERRE', 'VARIANZA DE CIERRE']:
            if c in df.columns: df[c+'_M'] = df[c].apply(to_m)

        cols_pos = [c for c in df.columns if 'RESULTADO POSITIVO' in c.upper()]
        df['T_POS_COUNT'] = df[cols_pos].notna().sum(axis=1)
        
        if 'CENTRO' in df.columns:
            df['CENTRO'] = df['CENTRO'].astype(str).str.replace('CONTRA', 'CON').str.strip()
            
        return df[df['T_POS_COUNT'] > 0].copy()
    except: return None

def format_time(minutes):
    if minutes >= 60: return f"{minutes/60:.1f} h"
    return f"{minutes:.1f} min"

df_raw = load_full_data()

if df_raw is not None:
    # --- FILTROS ---
    with st.sidebar:
        st.header("🔎 Filtros")
        f1 = st.date_input("Desde:", df_raw['FECHA_DT'].min().date())
        f2 = st.date_input("Hasta:", df_raw['FECHA_DT'].max().date())
        h1 = st.selectbox("Hora Inicial:", list(range(24)), index=0)
        h2 = st.selectbox("Hora Final:", list(range(24)), index=23)

    df = df_raw[(df_raw['FECHA_DT'].dt.date >= f1) & (df_raw['FECHA_DT'].dt.date <= f2) & 
                (df_raw['HORA_NUM'] >= h1) & (df_raw['HORA_NUM'] <= h2)].copy()

    # --- MÉTRICAS ---
    st.title("🛡️ Hexágono S-Portal | Command Center")
    total_positivos = int(df['T_POS_COUNT'].sum())
    
    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("📊 EVENTOS", f"{len(df):,}")
    m2.metric("✅ POSITIVOS", f"{total_positivos:,}")
    m3.metric("⏱️ DESPACHO", format_time(df['VARIANZA DE DESPACHO_M'].mean() if 'VARIANZA DE DESPACHO_M' in df.columns else 0))
    m4.metric("🤝 ATENCIÓN", format_time(df['VARIANZA DE LA ATENCION_M'].mean() if 'VARIANZA DE LA ATENCION_M' in df.columns else 0))
    v_cierre_col = 'VARIANZA DEL CIERRE_M' if 'VARIANZA DEL CIERRE_M' in df.columns else 'VARIANZA DE CIERRE_M'
    m5.metric("🔐 CIERRE", format_time(df[v_cierre_col].mean() if v_cierre_col in df.columns else 0))

    st.markdown("---")

    # --- SECCIÓN 1: MAPA ---
    st.subheader("📍 MAPA DE CALOR PROVINCIAL")
    if 'PROVINCIA' in df.columns:
        prov_stats = df.groupby('PROVINCIA')['T_POS_COUNT'].sum().reset_index()
        coords = {'Panamá':[8.98,-79.52], 'Chiriquí':[8.43,-82.43], 'Colón':[9.35,-79.9], 'Panamá Oeste':[8.88,-79.78], 'Coclé':[8.51,-80.35], 'Veraguas':[8.1,-80.97], 'Los Santos':[7.93,-80.48], 'Herrera':[7.96,-80.7], 'Darién':[8.4,-77.91], 'Bocas del Toro':[9.33,-82.24]}
        prov_stats['lat'] = prov_stats['PROVINCIA'].map(lambda x: coords.get(x, [8.5, -80.0])[0])
        prov_stats['lon'] = prov_stats['PROVINCIA'].map(lambda x: coords.get(x, [8.5, -80.0])[1])
        c_map, c_rank = st.columns([2, 1])
        with c_map:
            st.markdown(f'<div class="map-overlay-total"><small style="color:#00ebff;">TOTAL POSITIVOS</small><br><span style="font-size:24px; font-weight:bold;">{total_positivos:,}</span></div>', unsafe_allow_html=True)
            st.plotly_chart(px.density_mapbox(prov_stats, lat='lat', lon='lon', z='T_POS_COUNT', radius=35, center=dict(lat=8.5, lon=-80.0), zoom=6, mapbox_style="carto-darkmatter"), use_container_width=True)
        with c_rank:
            st.write("**Ranking Provincial**")
            st.dataframe(prov_stats[['PROVINCIA', 'T_POS_COUNT']].sort_values('T_POS_COUNT', ascending=False), hide_index=True, use_container_width=True)

    st.markdown("---")

    # --- SECCIÓN 2: PASTELES ---
    st.subheader("📊 DISTRIBUCIÓN POR CANALES Y CENTROS")
    cp1, cp2 = st.columns(2)
    with cp1: st.plotly_chart(px.pie(df, names='CANAL DE ENTRADA', values='T_POS_COUNT', title="Proporción por Canales", hole=0.5), use_container_width=True)
    with cp2: st.plotly_chart(px.pie(df, names='CENTRO', values='T_POS_COUNT', title="Proporción por Centros", hole=0.5, color_discrete_sequence=px.colors.sequential.Tealgrn), use_container_width=True)

    # --- SECCIÓN 3: TABLA TIPOS VS CENTROS (ORDENADO CENTROS Y FILAS) ---
    st.subheader("📋 DETALLE: TIPOS VS CENTROS")
    cols_p = [c for c in df.columns if 'RESULTADO POSITIVO' in c.upper()]
    df_l = pd.melt(df, id_vars=['CENTRO'], value_vars=cols_p, value_name='Tipo').dropna()
    if not df_l.empty:
        t_c = df_l.groupby(['Tipo', 'CENTRO']).size().unstack(fill_value=0)
        # Ordenar columnas (Centros) de mayor a menor según su suma total
        cols_sorted = t_c.sum(axis=0).sort_values(ascending=False).index
        t_c = t_c[cols_sorted]
        # Ordenar filas (Tipos) por el total
        t_c['TOTAL'] = t_c.sum(axis=1)
        t_c = t_c.sort_values('TOTAL', ascending=False)
        st.dataframe(pd.concat([t_c, t_c.sum().to_frame(name='TOTAL GENERAL').T]), use_container_width=True)

    st.markdown("---")

    # --- SECCIÓN 4: CIERRE Y ZONAS ---
    cn1, cn2 = st.columns(2)
    with cn1:
        st.subheader("📉 CIERRE DEL INCIDENTE-SUBTIPO")
        col_cierre = next((c for c in df.columns if 'CIERRE' in c.upper() and 'SUBTIPO' in c.upper()), None)
        if col_cierre:
            df[col_cierre] = df[col_cierre].fillna("SIN ESPECIFICAR")
            t_sb = df.groupby([col_cierre, 'CENTRO']).size().unstack(fill_value=0)
            # Ordenar columnas (Centros) de mayor a menor
            cols_sb_sorted = t_sb.sum(axis=0).sort_values(ascending=False).index
            t_sb = t_sb[cols_sb_sorted]
            # Ordenar filas por el total
            t_sb['TOTAL'] = t_sb.sum(axis=1)
            t_sb = t_sb.sort_values('TOTAL', ascending=False)
            st.dataframe(pd.concat([t_sb, t_sb.sum().to_frame(name='TOTAL GENERAL').T]), use_container_width=True, height=400)

    with cn2:
        st.subheader("🚔 ZP., SERVICIO POLICIAL O ENLACE")
        col_zp = next((c for c in df.columns if any(k in c.upper() for k in ['ZONA', 'ZP', 'SERVICIO'])), None)
        if col_zp:
            zp_s = df.groupby(col_zp)['T_POS_COUNT'].sum().reset_index().sort_values('T_POS_COUNT', ascending=False)
            st.dataframe(pd.concat([zp_s, pd.DataFrame({col_zp:['TOTAL GENERAL'], 'T_POS_COUNT':[zp_s['T_POS_COUNT'].sum()]})]), use_container_width=True, height=400, hide_index=True)

    st.markdown("---")

    # --- SECCIÓN 5: ANÁLISIS DETALLADO ---
    st.subheader("📊 ANÁLISIS POR UNIDAD Y TIEMPO (DETALLADO)")
    c_mes, c_vv, c_desp = st.columns(3)
    
    with c_mes:
        st.write("**📅 Positivos por Meses**")
        if 'MES_NOMBRE' in df.columns:
            df['MES_NOMBRE'] = df['MES_NOMBRE'].fillna("SIN FECHA")
            mes_stats = df.groupby('MES_NOMBRE')['T_POS_COUNT'].sum().reset_index()
            mes_total = pd.DataFrame({'MES_NOMBRE': ['TOTAL GENERAL'], 'T_POS_COUNT': [mes_stats['T_POS_COUNT'].sum()]})
            st.dataframe(pd.concat([mes_stats.sort_values('MES_NOMBRE'), mes_total]), use_container_width=True, hide_index=True)

    with c_vv:
        st.write("**📟 Unidad de VV/104 por Centro**")
        col_vv = next((c for c in df.columns if 'UNIDAD DE VV' in c.upper() or 'VV/104' in c.upper()), None)
        if col_vv and 'CENTRO' in df.columns:
            df[col_vv] = df[col_vv].fillna("SIN UNIDAD ASIGNADA")
            vv_stats = df.groupby([col_vv, 'CENTRO']).size().reset_index(name='EVENTOS').sort_values('EVENTOS', ascending=False)
            vv_total = pd.DataFrame({col_vv: ['TOTAL GENERAL'], 'CENTRO': ['-'], 'EVENTOS': [vv_stats['EVENTOS'].sum()]})
            st.dataframe(pd.concat([vv_stats, vv_total]), use_container_width=True, hide_index=True, height=350)

    with c_desp:
        st.write("**🚨 Unidad de Despacho por Centro**")
        col_desp = next((c for c in df.columns if 'UNIDAD DE DESPACHO' in c.upper()), None)
        if col_desp and 'CENTRO' in df.columns:
            df[col_desp] = df[col_desp].fillna("SIN UNIDAD ASIGNADA")
            desp_stats = df.groupby([col_desp, 'CENTRO']).size().reset_index(name='EVENTOS').sort_values('EVENTOS', ascending=False)
            desp_total = pd.DataFrame({col_desp: ['TOTAL GENERAL'], 'CENTRO': ['-'], 'EVENTOS': [desp_stats['EVENTOS'].sum()]})
            st.dataframe(pd.concat([desp_stats, desp_total]), use_container_width=True, hide_index=True, height=350)

    time.sleep(1)
    st.rerun()
