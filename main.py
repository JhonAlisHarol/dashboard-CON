import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import time
import unicodedata
import base64


# --- FONDO GLOBAL PARA TODO EL DASHBOARD Y SIDEBAR ---
st.markdown("""
    <style>
    /* 1. Fondo de toda la aplicación */
    .stApp {
        background-image: url("https://raw.githubusercontent.com/JhonAlisHarol/dashboard-CON/main/FONDO%20PARA%20DASHBOARD.png");
        background-size: cover;
        background-position: center;
        background-attachment: fixed;
    }

    /* 2. Forzar transparencia en los contenedores para que se vea el fondo */
    .stApp, [data-testid="stSidebar"], .stMainBlockContainer {
        background-color: transparent !important;
    }

    /* 3. Capa de oscurecimiento (ajusta el 0.6 si quieres ver más o menos la imagen) */
    .stApp::before {
        content: "";
        position: absolute;
        top: 0; left: 0; width: 100%; height: 100%;
        background: rgba(0, 0, 0, 0.6);
        z-index: -1;
    }
    
    /* 4. Asegurar que los textos se vean blancos sobre el fondo */
    div, p, h1, h2, h3, label {
        color: white !important;
    }
    </style>
""", unsafe_allow_html=True)
# ==============================================================================
# 1. SEGURIDAD: DEFINICIÓN DE USUARIOS
# ==============================================================================
USUARIOS_AUTORIZADOS = {
    "CONC5": "12345", "CORCOL": "CORCOLONC3", "COMCH": "12345678",
    "COMAR": "hex123", "COMDA": "hex123", "COMCHEP": "hex123",
    "CEVIBO": "hex123", "COMSAM": "hex123", "ALISJHON": "199432", "ISMAEL SAMUDIO": "20626"
}

def login():
    st.markdown("""
        <style>
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        </style>
    """, unsafe_allow_html=True)
    
    st.markdown("""
        <style>
        .stApp { background-color: #0a0e17; }
        h1, label { color: #ffffff !important; }
        </style>
    """, unsafe_allow_html=True)
    st.title("🔐 DASHBOARD C.O.N - C5")
    st.markdown('<p class="author-text">DESARROLLADO POR= CABO 1° ELMER RODRIGUEZ</p>', unsafe_allow_html=True)
    usuario = st.text_input("Usuario del Centro:")
    clave = st.text_input("Contraseña:", type="password")
    if st.button("Ingresar"):
        if usuario in USUARIOS_AUTORIZADOS and USUARIOS_AUTORIZADOS[usuario] == clave:
            st.session_state.autenticado = True
            st.session_state.usuario = usuario
            st.rerun()
        else:
            st.error("Credenciales inválidas")

if "autenticado" not in st.session_state: st.session_state.autenticado = False

if not st.session_state.autenticado:
    login()
    st.stop()

# ==============================================================================
# 1. CONFIGURACIÓN, FUNCIONES DE LIMPIEZA Y MEDIDORES (GAUGES)
# ==============================================================================
st.set_page_config(
    page_title="S-Portal Hexagon | Traffic Center", 
    layout="wide",
    initial_sidebar_state="expanded"
)
    
st.markdown("""
    <style>
    #MainMenu {visibility: visible;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Estilo Base */
    .stApp { background-color: #0a0e17; }
    h1, h2, h3, span, p, label { color: #ffffff !important; }
    
    .stMetric { 
        background: rgba(255, 255, 255, 0.05); 
        border: 1px solid #00ebff; 
        border-radius: 10px; 
        padding: 10px; 
    }

    /* CONTENEDOR NEÓN GLOBAL ROTATIVO */
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

    /* EFECTO CINTA DE NEÓN FLUIDA ALREDEDOR DEL TÍTULO */
    .neon-title-container {
        position: relative;
        border-radius: 12px;
        padding: 3px; 
        background: #0d121f;
        overflow: hidden;
        margin-bottom: 1.5rem;z
        box-shadow: 0 0 20px rgba(0, 235, 255, 0.2);
    }
    
    .neon-title-container::before {
        content: '';
        position: absolute;
        top: -150%;
        left: -150%;
        width: 400%;
        height: 400%;
        background: conic-gradient(
            from 0deg,
            #00ffff 0%,
            #0077ff 25%,
            #001133 50%,
            #0077ff 75%,
            #00ffff 100%
        );
        animation: rotate-neon 4s linear infinite;
        z-index: 0;
    }

    .neon-title-inner {
        position: relative;
        background: #0d121f; 
        border-radius: 9px;
        padding: 22px;
        z-index: 1;
        text-align: center;
    }

    .neon-title-inner h1 {
        margin: 0;
        font-size: 32px;
        font-weight: 800;
        letter-spacing: 1px;
        text-transform: uppercase;
        background: linear-gradient(45deg, #ffffff, #00ebff);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        display: inline-block;
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

    .author-text { color: #00ebff !important; font-size: 14px; font-style: italic; margin-top: -5px; margin-bottom: 20px; text-align: center; }
    
    .map-overlay-total {
        position: relative;
        top: 60px; left: 20px;
        background: rgba(10, 14, 23, 0.85); border: 2px solid #00ebff;
        padding: 10px 20px; border-radius: 10px; z-index: 100;
        width: fit-content; margin-bottom: -70px;
    }

    @media (max-width: 768px) {
        .neon-title-inner h1 { font-size: 22px !important; }
        .neon-inner-content p { font-size: 22px !important; }
        .map-overlay-total { position: relative; top: 10px; left: 10px; margin-bottom: 10px; width: 90%; }
        .stPlotlyChart { height: 350px !important; }
    }
    </style>
""", unsafe_allow_html=True)

