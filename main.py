import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import time

# 1. CONFIGURACIÓN Y ESTILO (Optimizado para Computadora y Teléfono)
st.set_page_config(page_title="S-Portal Hexagon | Command Center", layout="wide")

st.markdown("""
    <style>
    /* 1.OCULTAR OPCIONES DE CÓDIGO EN EL MENÚ */
    #MainMenu {visibility: visible;}
    ul[data-testid="main-menu-list"] li:nth-child(4),
    ul[data-testid="main-menu-list"] li:nth-child(5) {
        display: none !important;
    }
    /* 2. ELIMINAR EL LOGO DE GITHUB Y ENLACE AL REPOSITORIO */
    .stApp a svg {display: none !important; }
    div[data-testid="stStatusWidget"] { visibility: hidden; }
    footer {visibility: hidden; }
    
    /* Estilo Base */
    .stApp { background-color: #0a0e17; }
    h1, h2, h3, span, p, label { color: #ffffff !important; }
    
    .stMetric { 
        background: rgba(255, 255, 255, 0.05); 
        border: 1px solid #00ebff; 
        border-radius: 10px; 
        padding: 10px; 
    }

    .neon-container {
        position: relative;
        border-radius: 10px;
        padding: 4px;
        background: rgba(10, 14, 23, 1);
        background-clip: padding-box;
        border: 1px solid transparent;
        overflow: hidden;
        margin-bottom: 1rem;
    }

    .neon-container::before {
        content: '';
        position: absolute;
        top: -50%;
        left: -50%;
        width: 200%;
        height: 200%;
        background: conic-gradient(
            #ff0000, #ff7300, #fffb00, #48ff00, #00ffd5, #002bff, #7a00ff, #ff00c8, #ff0000
        );
        animation: rotate-neon 3s linear infinite;
        z-index: 0;
    }

    .neon-inner-content {
        position: relative;
        background: #0d121f;
        border-radius: 7px;
        padding: 15px;
        z-index: 1;
    }

    @keyframes rotate-neon {
        from { transform: rotate(0deg); }
        to { transform: rotate(360deg); }
    }

    .neon-inner-content h3 { margin: 0; font-size: 14px; text-transform: uppercase; color: #ffffff !important; }
    .neon-inner-content p { margin: 0; font-size: 28px; font-weight: bold; color: #00ebff !important; }

    .author-text { color: #00ebff !important; font-size: 14px; font-style: italic; margin-top: -15px; margin-bottom: 15px; }
    
    .map-overlay-total {
        position: relative; top: 60px; left: 20px;
        background: rgba(10, 14, 23, 0.85); border: 2px solid #00ebff;
        padding: 10px 20px; border-radius: 10px; z-index: 100;
        width: fit-content; margin-bottom: -70px;
    }

    /* AJUSTES RESPONSIVOS PARA TELÉFONO */
    @media (max-width: 768px) {
        .neon-inner-content p { font-size: 22px !important; } /* Texto un poco más pequeño en móvil */
        .map-overlay-total { 
            position: relative; top: 10px; left: 10px; 
            margin-bottom: 10px; width: 90%; 
        } /* El indicador del mapa se ajusta para no estorbar en móvil */
        .stPlotlyChart { height: 350px !important; } /* Ajuste de altura de gráficos */
    }
    </style>
    """, unsafe_allow_html=True)

# 2. SISTEMA DE RECARGA (Mantenido intacto)
if 'last_update' not in st.session_state:
    st.session_state.last_update = time.time()

elapsed = int(time.time() - st.session_state.last_update)
remaining = max(0, 60 - elapsed)

if remaining <= 0:
    st.session_state.last_update = time.time()
    st.rerun()

