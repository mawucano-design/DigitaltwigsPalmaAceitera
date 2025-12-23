import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import io
import tempfile
import os
import zipfile
import matplotlib.pyplot as plt

# Google Earth Engine
import ee

# Geoespacial
import geopandas as gpd
from shapely.geometry import Polygon, Point, mapping
import folium
from folium import plugins
from streamlit_folium import st_folium

# ============================================================================
# INICIALIZAR GOOGLE EARTH ENGINE
# ============================================================================
try:
    ee.Initialize(opt_url='https://earthengine.googleapis.com')
except Exception as e:
    st.error(f"Error al inicializar Google Earth Engine: {e}")
    st.stop()

# ============================================================================
# CONFIGURACIÓN DE LA PÁGINA
# ============================================================================
st.set_page_config(
    page_title="🌴 Gemelo Digital - Palma Aceitera",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown(
    '<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">',
    unsafe_allow_html=True
)

# ============================================================================
# CSS
# ============================================================================
st.markdown("""
<style>
    .stApp { background-color: #f8f9fa; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
    .main-header {
        background: linear-gradient(90deg, #1B5E20 0%, #2E7D32 100%);
        padding: 1.5rem 2rem;
        color: white;
        margin-bottom: 1.5rem;
        border-radius: 0 0 15px 15px;
        box-shadow: 0 4px 12px rgba(27, 94, 32, 0.3);
    }
    .metric-card {
        background: white;
        border-radius: 10px;
        padding: 1.25rem;
        box-shadow: 0 3px 10px rgba(0, 0, 0, 0.08);
        border-left: 4px solid #2E7D32;
        margin-bottom: 1rem;
    }
    .metric-title { color: #666; font-size: 0.85rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 0.5rem; }
    .metric-value { color: #2E7D32; font-size: 1.8rem; font-weight: 700; margin: 0; line-height: 1.2; }
    .stButton > button {
        background-color: #1B5E20;
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.7rem 1.5rem;
        font-weight: 600;
        font-size: 1rem;
        width: 100%;
    }
    .stButton > button:hover { background-color: #0D3B1A; }
</style>
""", unsafe_allow_html=True)

# ============================================================================
# FUNCIONES KML
# ============================================================================
def procesar_archivo_kml(uploaded_file):
    """Procesa KML o KMZ."""
    try:
        suffix = '.kmz' if uploaded_file.name.lower().endswith('.kmz') else '.kml'
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            if suffix == '.kmz':
                with zipfile.ZipFile(uploaded_file) as kmz:
                    kml_file = [f for f in kmz.namelist() if f.endswith('.kml')][0]
                    tmp.write(kmz.read(kml_file))
            else:
                tmp.write(uploaded_file.getvalue())
            tmp_path = tmp.name

        gdf = gpd.read_file(tmp_path, driver='KML')
        os.unlink(tmp_path)

        if gdf.empty:
            st.error("Archivo sin geometrías válidas.")
            return None

        if gdf.crs is None:
            gdf.set_crs(epsg=4326, inplace=True)
        else:
            gdf = gdf.to_crs(epsg=4326)

        gdf = gdf[gdf.is_valid & ~gdf.is_empty]
        if gdf.empty:
            st.error("No hay geometrías válidas tras limpieza.")
            return None

        gdf_proj = gdf.to_crs(epsg=3857)
        gdf['area_ha'] = gdf_proj.area / 10000
        return gdf

    except Exception as e:
        st.error(f"Error procesando KML: {str(e)}")
        return None

# ============================================================================
# FUNCIONES DE GOOGLE EARTH ENGINE
# ============================================================================
INDICES = {
    'NDVI': lambda img: img.normalizedDifference(['B8', 'B4']).rename('NDVI'),
    'GNDVI': lambda img: img.normalizedDifference(['B8', 'B3']).rename('GNDVI'),
    'EVI': lambda img: img.expression(
        '2.5 * ((NIR - RED) / (NIR + 6 * RED - 7.5 * BLUE + 1))',
        {'NIR': img.select('B8'), 'RED': img.select('B4'), 'BLUE': img.select('B2')}
    ).rename('EVI'),
    'SAVI': lambda img: img.expression(
        '((NIR - RED) / (NIR + RED + 0.5)) * 1.5',
        {'NIR': img.select('B8'), 'RED': img.select('B4')}
    ).rename('SAVI'),
    'MSAVI': lambda img: img.expression(
        '(2 * NIR + 1 - ((2 * NIR + 1)**2 - 8 * (NIR - RED))**0.5) / 2',
        {'NIR': img.select('B8'), 'RED': img.select('B4')}
    ).rename('MSAVI'),
    'NDMI': lambda img: img.normalizedDifference(['B8', 'B11']).rename('NDMI'),
    'NDRE': lambda img: img.normalizedDifference(['B8', 'B5']).rename('NDRE'),
    'SATVI': lambda img: img.expression(
        '((SWIR - RED) / (SWIR + RED + 0.5)) * 1.5 - (SWIR / 2)',
        {'SWIR': img.select('B11'), 'RED': img.select('B4')}
    ).rename('SATVI')
}

def obtener_indice_gee(poligono_geojson, indice_nombre, fecha_inicio, fecha_fin):
    try:
        geometry = ee.Geometry(poligono_geojson)
        s2 = (ee.ImageCollection('COPERNICUS/S2_SR')
              .filterBounds(geometry)
              .filterDate(fecha_inicio, fecha_fin)
              .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 20))
              .median()
              .clip(geometry))

        if indice_nombre not in INDICES:
            raise ValueError(f"Índice {indice_nombre} no soportado")

        indice_img = INDICES[indice_nombre](s2)
        min_max = indice_img.reduceRegion(
            reducer=ee.Reducer.minMax(),
            geometry=geometry,
            scale=10,
            maxPixels=1e9
        ).getInfo()

        vmin = min_max.get(f"{indice_nombre}_min", -1)
        vmax = min_max.get(f"{indice_nombre}_max", 1)

        url = indice_img.getThumbUrl({
            'min': vmin,
            'max': vmax,
            'palette': 'red,yellow,green',
            'dimensions': 512
        })

        return url, vmin, vmax
    except Exception as e:
        st.error(f"Error GEE en {indice_nombre}: {str(e)}")
        return None, 0, 1