# ==============================================================================
# BARRA LATERAL DE USUARIO (Cerrar Sesión)
# ==============================================================================
with st.sidebar:
    st.write("---")
    st.write(f"👤 Usuario: **{st.session_state.usuario.upper()}**")
    if st.button("Cerrar Sesión"):
        st.session_state.autenticado = False
        st.rerun()
    st.write("---")

# --- FUNCIÓN DE LIMPIEZA DE NÚMEROS ---
def clean_num(val):
    if pd.isna(val): return 0
    if isinstance(val, (int, float)):
        if val < 1000 and val % 1 != 0: return int(round(val * 1000))
        return int(val)
    val_str = str(val).strip().replace(' ', '')
    if not val_str: return 0
    try:
        val_str = val_str.replace('.', '')
        return int(val_str)
    except ValueError:
        try: return int(float(val_str))
        except ValueError: return 0

# --- FUNCIÓN DE GAUGES ---
def create_gauge(value, title, color, is_timer=False):
    suffix = " seg" if is_timer else (" h" if value >= 60 else " min")
    display_val = value / 60 if (not is_timer and suffix == " h") else value
    fig = go.Figure(go.Indicator(
        mode = "gauge+number", value = display_val,
        title = {'text': title, 'font': {'size': 14, 'color': "white"}},
        number = {'suffix': suffix, 'font': {'color': "white"}},
        gauge = {'axis': {'range': [0, 60 if is_timer else max(60, display_val * 1.5)], 'tickcolor': "white"}, 'bar': {'color': color}}
    ))
    fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', height=200, margin=dict(l=20, r=20, t=40, b=20))
    return fig

# ==============================================================================
# 2. SISTEMA DE RECARGA AUTOMÁTICA
# ==============================================================================
if 'last_update' not in st.session_state:
    st.session_state.last_update = time.time()

elapsed = int(time.time() - st.session_state.last_update)
remaining = max(0, 60 - elapsed)

if remaining <= 0:
    st.session_state.last_update = time.time()
    st.rerun()