# 3. CARGA DE DATOS (Mantenido intacto)
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
            df['MES_NUM'] = df['FECHA_DT'].dt.month
            df['MES_NOMBRE'] = df['FECHA_DT'].dt.strftime('%B').str.capitalize()
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

    st.title("🛡️ C.O.N.C5- S-Portal | Centro de Mando")
    st.markdown('<p class="author-text">Elaborado por el Cabo 1° Elmer Rodriguez</p>', unsafe_allow_html=True)

    c_m1, c_m2 = st.columns(2)
    with c_m1:
        st.markdown(f'<div class="neon-container"><div class="neon-inner-content"><h3>📊 EVENTOS TOTALES</h3><p>{len(df):,}</p></div></div>', unsafe_allow_html=True)
    with c_m2:
        st.markdown(f'<div class="neon-container"><div class="neon-inner-content"><h3>✅ TOTAL POSITIVOS</h3><p>{int(df["T_POS_COUNT"].sum()):,}</p></div></div>', unsafe_allow_html=True)

    g1, g2, g3 = st.columns(3)
    v_desp = df['VARIANZA DE DESPACHO_M'].mean() if 'VARIANZA DE DESPACHO_M' in df.columns else 0
    v_aten = df['VARIANZA DE LA ATENCION_M'].mean() if 'VARIANZA DE LA ATENCION_M' in df.columns else 0
    v_c_col = 'VARIANZA DEL CIERRE_M' if 'VARIANZA DEL CIERRE_M' in df.columns else 'VARIANZA DE CIERRE_M'
    v_cier = df[v_c_col].mean() if v_c_col in df.columns else 0
    with g1: st.plotly_chart(create_gauge(v_desp, "VARIANZA DESPACHO", "#00ebff"), use_container_width=True)
    with g2: st.plotly_chart(create_gauge(v_aten, "VARIANZA ATENCIÓN", "#00ffaa"), use_container_width=True)
    with g3: st.plotly_chart(create_gauge(v_cier, "VARIANZA CIERRE", "#ffaa00"), use_container_width=True)

    st.markdown("---")

    # --- SECCIÓN DEL MAPA ---
    st.subheader("📍 MAPA TÁCTICO DETALLADO DE INCIDENCIAS")
    if 'PROVINCIA' in df.columns:
        cols_p = [c for c in df.columns if 'RESULTADO POSITIVO' in c.upper()]
        df_long = pd.melt(df, id_vars=['PROVINCIA'], value_vars=cols_p, value_name='Tipo').dropna()
        top_details = df_long.groupby('PROVINCIA').apply(lambda g: "<br>".join([f"• {t}: {v}" for t, v in g['Tipo'].value_counts().nlargest(5).items()])).reset_index(name='DETALLE_TOP')
        prov_stats = df.groupby('PROVINCIA')['T_POS_COUNT'].sum().reset_index().sort_values('T_POS_COUNT', ascending=True)
        prov_stats = prov_stats.merge(top_details, on='PROVINCIA', how='left')
        
        coords = {
            'Panamá':[8.98,-79.52], 'Chiriquí':[8.43,-82.43], 'Colón':[9.35,-79.9], 
            'Panamá Oeste':[8.88,-79.78], 'Coclé':[8.51,-80.35], 'Veraguas':[8.1,-80.97], 
            'Los Santos':[7.93,-80.48], 'Herrera':[7.96,-80.7], 'Darién':[8.4,-77.91], 
            'Bocas del Toro':[9.33,-82.24], 
            'Comarca Ngäbe-Buglé':[8.41, -81.75]
        }
        
        prov_stats['lat'] = prov_stats['PROVINCIA'].map(lambda x: coords.get(x, [8.5, -80.0])[0])
        prov_stats['lon'] = prov_stats['PROVINCIA'].map(lambda x: coords.get(x, [8.5, -80.0])[1])
        
        c_map, c_rank = st.columns([2, 1])
        with c_map:
            st.markdown(f'<div class="map-overlay-total"><small style="color:#00ebff;">TOTAL POSITIVOS</small><br><span style="font-size:24px; font-weight:bold;">{int(df["T_POS_COUNT"].sum()):,}</span></div>', unsafe_allow_html=True)
            
            fig_m = px.scatter_mapbox(prov_stats, lat='lat', lon='lon', size='T_POS_COUNT', 
                                      color='T_POS_COUNT', color_continuous_scale="Darkmint", 
                                      size_max=55, zoom=7.2, center=dict(lat=8.5, lon=-80.5), 
                                      hover_name='PROVINCIA', 
                                      hover_data={'lat':False, 'lon':False, 'T_POS_COUNT':True, 'DETALLE_TOP':True})
            
            fig_m.update_layout(mapbox_style="carto-darkmatter", margin={"r":0,"t":0,"l":0,"b":0}, 
                                paper_bgcolor='rgba(0,0,0,0)', coloraxis_showscale=False)
            st.plotly_chart(fig_m, use_container_width=True)
        with c_rank:
            st.plotly_chart(px.bar(prov_stats, x='T_POS_COUNT', y='PROVINCIA', orientation='h', text='T_POS_COUNT', color='T_POS_COUNT', color_continuous_scale='Tealgrn').update_layout(showlegend=False, coloraxis_showscale=False, paper_bgcolor='rgba(0,0,0,0)', font=dict(color="white"), height=400), use_container_width=True)

    # --- RESTO DEL CÓDIGO (Mantenido intacto) ---
    st.markdown("---")
    cp1, cp2 = st.columns(2)
    with cp1: st.plotly_chart(px.pie(df, names='CANAL DE ENTRADA', values='T_POS_COUNT', title="Proporción por Canales", hole=0.5), use_container_width=True)
    with cp2: st.plotly_chart(px.pie(df, names='CENTRO', values='T_POS_COUNT', title="Proporción por Centros", hole=0.5, color_discrete_sequence=px.colors.sequential.Tealgrn), use_container_width=True)
    
    st.subheader("📋 DETALLE: TIPOS VS CENTROS")
    df_l_t = pd.melt(df, id_vars=['CENTRO'], value_vars=cols_p, value_name='Tipo').dropna()
    if not df_l_t.empty:
        t_c = df_l_t.groupby(['Tipo', 'CENTRO']).size().unstack(fill_value=0)
        t_c['TOTAL'] = t_c.sum(axis=1)
        ord_c = t_c.drop(columns='TOTAL').sum().sort_values(ascending=False).index.tolist()
        t_c = t_c[ord_c + ['TOTAL']].sort_values('TOTAL', ascending=False)
        st.dataframe(pd.concat([t_c, t_c.sum().to_frame(name='TOTAL GENERAL').T]), use_container_width=True)
    
    st.markdown("---")
    cn1, cn2 = st.columns(2)
    with cn1:
        st.subheader("📉 CIERRE DEL INCIDENTE-SUBTIPO")
        col_c = next((c for c in df.columns if 'CIERRE' in c.upper() and 'SUBTIPO' in c.upper()), None)
        if col_c:
            t_sb = df.groupby([col_c, 'CENTRO']).size().unstack(fill_value=0)
            t_sb['TOTAL'] = t_sb.sum(axis=1)
            ord_centros_cierre = t_sb.drop(columns='TOTAL').sum().sort_values(ascending=False).index.tolist()
            t_sb = t_sb[ord_centros_cierre + ['TOTAL']].sort_values('TOTAL', ascending=False)
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
            m_s = df.groupby(['MES_NOMBRE', 'MES_NUM'])['T_POS_COUNT'].sum().reset_index().sort_values('MES_NUM', ascending=False)
            fig_m_b = px.bar(m_s, x='T_POS_COUNT', y='MES_NOMBRE', orientation='h', text='T_POS_COUNT', color='T_POS_COUNT', color_continuous_scale='Tealgrn')
            fig_m_b.update_layout(showlegend=False, coloraxis_showscale=False, paper_bgcolor='rgba(0,0,0,0)', font=dict(color="white"), height=400)
            st.plotly_chart(fig_m_b, use_container_width=True)
    with c_vv:
        col_vv = next((c for c in df.columns if 'UNIDAD DE VV' in c.upper() or 'VV/104' in c.upper()), None)
        if col_vv:
            st.write("**📟 Unidad de VV/104**")
            df[col_vv] = df[col_vv].fillna("SIN ASIGNAR").astype(str)
            vv_s = df.groupby([col_vv, 'CENTRO']).size().reset_index(name='E').sort_values('E', ascending=False)
            st.dataframe(pd.concat([vv_s, pd.DataFrame({col_vv:['TOTAL GENERAL'], 'CENTRO':['-'], 'E':[vv_s['E'].sum()]})]), use_container_width=True, hide_index=True)
    with c_desp:
        col_dp = next((c for c in df.columns if 'UNIDAD DE DESPACHO' in c.upper()), None)
        if col_dp:
            st.write("**🚨 Unidad de Despacho**")
            df[col_dp] = df[col_dp].fillna("SIN ASIGNAR").astype(str)
            dp_s = df.groupby([col_dp, 'CENTRO']).size().reset_index(name='E').sort_values('E', ascending=False)
            st.dataframe(pd.concat([dp_s, pd.DataFrame({col_dp:['TOTAL GENERAL'], 'CENTRO':['-'], 'E':[dp_s['E'].sum()]})]), use_container_width=True, hide_index=True)
    
    time.sleep(1)
    st.rerun()