# ============================================================================
# FUNCIONES AUXILIARES
# ============================================================================
CULTIVOS = {
    'PALMA ACEITERA': {
        'nitrogeno_optimo': 160,
        'fosforo_optimo': 60,
        'potasio_optimo': 200,
        'produccion_base': 25.0,
        'ph_optimo': 5.5
    }
}

MESES = [f"{datetime(2000, i, 1).strftime('%B').upper()}" for i in range(1,13)]

def generar_datos_edaficos(n_zonas, cultivo='PALMA ACEITERA'):
    np.random.seed(42)
    params = CULTIVOS[cultivo]
    df = pd.DataFrame({
        'id_zona': list(range(1, n_zonas + 1)),
        'nitrogeno': np.random.normal(params['nitrogeno_optimo'], 20, n_zonas).clip(50, 300),
        'fosforo': np.random.normal(params['fosforo_optimo'], 10, n_zonas).clip(20, 120),
        'potasio': np.random.normal(params['potasio_optimo'], 30, n_zonas).clip(100, 400),
        'ph': np.random.normal(params['ph_optimo'], 0.3, n_zonas).clip(4.0, 7.0),
        'materia_organica': np.random.uniform(2.0, 5.0, n_zonas),
    })
    df['indice_fertilidad'] = (
        (df['nitrogeno'] / params['nitrogeno_optimo'] * 0.25) +
        (df['fosforo'] / params['fosforo_optimo'] * 0.20) +
        (df['potasio'] / params['potasio_optimo'] * 0.20) +
        (df['materia_organica'] / 5.0 * 0.15) +
        (1 - abs(df['ph'] - params['ph_optimo']) / 3.0 * 0.20)
    ).clip(0.2, 0.95)
    df['categoria'] = pd.cut(df['indice_fertilidad'], 
                            bins=[0, 0.35, 0.5, 0.65, 0.8, 1], 
                            labels=['MUY BAJA', 'BAJA', 'MEDIA', 'BUENA', 'EXCELENTE'])
    df['potencial_cosecha'] = (params['produccion_base'] * df['indice_fertilidad']).round(1)
    return df

def crear_mapa_base(gdf):
    centroide = gdf.geometry.unary_union.centroid
    m = folium.Map(location=[centroide.y, centroide.x], zoom_start=14)
    folium.GeoJson(gdf).add_to(m)
    m.fit_bounds([[gdf.total_bounds[1], gdf.total_bounds[0]], [gdf.total_bounds[3], gdf.total_bounds[2]]])
    return m

# ============================================================================
# INTERFAZ
# ============================================================================
def mostrar_header():
    st.markdown("""
    <div class="main-header">
        <h1>🌱 GEMELO DIGITAL - PALMA ACEITERA</h1>
        <p>Plataforma de monitoreo con Sentinel-2, análisis edáfico y recomendaciones agronómicas</p>
    </div>
    """, unsafe_allow_html=True)