# ==============================================================================
# 3. CARGA DE DATOS Y MAPEO TÁCTICO
# ==============================================================================
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
            df['MES_NOMBRE'] = df['FECHA_DT'].dt.strftime('%B').str.upper()
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
        
        map_tactico_raw = {
            'Aprehensión de Menor por Alerta de Custodia': 'CAPTURAS', 'Ciudadana Aprehendida por Violencia Doméstica': 'CAPTURAS',
            'Ciudadano Aprehendido': 'CAPTURAS', 'Ciudadano Aprehendido por Inviolabilidad Del Domicilio': 'CAPTURAS',
            'Ciudadano Aprehendido por Libertad Vigilada': 'CAPTURAS', 'Ciudadano Aprehendido con Accesorio De Arma De Fuego': 'CAPTURAS',
            'Ciudadano Aprehendido con Arma Blanca': 'CAPTURAS', 'Ciudadano Aprehendido con Arma de Fuego': 'CAPTURAS',
            'Ciudadano Aprehendido con Sustancias Ilícitas': 'CAPTURAS', 'Ciudadano Aprehendido por Agresiones Fisicas': 'CAPTURAS',
            'Ciudadano Aprehendido por Agresiones Verbales': 'CAPTURAS', 'Ciudadano Aprehendido por Alteración De La Convivencia Pacífica': 'CAPTURAS',
            'Ciudadano Aprehendido por Consumo de Licor en Vía Pública': 'CAPTURAS', 'Ciudadano Aprehendido por Daño A La Prop. Privada': 'CAPTURAS',
            'Ciudadano Aprehendido por Estafa Simple': 'CAPTURAS', 'Ciudadano Aprehendido por Falsificación De Documentos': 'CAPTURAS',
            'Ciudadano Aprehendido por Falsificación De Monedas': 'CAPTURAS', 'Ciudadano Aprehendido por Hurto': 'CAPTURAS',
            'Ciudadano Aprehendido por Hurto A local Comercial': 'CAPTURAS', 'Ciudadano Aprehendido por Hurto A Propiedad': 'CAPTURAS',
            'Ciudadano Aprehendido por Hurto A Residencia': 'CAPTURAS', 'Ciudadano Aprehendido por Hurto de Accesorio De Vehículo': 'CAPTURAS',
            'Ciudadano Aprehendido por Hurto De Vehículo': 'CAPTURAS', 'Ciudadano Aprehendido por Hurto Simple A Persona': 'CAPTURAS',
            'Ciudadano Aprehendido por Hurto Simple a Propiedad': 'CAPTURAS', 'Ciudadano Aprehendido por Intento de Hurto': 'CAPTURAS',
            'Ciudadano Aprehendido por Intento De Violación': 'CAPTURAS', 'Ciudadano Aprehendido por Lesiones Personales': 'CAPTURAS',
            'Ciudadano Aprehendido por Lesiones Personales Con Arma Blanca': 'CAPTURAS', 'Ciudadano Aprehendido por Maltrato De Niños(As)-Adolescentes': 'CAPTURAS',
            'Ciudadano Aprehendido por No Portar Documento de Identidad Personal': 'CAPTURAS', 'Ciudadano Aprehendido por Oficio de Captura': 'CAPTURAS',
            'Ciudadano Aprehendido por Oficio de Conducción': 'CAPTURAS', 'Ciudadano Aprehendido por Privación De Libertad': 'CAPTURAS',
            'Ciudadano Aprehendido por Quebrantamiento De Boleta De Protección': 'CAPTURAS', 'Ciudadano Aprehendido por Riña o Pelea': 'CAPTURAS',
            'Ciudadano Aprehendido por Robo A local Comercial': 'CAPTURAS', 'Ciudadano Aprehendido por Robo A Persona Con Arma De Fuego': 'CAPTURAS',
            'Ciudadano Aprehendido por Robo A Propiedad': 'CAPTURAS', 'Ciudadano Aprehendido por Robo de Vehículo (Alerta Temprana)': 'CAPTURAS',
            'Ciudadano Aprehendido por Robo Simple (carterista)': 'CAPTURAS', 'Ciudadano Aprehendido por Robo Simple a Persona': 'CAPTURAS',
            'Ciudadano Aprehendido por Subrogado Penal': 'CAPTURAS', 'Ciudadano Aprehendido por Supuesta Vinculación A Delito': 'CAPTURAS',
            'Ciudadano Aprehendido por Violencia Doméstica': 'CAPTURAS', 'Ciudadano Capturado por Alerta Penitenciaria': 'CAPTURAS',
            'Ciudadano Notificado por Oficio de Citación': 'CAPTURAS', 'Menor Infractor por Hurto': 'CAPTURAS', 'Menor Infractor por Robo': 'CAPTURAS',
            'Arma de Fuego - Decomiso - Escopeta': 'RECUPERACIONES', 'Arma de Fuego - Decomiso - Fusil': 'RECUPERACIONES',
            'Arma de Fuego - Decomiso - Pistola': 'RECUPERACIONES', 'Arma de Fuego - Decomiso - Revolver': 'RECUPERACIONES',
            'Arma de Fuego - Decomiso - Rifle': 'RECUPERACIONES', 'Arma de Fuego - Hallazgo - Escopeta': 'RECUPERACIONES',
            'Arma de Fuego - Hallazgo - Fusil': 'RECUPERACIONES', 'Arma de Fuego - Hallazgo - Pistola': 'RECUPERACIONES',
            'Arma de Fuego - Hallazgo - Revolver': 'RECUPERACIONES', 'Arma de Fuego - Replica Decomiso': 'RECUPERACIONES',
            'Arma de Fuego - Replica Hallazgo': 'RECUPERACIONES', 'Articulo de Dudosa Procedencia': 'RECUPERACIONES',
            'Articulo Recuperados': 'RECUPERACIONES', 'Decomiso de Articulos Prohibidos': 'RECUPERACIONES',
            'Decomiso de Cajetillas Cigarrillos': 'RECUPERACIONES', 'Decomiso de Sustancia Ilícita': 'RECUPERACIONES',
            'Hallazgo de Sustancia Ilícita': 'RECUPERACIONES', 'Recuperación de Articulos': 'RECUPERACIONES',
            'Recuperación de Menor Evadido': 'RECUPERACIONES', 'Remoción de Vehículo en Grúa': 'RECUPERACIONES',
            'Vehículo Recuperado': 'RECUPERACIONES', 'Vehículo Recuperado por Apropiación Indebida': 'RECUPERACIONES',
            'Vehículo Recuperado por Hurto (Alerta Temprana)': 'RECUPERACIONES', 'Vehículo Recuperado por Oficio de Hurto': 'RECUPERACIONES',
            'Vehículo Recuperado por Oficio de Robo': 'RECUPERACIONES', 'Vehículo Recuperado por Robo (Alerta Temprana)': 'RECUPERACIONES',
            'Atención de Atropello': 'SEGURIDAD VIAL', 'Atención de Atropello con victima fatal': 'SEGURIDAD VIAL',
            'Atención de Caida de Vehiculo en la Cuneta': 'SEGURIDAD VIAL', 'Atención de Choque con Objeto Fijo': 'SEGURIDAD VIAL',
            'Atención de Colisión de Alto Impacto': 'SEGURIDAD VIAL', 'Atención de Colisión menor': 'SEGURIDAD VIAL',
            'Atención de Colisión multiple': 'SEGURIDAD VIAL', 'Atención de Colision y fuga': 'SEGURIDAD VIAL',
            'Atención de Colision y vuelco': 'SEGURIDAD VIAL', 'Atención de Derrame de Combustible': 'SEGURIDAD VIAL',
            'Atención de Derrape de Motorizado': 'SEGURIDAD VIAL', 'Atención de Derrape de Motorizado con Víctima Fatal': 'SEGURIDAD VIAL',
            'Atención de Triple Colisión': 'SEGURIDAD VIAL', 'Atención de Vuelco': 'SEGURIDAD VIAL',
            'Infracción por Ceder el Manejo a Persona No Autorizada': 'SEGURIDAD VIAL', 'Infracción por Circular en Vía Contraria': 'SEGURIDAD VIAL',
            'Infracción por Conducir a Velocidad Superior al Limite': 'SEGURIDAD VIAL', 'Infracción por Conducir con Aliento Alcohólico': 'SEGURIDAD VIAL',
            'Infracción por Conducir de Forma Desordenada': 'SEGURIDAD VIAL', 'Infracción por Conducir por el Carril Indebido': 'SEGURIDAD VIAL',
            'Infracción por Conductor en Estado de Embriaguez Comprobado': 'SEGURIDAD VIAL', 'Infracción por Estado Etilico': 'SEGURIDAD VIAL',
            'Infracción por Daño a la Propiedad': 'SEGURIDAD VIAL', 'Infracción por Desatender lineas de no pare': 'SEGURIDAD VIAL',
            'Infracción por Desatender señales': 'SEGURIDAD VIAL', 'Infracción por Emitir Gases, Ruidos o Sonidos Excesivos': 'SEGURIDAD VIAL',
            'Infracción por Hablar por Teléfono Celular': 'SEGURIDAD VIAL', 'Infracción por Licencia Vencida': 'SEGURIDAD VIAL',
            'Infracción por Licencia no Adecuada': 'SEGURIDAD VIAL', 'Infracción Nunca ha Sacado Licencia': 'SEGURIDAD VIAL',
            'Infracción por Luces Inadecuadas': 'SEGURIDAD VIAL', 'Infracción por Negarse a Prueba de Alcoholemia': 'SEGURIDAD VIAL',
            'Infracción por No portar licencia': 'SEGURIDAD VIAL', 'Infracción por No utilizar el Cinturón': 'SEGURIDAD VIAL',
            'Infracción por Papel ahumado no Autorizado': 'SEGURIDAD VIAL', 'Infracción por Pasar Semáforo en Rojo': 'SEGURIDAD VIAL',
            'Infracción por Poliza Vencida': 'SEGURIDAD VIAL', 'Infracción por Portar Placa Diferente': 'SEGURIDAD VIAL',
            'Infracción por Prestar el Servicio en Ruta Distinta': 'SEGURIDAD VIAL', 'Infracción por Vehículo no Autorizado': 'SEGURIDAD VIAL',
            'Infracción por Realizar Giros Prohibidos': 'SEGURIDAD VIAL', 'Infracción por Sin Condiciones de Seguridad': 'SEGURIDAD VIAL',
            'Infracción por Sin Equipos de Seguridad': 'SEGURIDAD VIAL', 'Infracción por Exceso de Pasajero': 'SEGURIDAD VIAL',
            'Infracción por Vehículo sin Cinta Reflectiva': 'SEGURIDAD VIAL', 'Infracción por Vehículos mal Estacionados': 'SEGURIDAD VIAL',
            'Infracción por Remolcar sin Seguridad': 'SEGURIDAD VIAL', 'Restablecimiento de la Segurida Víal': 'SEGURIDAD VIAL',
            'Apoyo a Vehiculo de Valores Desperfectos': 'EMERGENCIAS', 'Apoyo al Ciudadano': 'EMERGENCIAS',
            'Apoyo al Ciudadano Brindar Seguridad': 'EMERGENCIAS', 'Apoyo al Ciudadano Cruce de Peatón': 'EMERGENCIAS',
            'Apoyo al Ciudadano para Reparar Vehículo': 'EMERGENCIAS', 'Apoyo al Ciudadano Reskate de Embarcacion': 'EMERGENCIAS',
            'Apoyo al Ciudadano Reskate de Persona': 'EMERGENCIAS', 'Atención Prehospitalaria BCBPA': 'EMERGENCIAS',
            'Atención Prehospitalaria CSS': 'EMERGENCIAS', 'Atención Prehospitalaria MINSACAPSI': 'EMERGENCIAS',
            'Atención Prehospitalaria Policía Nacional': 'EMERGENCIAS', 'Atención Prehospitalaria Privada': 'EMERGENCIAS',
            'Atención Prehospitalaria SUME 911': 'EMERGENCIAS', 'Coordinación con Atención Primaria': 'EMERGENCIAS',
            'Extinción de Incendio': 'EMERGENCIAS', 'Extinción del Conato de Incendio': 'EMERGENCIAS',
            'Proveedor': 'EMERGENCIAS', 'Rescate de Animal Domestico': 'EMERGENCIAS',
            'Rescate de Menor por Alerta AMBER': 'EMERGENCIAS', 'Rescate de Menor por Riego Social': 'EMERGENCIAS',
            'Rescate de Persona': 'EMERGENCIAS', 'Rescate de Vida y fauna Silvestre': 'EMERGENCIAS',
            'Restitución de Propiedad Extraviada': 'EMERGENCIAS', 'Traslado a Hospital': 'EMERGENCIAS',
            'Traslado a Hospital por BCBPA': 'EMERGENCIAS', 'Traslado a Hospital por CSS': 'EMERGENCIAS',
            'Traslado a Hospital por Policía Nacional': 'EMERGENCIAS', 'Traslado a Hospital por Serv. Privado': 'EMERGENCIAS',
            'Traslado a Hospital por SUME 911': 'EMERGENCIAS'
        }

        def normalizar_texto(texto):
            if not texto or pd.isna(texto): return ""
            texto = str(texto).strip().lower()
            return "".join(c for c in unicodedata.normalize('NFKD', texto) if not unicodedata.combining(c))

        map_tactico = {normalizar_texto(k): v for k, v in map_tactico_raw.items()}

        def asignar_grupo(row):
            for col in cols_pos:
                val_raw = str(row[col]).strip() if pd.notna(row[col]) else ""
                if val_raw:
                    val_norm = normalizar_texto(val_raw)
                    if val_norm in map_tactico: return map_tactico[val_norm]
            return "EMERGENCIAS"

        df['GRUPO_TACTICO'] = df.apply(asignar_grupo, axis=1)
        return df[df['T_POS_COUNT'] > 0].copy()
    except: return None

