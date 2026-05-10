import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import time

# 1. CONFIGURACIÓN Y ESTILO
st.set_page_config(page_title="S-Portal Hexagon | Command Center", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #0a0e17; }
    .stMetric { background: rgba(255, 255, 255, 0.05); border: 1px solid #00ebff; border-radius: 10px; padding: 10px; }
    h1, h2, h3, span, p, label { color: #ffffff !important; }
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
        if 'CENTRO' in df.columns:
            df['CENTRO'] = df['CENTRO'].astype(str).str.replace('CONTRA', 'CON', case=False).str.strip()
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
        return df[df['T_POS_COUNT'] > 0].copy()
    except: return None

def create_gauge(value, title, color, is_timer=False):
    suffix = " seg" if is_timer else (" h" if value >= 60 else " min")
    display_val = value / 60 if suffix == " h" else value
    fig = go.Figure(go.Indicator(
        mode = "gauge+number", value = display_val,
        title = {'text': title, 'font': {'size': 14, 'color': "white"}},
        number = {'suffix': suffix, 'font': {'color': "white"}},
        gauge = {'axis': {'range': [0, 60 if is_timer else max(60, display_val*1.5)]}, 'bar': {'color': color}}
    ))
    fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', height=200, margin=dict(l=20, r=20, t=40, b=20))
    return fig

df_raw = load_full_data()

if df_raw is not None:
    with st.sidebar:
        st.header("🔎 Filtros")
        f1 = st.date_input("Desde:", df_raw['FECHA_DT'].min().date())
        f2 = st.date_input("Hasta:", df_raw['FECHA_DT'].max().date())
        h1 = st.selectbox("Hora Inicial:", list(range(24)), index=0)
        h2 = st.selectbox("Hora Final:", list(range(24)), index=23)
        st.plotly_chart(create_gauge(remaining, "ACTUALIZACIÓN", "#00ebff", is_timer=True), use_container_width=True)

    df = df_raw[(df_raw['FECHA_DT'].dt.date >= f1) & (df_raw['FECHA_DT'].dt.date <= f2) & 
                (df_raw['HORA_NUM'] >= h1) & (df_raw['HORA_NUM'] <= h2)].copy()

    st.title("🛡️ Hexágono S-Portal | Centro de Mando")
    total_positivos = int(df['T_POS_COUNT'].sum())
    col_met1, col_met2 = st.columns(2)
    col_met1.metric("📊 EVENTOS TOTALES", f"{len(df):,}")
    col_met2.metric("✅ TOTAL POSITIVOS", f"{total_positivos:,}")

    g1, g2, g3 = st.columns(3)
    v_desp = df['VARIANZA DE DESPACHO_M'].mean() if 'VARIANZA DE DESPACHO_M' in df.columns else 0
    v_aten = df['VARIANZA DE LA ATENCION_M'].mean() if 'VARIANZA DE LA ATENCION_M' in df.columns else 0
    v_cierre_col = 'VARIANZA DEL CIERRE_M' if 'VARIANZA DEL CIERRE_M' in df.columns else 'VARIANZA DE CIERRE_M'
    v_cier = df[v_cierre_col].mean() if v_cierre_col in df.columns else 0
    with g1: st.plotly_chart(create_gauge(v_desp, "VARIANZA DESPACHO", "#00ebff"), use_container_width=True)
    with g2: st.plotly_chart(create_gauge(v_aten, "VARIANZA ATENCIÓN", "#00ffaa"), use_container_width=True)
    with g3: st.plotly_chart(create_gauge(v_cier, "VARIANZA CIERRE", "#ffaa00"), use_container_width=True)

    st.markdown("---")

    # --- SECCIÓN 1: MAPA SATELITAL (SIN TOKEN REQUERIDO) ---
    st.subheader("📍 MAPA SATELITAL DE INCIDENCIAS")
    if 'PROVINCIA' in df.columns:
        cols_p = [c for c in df.columns if 'RESULTADO POSITIVO' in c.upper()]
        df_long = pd.melt(df, id_vars=['PROVINCIA'], value_vars=cols_p, value_name='Tipo').dropna()
        
        def get_detailed_top(group):
            counts = group['Tipo'].value_counts()
            top_5 = counts.nlargest(5)
            others_count = counts.iloc[5:].sum()
            lines = [f"• {tipo}: {cant}" for tipo, cant in top_5.items()]
            if others_count > 0: lines.append(f"• Otros: {others_count}")
            return "<br>".join([""] + lines)

        top_details = df_long.groupby('PROVINCIA').apply(get_detailed_top).reset_index(name='DETALLE_TOP')
        prov_stats = df.groupby('PROVINCIA')['T_POS_COUNT'].sum().reset_index().sort_values('T_POS_COUNT', ascending=True)
        prov_stats = prov_stats.merge(top_details, on='PROVINCIA', how='left')
        
        coords = {'Panamá':[8.98,-79.52], 'Chiriquí':[8.43,-82.43], 'Colón':[9.35,-79.9], 'Panamá Oeste':[8.88,-79.78], 'Coclé':[8.51,-80.35], 'Veraguas':[8.1,-80.97], 'Los Santos':[7.93,-80.48], 'Herrera':[7.96,-80.7], 'Darién':[8.4,-77.91], 'Bocas del Toro':[9.33,-82.24]}
        prov_stats['lat'] = prov_stats['PROVINCIA'].map(lambda x: coords.get(x, [8.5, -80.0])[0])
        prov_stats['lon'] = prov_stats['PROVINCIA'].map(lambda x: coords.get(x, [8.5, -80.0])[1])
        
        c_map, c_rank = st.columns([2, 1])
        with c_map:
            st.markdown(f'<div class="map-overlay-total"><small style="color:#00ebff;">TOTAL POSITIVOS</small><br><span style="font-size:24px; font-weight:bold;">{total_positivos:,}</span></div>', unsafe_allow_html=True)
            
            # Scatter mapbox con capas de satélite públicas
            fig_mapa = px.scatter_mapbox(
                prov_stats, lat='lat', lon='lon', size='T_POS_COUNT', color='T_POS_COUNT',
                color_continuous_scale="Jet", size_max=40, zoom=6.5,
                center=dict(lat=8.5, lon=-80.0),
                hover_name='PROVINCIA',
                hover_data={'lat': False, 'lon': False, 'T_POS_COUNT': True, 'DETALLE_TOP': True},
                labels={'T_POS_COUNT': 'Total Positivos', 'DETALLE_TOP': 'Detalle'}
            )
            
            # Configuración para forzar la vista satelital sin necesidad de Mapbox Token
            fig_mapa.update_layout(
                mapbox=dict(
                    style="white-bg",
                    layers=[{
                        "below": 'traces',
                        "sourcetype": "raster",
                        "source": ["https://basemap.nationalmap.gov/arcgis/rest/services/USGSImageryOnly/MapServer/tile/{z}/{y}/{x}"]
                    }]
                ),
                margin={"r":0,"t":0,"l":0,"b":0},
                paper_bgcolor='rgba(0,0,0,0)',
                coloraxis_showscale=False
            )
            st.plotly_chart(fig_mapa, use_container_width=True)
            
        with c_rank:
            fig_prov = px.bar(prov_stats, x='T_POS_COUNT', y='PROVINCIA', orientation='h', text='T_POS_COUNT', color='T_POS_COUNT', color_continuous_scale='Tealgrn')
            fig_prov.update_layout(showlegend=False, coloraxis_showscale=False, paper_bgcolor='rgba(0,0,0,0)', font=dict(color="white"), height=450)
            st.plotly_chart(fig_prov, use_container_width=True)

    st.markdown("---")
    # --- SECCIONES RESTANTES (SIN TOCAR) ---
    cp1, cp2 = st.columns(2)
    with cp1: st.plotly_chart(px.pie(df, names='CANAL DE ENTRADA', values='T_POS_COUNT', title="Proporción por Canales", hole=0.5), use_container_width=True)
    with cp2: st.plotly_chart(px.pie(df, names='CENTRO', values='T_POS_COUNT', title="Proporción por Centros", hole=0.5, color_discrete_sequence=px.colors.sequential.Tealgrn), use_container_width=True)
    st.subheader("📋 DETALLE: TIPOS VS CENTROS")
    df_l_t = pd.melt(df, id_vars=['CENTRO'], value_vars=cols_p, value_name='Tipo').dropna()
    if not df_l_t.empty:
        t_c = df_l_t.groupby(['Tipo', 'CENTRO']).size().unstack(fill_value=0)
        t_c['TOTAL'] = t_c.sum(axis=1)
        orden_centros = t_c.drop(columns='TOTAL').sum().sort_values(ascending=False).index.tolist()
        t_c = t_c[orden_centros + ['TOTAL']].sort_values('TOTAL', ascending=False)
        st.dataframe(pd.concat([t_c, t_c.sum().to_frame(name='TOTAL GENERAL').T]), use_container_width=True)
    st.markdown("---")
    cn1, cn2 = st.columns(2)
    with cn1:
        st.subheader("📉 CIERRE DEL INCIDENTE-SUBTIPO")
        col_cierre = next((c for c in df.columns if 'CIERRE' in c.upper() and 'SUBTIPO' in c.upper()), None)
        if col_cierre:
            t_sb = df.groupby([col_cierre, 'CENTRO']).size().unstack(fill_value=0)
            t_sb['TOTAL'] = t_sb.sum(axis=1)
            orden_c = t_sb.drop(columns='TOTAL').sum().sort_values(ascending=False).index.tolist()
            t_sb = t_sb[orden_c + ['TOTAL']].sort_values('TOTAL', ascending=False)
            st.dataframe(pd.concat([t_sb, t_sb.sum().to_frame(name='TOTAL GENERAL').T]), use_container_width=True, height=400)
    with cn2:
        st.subheader("🚔 ZP., SERVICIO POLICIAL O ENLACE")
        col_zp = next((c for c in df.columns if any(k in c.upper() for k in ['ZONA', 'ZP', 'SERVICIO'])), None)
        if col_zp:
            zp_s = df.groupby(col_zp)['T_POS_COUNT'].sum().reset_index().sort_values('T_POS_COUNT', ascending=False)
            st.dataframe(pd.concat([zp_s, pd.DataFrame({col_zp:['TOTAL GENERAL'], 'T_POS_COUNT':[zp_s['T_POS_COUNT'].sum()]})]), use_container_width=True, height=400, hide_index=True)
    st.markdown("---")
    st.subheader("📊 ANÁLISIS POR UNIDAD Y TIEMPO")
    c_mes, c_vv, c_desp = st.columns(3)
    with c_mes:
        if 'MES_NOMBRE' in df.columns:
            st.write("**📅 Positivos por Meses**")
            m_s = df.groupby('MES_NOMBRE')['T_POS_COUNT'].sum().reset_index()
            st.dataframe(pd.concat([m_s, pd.DataFrame({'MES_NOMBRE':['TOTAL'], 'T_POS_COUNT':[m_s['T_POS_COUNT'].sum()]})]), use_container_width=True, hide_index=True)
    with c_vv:
        col_vv = next((c for c in df.columns if 'UNIDAD DE VV' in c.upper() or 'VV/104' in c.upper()), None)
        if col_vv:
            st.write("**📟 Unidad de VV/104**")
            df[col_vv] = df[col_vv].fillna("SIN ASIGNAR")
            vv_s = df.groupby([col_vv, 'CENTRO']).size().reset_index(name='E').sort_values('E', ascending=False)
            st.dataframe(pd.concat([vv_s, pd.DataFrame({col_vv:['TOTAL GENERAL'], 'CENTRO':['-'], 'E':[vv_s['E'].sum()]})]), use_container_width=True, hide_index=True)
    with c_desp:
        col_desp = next((c for c in df.columns if 'UNIDAD DE DESPACHO' in c.upper()), None)
        if col_desp:
            st.write("**🚨 Unidad de Despacho**")
            df[col_desp] = df[col_desp].fillna("SIN ASIGNAR")
            dp_s = df.groupby([col_desp, 'CENTRO']).size().reset_index(name='E').sort_values('E', ascending=False)
            st.dataframe(pd.concat([dp_s, pd.DataFrame({col_desp:['TOTAL GENERAL'], 'CENTRO':['-'], 'E':[dp_s['E'].sum()]})]), use_container_width=True, hide_index=True)
    time.sleep(1)
    st.rerun()