def main():
    mostrar_header()

    # Session state
    if 'gdf_poligono' not in st.session_state:
        st.session_state['gdf_poligono'] = None
    if 'analisis_ejecutado' not in st.session_state:
        st.session_state['analisis_ejecutado'] = False

    # Sidebar
    with st.sidebar:
        st.markdown("### 📁 CARGA DE POLÍGONO")
        uploaded_file = st.file_uploader("Sube KML/KMZ", type=['kml', 'kmz'])
        if uploaded_file:
            gdf = procesar_archivo_kml(uploaded_file)
            if gdf is not None:
                st.session_state['gdf_poligono'] = gdf
                st.success(f"✅ Cargado: {len(gdf)} polígono(s), {gdf['area_ha'].sum():.2f} ha")

        st.markdown("---")
        n_zonas = st.slider("Zonas de análisis", 4, 30, 12)
        mes_idx = st.selectbox("Mes de análisis", range(12), index=datetime.now().month-1, format_func=lambda x: MESES[x])
        fecha_fin = datetime(datetime.now().year, mes_idx+1, 1)
        fecha_inicio = fecha_fin - timedelta(days=30)

        if st.button("🚀 EJECUTAR ANÁLISIS", type="primary"):
            if st.session_state['gdf_poligono'] is None:
                st.error("Primero carga un polígono KML/KMZ")
            else:
                st.session_state['analisis_ejecutado'] = True
                st.session_state['n_zonas'] = n_zonas
                st.session_state['fecha_inicio'] = fecha_inicio.strftime('%Y-%m-%d')
                st.session_state['fecha_fin'] = fecha_fin.strftime('%Y-%m-%d')

    # Contenido principal
    if not st.session_state['analisis_ejecutado']:
        st.info("👆 Sube un polígono y haz clic en 'EJECUTAR ANÁLISIS'")
        if st.session_state['gdf_poligono'] is not None:
            st_folium(crear_mapa_base(st.session_state['gdf_poligono']), width=800, height=500)
        return

    # Ejecutar análisis
    gdf = st.session_state['gdf_poligono']
    n_zonas = st.session_state['n_zonas']
    fecha_inicio = st.session_state['fecha_inicio']
    fecha_fin = st.session_state['fecha_fin']

    # Datos edáficos
    df_edafico = generar_datos_edaficos(n_zonas)

    # Pestañas
    tabs = st.tabs([
        "📍 Base", "🌿 NDVI", "🌾 GNDVI", "🌎 EVI", "🍃 SAVI",
        "🌿 MSAVI", "💧 NDMI", "🔍 NDRE", "🏜️ SATVI", "📊 Dashboard"
    ])

    # Mapa base
    with tabs[0]:
        st_folium(crear_mapa_base(gdf), width=800, height=500)

    # Mapas de índices
    poligono_geojson = mapping(gdf.geometry.unary_union)
    for i, indice in enumerate(INDICES.keys(), start=1):
        with tabs[i]:
            st.subheader(f"Índice {indice}")
            with st.spinner(f"Consultando {indice} en Google Earth Engine..."):
                url, vmin, vmax = obtener_indice_gee(poligono_geojson, indice, fecha_inicio, fecha_fin)
                if url:
                    st.image(url, caption=f"{indice} ({fecha_inicio} a {fecha_fin})", use_column_width=True)
                    st.caption(f"Rango: [{vmin:.2f}, {vmax:.2f}]")
                else:
                    st.warning(f"No se pudo generar el mapa de {indice}")

    # Dashboard
    with tabs[-1]:
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            fert_prom = df_edafico['indice_fertilidad'].mean()
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-title">Fertilidad Promedio</div>
                <div class="metric-value">{fert_prom:.3f}</div>
            </div>
            """, unsafe_allow_html=True)
        with col2:
            st.metric("Área Total", f"{gdf['area_ha'].sum():.1f} ha")
        with col3:
            st.metric("Potencial Cosecha", f"{df_edafico['potencial_cosecha'].mean():.1f} t/ha")
        with col4:
            criticas = len(df_edafico[df_edafico['categoria'].isin(['BAJA', 'MUY BAJA'])])
            st.metric("Zonas Críticas", f"{criticas}")

        st.markdown("### Recomendaciones Agronómicas")
        for _, row in df_edafico.iterrows():
            if row['categoria'] in ['MUY BAJA', 'BAJA']:
                st.warning(f"Zona {row['id_zona']}: Fertilidad {row['categoria'].lower()}. Recomendación: Ajustar NPK y pH.")
            elif row['categoria'] == 'EXCELENTE':
                st.success(f"Zona {row['id_zona']}: Excelente estado. Mantener manejo actual.")

        st.markdown("### Datos Edáficos")
        st.dataframe(df_edafico.round(2), use_container_width=True)

if __name__ == "__main__":
    main()