# ==============================================================================
# 4. DISPOSICIÓN DE LA INTERFAZ DE USUARIO (DASHBOARD)
# ==============================================================================
df_raw = load_full_data()

if df_raw is not None:
    with st.sidebar:
        st.header("🔎 Fechas y Horas")
        f1 = st.date_input("Desde:", df_raw['FECHA_DT'].min().date())
        f2 = st.date_input("Hasta:", df_raw['FECHA_DT'].max().date())
        h1 = st.selectbox("Hora Inicial:", list(range(24)), index=0)
        h2 = st.selectbox("Hora Final:", list(range(24)), index=23)
        st.plotly_chart(create_gauge(remaining, "ACTUALIZACIÓN", "#00ebff", is_timer=True), use_container_width=True)

    df = df_raw[(df_raw['FECHA_DT'].dt.date >= f1) & (df_raw['FECHA_DT'].dt.date <= f2) & 
                (df_raw['HORA_NUM'] >= h1) & (df_raw['HORA_NUM'] <= h2)].copy()

    # --- TÍTULO ---
    st.markdown("""
        <div class="neon-title-container">
            <div class="neon-title-inner">
                <h1>🛡️ Centro de Operación Nacional | Datos Positivos-C.O.N-C5</h1>
            </div>
        </div>
    """, unsafe_allow_html=True)
    st.markdown('<p class="author-text">DESARROLLADO POR= CABO 1° ELMER RODRIGUEZ</p>', unsafe_allow_html=True)

    # ==============================================================================
# 1. CONFIGURACIÓN (Intacta)
# ==============================================================================
st.set_page_config(page_title="S-Portal Hexagon | Traffic Center", layout="wide")

st.markdown("""
    <style>
    #MainMenu {visibility: visible;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stApp { background-color: #0a0e17; }
    h1, h2, h3, span, p, label { color: #ffffff !important; }
    </style>
""", unsafe_allow_html=True)

# ==============================================================================
# 2. CARGA DE DATOS (Intacta)
# ==============================================================================
URL_HOJA_CSV = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRJjM8N55oQ9GLvCm72Jz8kbJpqze5ouhbBudOkYACwCIDGq9KmwLYX9Tz9lPmDPYEBzefNXqIE13PM/pub?gid=2008069627&single=true&output=csv"

@st.cache_data(ttl=60)
def load_traffic_only():
    try:
        df_c = pd.read_csv(URL_HOJA_CSV, header=None, dtype=str)
        df_con = df_c.iloc[6:12].copy()
        df_con.columns = [str(x).strip() for x in df_c.iloc[5]]
        df_con['CENTRO_ID'] = 'CON-C5'
        df_cor = df_c.iloc[37:43].copy()
        df_cor.columns = [str(x).strip() for x in df_c.iloc[36]]
        df_cor['CENTRO_ID'] = 'CORCOL'
        
        df_all = pd.concat([df_con, df_cor], ignore_index=True)
        df_all.columns = df_all.columns.str.replace(r'\s+', ' ', regex=True).str.strip()
        
        cols_convertir = ['Presentadas', 'Contestadas', 'Abandonadas', 'Orientación', 'Ociosa', 
                          'Contestadas Despues de 05 seg.', 'Abandonadas Despues de 05 seg.']
        for col in cols_convertir:
            if col in df_all.columns:
                df_all[col] = pd.to_numeric(df_all[col].str.replace('.', '', regex=False), errors='coerce').fillna(0).astype(int)
        return df_all
    except: return None

df_traffic = load_traffic_only()

# ==============================================================================
# 3. LÓGICA DE CÁLCULO (Ajustada para AMBOS)
# ==============================================================================
if df_traffic is not None and not df_traffic.empty:
    c_filt_1, c_filt_2, _ = st.columns([3, 2, 1])
    
    with c_filt_1:
        centro_filtro = st.radio("Centro:", ["AMBOS CENTROS (Sumados)", "CON-C5", "CORCOL"], horizontal=True)
    with c_filt_2:
        mes_seleccionado = st.selectbox("Período:", ["TODOS LOS MESES"] + list(df_traffic.iloc[:,0].unique()))

    # Filtramos sin borrar datos
    df_t = df_traffic if mes_seleccionado == "TODOS LOS MESES" else df_traffic[df_traffic.iloc[:,0] == mes_seleccionado]
    
    # Lógica central: subset captura todo si es "AMBOS", o solo el centro seleccionado
    if centro_filtro == "AMBOS CENTROS (Sumados)":
        subset = df_t
    else:
        subset = df_t[df_t['CENTRO_ID'] == centro_filtro]

    # CÁLCULO DE LA FÓRMULA EXACTA
    C = subset['Contestadas'].sum()
    A = subset['Abandonadas'].sum()
    C5 = subset['Contestadas Despues de 05 seg.'].sum()
    A5 = subset['Abandonadas Despues de 05 seg.'].sum()
    
    divisor = (C + A)
    avg_sla = (((C + A) - (C5 + A5)) / divisor * 100) if divisor > 0 else 0.0

    # GRÁFICOS (Estructura intacta)
    df_res = subset.agg({'Presentadas':'sum', 'Contestadas':'sum', 'Abandonadas':'sum', 'Orientación':'sum', 'Maliciosa':'sum'})
    
    c_grafico, c_sla_box = st.columns([2, 1])
    with c_grafico:
        fig = go.Figure(data=[go.Bar(
            x=['PRESENTADAS', 'CONTESTADAS', 'ABANDONADAS', 'ORIENTACIÓN', 'OCIOSA'],
            y=[df_res['Presentadas'], df_res['Contestadas'], df_res['Abandonadas'], df_res['Orientación'], df_res['Ociosa']],
            text=[f"{val:,.0f}" for val in [df_res['Presentadas'], df_res['Contestadas'], df_res['Abandonadas'], df_res['Orientación'], df_res['Ociosa']]],
            textposition='outside',
            marker_color=["#00ebff", "#00ffaa", "#ff4b4b", "#ffaa00", "#555555"]
        )])
        fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color="white"), yaxis=dict(showticklabels=False), margin=dict(t=40, b=10, l=10, r=10))
        st.plotly_chart(fig, use_container_width=True)
        
    with c_sla_box:
        col = "#00ffaa" if avg_sla >= 90 else ("#ffaa00" if avg_sla >= 80 else "#ff4b4b")
        st.markdown(f"""<div style="background: #0d121f; border: 1px solid #00ebff; border-radius: 8px; height: 360px; display: flex; flex-direction: column; justify-content: center; align-items: center;">
            <p style="margin: 0; font-size: 14px; color: #ffffff;">% NIVEL DE SERVICIO</p>
            <h1 style="margin: 20px 0 0 0; font-size: 56px; color: #ffffff; text-shadow: 0 0 12px {col};">{avg_sla:.2f}%</h1>
        </div>""", unsafe_allow_html=True)

   # =========================================================================
    # SECCIÓN: COMPONENTES DEL DASHBOARD
    # =========================================================================
    c_m1, c_m2 = st.columns(2) # Ajusta esto a tu sintaxis real de Streamlit
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

    # MAPA TÁCTICO POR PROVINCIAS
    st.subheader("📍 MAPA TÁCTICO DETALLADO DE INCIDENCIAS")
    if 'PROVINCIA' in df.columns:
        cols_p = [c for c in df.columns if 'RESULTADO POSITIVO' in c.upper()]
        df_long = pd.melt(df, id_vars=['PROVINCIA'], value_vars=cols_p, value_name='Tipo').dropna()
        top_details = df_long.groupby('PROVINCIA').apply(lambda g: "<br>".join([f"• {t}: {v}" for t, v in g['Tipo'].value_counts().nlargest(5).items()])).reset_index(name='DETALLE_TOP')
        prov_stats = df.groupby('PROVINCIA')['T_POS_COUNT'].sum().reset_index().sort_values('T_POS_COUNT', ascending=True)
        prov_stats = prov_stats.merge(top_details, on='PROVINCIA', how='left')
        
        coords = {'Panamá':[8.98,-79.52], 'Chiriquí':[8.43,-82.43], 'Colón':[9.35,-79.9], 'Panamá Oeste':[8.88,-79.78], 'Coclé':[8.51,-80.35], 'Veraguas':[8.1,-80.97], 'Los Santos':[7.93,-80.48], 'Herrera':[7.96,-80.7], 'Darién':[8.4,-77.91], 'Bocas del Toro':[9.33,-82.24], 'Comarca Ngäbe-Buglé':[8.41, -81.75]}
        prov_stats['lat'] = prov_stats['PROVINCIA'].map(lambda x: coords.get(x, [8.5, -80.0])[0])
        prov_stats['lon'] = prov_stats['PROVINCIA'].map(lambda x: coords.get(x, [8.5, -80.0])[1])
        
        c_map, c_rank = st.columns([2, 1])
        with c_map:
            st.markdown(f'<div class="map-overlay-total"><small style="color:#00ebff;">TOTAL POSITIVOS</small><br><span style="font-size:24px; font-weight:bold;">{int(df["T_POS_COUNT"].sum()):}</span></div>', unsafe_allow_html=True)
            fig_m = px.scatter_mapbox(prov_stats, lat='lat', lon='lon', size='T_POS_COUNT', color='T_POS_COUNT', color_continuous_scale="Darkmint", size_max=55, zoom=7.2, center=dict(lat=8.5, lon=-80.5), hover_name='PROVINCIA', hover_data={'lat':False, 'lon':False, 'T_POS_COUNT':True, 'DETALLE_TOP':True})
            fig_m.update_layout(mapbox_style="carto-darkmatter", margin={"r":0,"t":0,"l":0,"b":0}, paper_bgcolor='rgba(0,0,0,0)', coloraxis_showscale=False)
            st.plotly_chart(fig_m, use_container_width=True)
        with c_rank:
            st.plotly_chart(px.bar(prov_stats, x='T_POS_COUNT', y='PROVINCIA', orientation='h', text='T_POS_COUNT', color='T_POS_COUNT', color_continuous_scale='Tealgrn').update_layout(showlegend=False, coloraxis_showscale=False, paper_bgcolor='rgba(0,0,0,0)', font=dict(color="white"), height=400), use_container_width=True)

    # GRÁFICOS DE ROSA
    st.markdown("---")
    cp1, cp2, cp3 = st.columns(3)
    with cp1: 
        st.plotly_chart(px.pie(df, names='CANAL DE ENTRADA', values='T_POS_COUNT', title="Positivos por Canales", hole=0.5, color_discrete_map={"CLL-104": "#FF1493", "Video Vigilancia": "#FF69B4", "Radio Frecuencia": "#FFB6C1"}), use_container_width=True)
    with cp2: 
        st.plotly_chart(px.pie(df, names='CENTRO', values='T_POS_COUNT', title="Positivos por Centros", hole=0.5, color_discrete_sequence=px.colors.sequential.Tealgrn), use_container_width=True)
    with cp3: 
        st.plotly_chart(px.pie(df, names='GRUPO_TACTICO', values='T_POS_COUNT', title="Distribución por Grupo Táctico", hole=0.5, color_discrete_sequence=px.colors.qualitative.G10), use_container_width=True)
        
    st.subheader("📋 DETALLE: POSITIVOS POR CENTROS")
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
        st.subheader("🚔 ZONA POLICIAL O ENLACE")
        col_zp = next((c for c in df.columns if any(k in c.upper() for k in ['ZONA', 'ZP', 'SERVICIO'])), None)
        if col_zp:
            zp_s = df.groupby(col_zp)['T_POS_COUNT'].sum().reset_index().sort_values('T_POS_COUNT', ascending=False)
            st.dataframe(pd.concat([zp_s, pd.DataFrame({col_zp:['TOTAL GENERAL'], 'T_POS_COUNT':[zp_s['T_POS_COUNT'].sum()]})]), use_container_width=True, height=400, hide_index=True)

    st.markdown("---")
    st.subheader("📊 ANÁLISIS POR UNIDAD Y TIEMPO")
    c_mes, c_vv, c_desp = st.columns(3)
    with c_mes:
        if 'MES_NOMBRE' in df.columns:
            st.write("📅 Positivos por Meses")
            m_s = df.groupby(['MES_NOMBRE', 'MES_NUM'])['T_POS_COUNT'].sum().reset_index().sort_values('MES_NUM', ascending=False)
            fig_m_b = px.bar(m_s, x='T_POS_COUNT', y='MES_NOMBRE', orientation='h', text='T_POS_COUNT', color='T_POS_COUNT', color_continuous_scale='Tealgrn')
            fig_m_b.update_layout(showlegend=False, coloraxis_showscale=False, paper_bgcolor='rgba(0,0,0,0)', font=dict(color="white"), height=400)
            st.plotly_chart(fig_m_b, use_container_width=True)
    with c_vv:
        col_vv = next((c for c in df.columns if 'UNIDAD DE VV' in c.upper() or 'VV/104' in c.upper()), None)
        if col_vv:
            st.write("📟 Unidad de VV/104")
            df[col_vv] = df[col_vv].fillna("SIN ASIGNAR").astype(str)
            vv_s = df.groupby([col_vv, 'CENTRO']).size().reset_index(name='E').sort_values('E', ascending=False)
            st.dataframe(pd.concat([vv_s, pd.DataFrame({col_vv:['TOTAL GENERAL'], 'CENTRO':['-'], 'E':[vv_s['E'].sum()]})]), use_container_width=True, hide_index=True)
    with c_desp:
        col_dp = next((c for c in df.columns if 'UNIDAD DE DESPACHO' in c.upper()), None)
        if col_dp:
            st.write("🚨 Unidad de Despacho")
            df[col_dp] = df[col_dp].fillna("SIN ASIGNAR").astype(str)
            dp_s = df.groupby([col_dp, 'CENTRO']).size().reset_index(name='E').sort_values('E', ascending=False)
            st.dataframe(pd.concat([dp_s, pd.DataFrame({col_dp:['TOTAL GENERAL'], 'CENTRO':['-'], 'E':[dp_s['E'].sum()]})]), use_container_width=True, hide_index=True)
    
    time.sleep(1)
    st.rerun()
