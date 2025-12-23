import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import io
import tempfile
import os
import geopandas as gpd
from shapely.geometry import Polygon, Point
import folium
from folium import plugins
from streamlit_folium import st_folium
import zipfile

# ============================================================================
# CONFIGURACIÓN DE LA PÁGINA
# ============================================================================
st.set_page_config(
    page_title="🌴 Analizador Cultivos Digital Twin",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Meta tag para prevenir errores de renderizado
st.markdown(
    '<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">',
    unsafe_allow_html=True
)

# ============================================================================
# CSS SIMPLIFICADO
# ============================================================================
st.markdown("""
<style>
    .stApp {
        background-color: #f8f9fa;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    
    .main-header {
        background: linear-gradient(90deg, #2E7D32 0%, #388E3C 100%);
        padding: 1.5rem 2rem;
        color: white;
        margin-bottom: 1.5rem;
        border-radius: 0 0 15px 15px;
        box-shadow: 0 4px 12px rgba(46, 125, 50, 0.2);
    }
    
    .metric-card {
        background: white;
        border-radius: 10px;
        padding: 1.25rem;
        box-shadow: 0 3px 10px rgba(0, 0, 0, 0.08);
        border-left: 4px solid #2E7D32;
        margin-bottom: 1rem;
    }
    
    .metric-title {
        color: #666;
        font-size: 0.85rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 0.5rem;
    }
    
    .metric-value {
        color: #2E7D32;
        font-size: 1.8rem;
        font-weight: 700;
        margin: 0;
        line-height: 1.2;
    }
    
    .stButton > button {
        background-color: #2E7D32;
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.7rem 1.5rem;
        font-weight: 600;
        font-size: 1rem;
        width: 100%;
    }
    
    .stButton > button:hover {
        background-color: #1B5E20;
    }
    
    .uploaded-file-info {
        background: #e8f5e9;
        padding: 10px;
        border-radius: 8px;
        margin: 10px 0;
        border-left: 4px solid #4CAF50;
    }
</style>
""", unsafe_allow_html=True)

# ============================================================================
# FUNCIONES PARA MANEJO DE ARCHIVOS KML
# ============================================================================
def procesar_archivo_kml(uploaded_file):
    """Procesa un archivo KML y retorna un GeoDataFrame."""
    try:
        # Crear un archivo temporal
        with tempfile.NamedTemporaryFile(delete=False, suffix='.kml') as tmp_file:
            tmp_file.write(uploaded_file.getvalue())
            tmp_path = tmp_file.name
        
        # Leer el archivo KML
        gdf = gpd.read_file(tmp_path, driver='KML')
        
        # Limpiar el archivo temporal
        os.unlink(tmp_path)
        
        # Validar que tenga geometrías
        if gdf.empty:
            st.error("El archivo KML no contiene geometrías válidas.")
            return None
        
        # Asegurar CRS
        if gdf.crs is None:
            gdf.set_crs(epsg=4326, inplace=True)
        else:
            gdf = gdf.to_crs(epsg=4326)
        
        # Validar geometrías
        gdf = gdf[gdf.is_valid]
        
        if gdf.empty:
            st.error("No se encontraron geometrías válidas en el archivo.")
            return None
        
        # Calcular área en hectáreas
        gdf_proj = gdf.to_crs(epsg=3857)  # Proyección para cálculo de área
        gdf['area_ha'] = gdf_proj.geometry.area / 10000
        
        return gdf
    
    except Exception as e:
        st.error(f"Error procesando el archivo KML: {str(e)}")
        return None

def crear_mapa_esri(gdf):
    """Crea un mapa interactivo con Esri Satellite como capa base."""
    if gdf is None or gdf.empty:
        return None
    
    try:
        # Obtener el centroide del polígono
        centroide = gdf.geometry.unary_union.centroid
        
        # Crear mapa con Esri Satellite
        m = folium.Map(
            location=[centroide.y, centroide.x],
            zoom_start=14,
            control_scale=True,
            tiles=None  # Desactivar tiles por defecto
        )
        
        # Añadir capa base de Esri Satellite
        esri_satellite = folium.TileLayer(
            tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
            attr='Esri',
            name='Esri Satellite',
            overlay=False,
            control=True
        ).add_to(m)
        
        # Añadir otras capas base opcionales
        esri_streets = folium.TileLayer(
            tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Street_Map/MapServer/tile/{z}/{y}/{x}',
            attr='Esri',
            name='Esri Streets',
            overlay=False,
            control=True
        ).add_to(m)
        
        open_street_map = folium.TileLayer(
            tiles='OpenStreetMap',
            name='OpenStreetMap',
            overlay=False,
            control=True
        ).add_to(m)
        
        # Añadir el polígono al mapa
        for idx, row in gdf.iterrows():
            # Estilo del polígono
            folium.GeoJson(
                row.geometry.__geo_interface__,
                name=f'Polígono {idx + 1}',
                style_function=lambda x: {
                    'fillColor': '#2E7D32',
                    'color': '#1B5E20',
                    'weight': 3,
                    'fillOpacity': 0.3,
                    'opacity': 0.8
                },
                tooltip=f"Área: {row.get('area_ha', 0):.2f} ha",
                popup=folium.Popup(
                    f"<b>Polígono {idx + 1}</b><br>"
                    f"Área: {row.get('area_ha', 0):.2f} ha<br>"
                    f"Tipo: {row.geometry.geom_type}",
                    max_width=300
                )
            ).add_to(m)
            
            # Añadir marcador en el centroide
            folium.Marker(
                [centroide.y, centroide.x],
                popup=f"Centroide<br>Lat: {centroide.y:.6f}<br>Lon: {centroide.x:.6f}",
                icon=folium.Icon(color='red', icon='info-sign')
            ).add_to(m)
        
        # Añadir control de capas
        folium.LayerControl().add_to(m)
        
        # Añadir minimapa
        minimap = plugins.MiniMap()
        m.add_child(minimap)
        
        # Añadir botón de pantalla completa
        plugins.Fullscreen().add_to(m)
        
        # Ajustar límites del mapa al polígono
        bounds = [[gdf.total_bounds[1], gdf.total_bounds[0]], 
                  [gdf.total_bounds[3], gdf.total_bounds[2]]]
        m.fit_bounds(bounds)
        
        return m
    
    except Exception as e:
        st.error(f"Error creando el mapa: {str(e)}")
        return None

def generar_zonas_desde_poligono(gdf, n_zonas=12):
    """Genera zonas de análisis dentro del polígono cargado."""
    if gdf is None or gdf.empty:
        return None
    
    try:
        # Tomar el primer polígono (puedes modificar para múltiples polígonos)
        poligono_principal = gdf.iloc[0].geometry
        
        # Crear una cuadrícula dentro del polígono
        bounds = poligono_principal.bounds
        minx, miny, maxx, maxy = bounds
        
        # Determinar número de filas y columnas
        n_cols = int(np.sqrt(n_zonas))
        n_rows = int(np.ceil(n_zonas / n_cols))
        
        # Tamaño de celda
        cell_width = (maxx - minx) / n_cols
        cell_height = (maxy - miny) / n_rows
        
        zonas = []
        
        for i in range(n_rows):
            for j in range(n_cols):
                # Crear celda rectangular
                cell_minx = minx + (j * cell_width)
                cell_maxx = minx + ((j + 1) * cell_width)
                cell_miny = miny + (i * cell_height)
                cell_maxy = miny + ((i + 1) * cell_height)
                
                cell_poly = Polygon([
                    (cell_minx, cell_miny),
                    (cell_maxx, cell_miny),
                    (cell_maxx, cell_maxy),
                    (cell_minx, cell_maxy)
                ])
                
                # Intersectar con el polígono principal
                intersection = poligono_principal.intersection(cell_poly)
                
                if not intersection.is_empty and intersection.area > 0:
                    # Calcular centroide para la zona
                    if intersection.geom_type == 'MultiPolygon':
                        # Tomar el polígono más grande
                        largest = max(intersection.geoms, key=lambda p: p.area)
                        centroid = largest.centroid
                    else:
                        centroid = intersection.centroid
                    
                    zonas.append({
                        'id_zona': len(zonas) + 1,
                        'geometry': intersection,
                        'centroid_lat': centroid.y,
                        'centroid_lon': centroid.x,
                        'area_ha': intersection.area * 11100 * 11100 * np.cos(np.radians(centroid.y)) / 10000  # Aproximación
                    })
                
                if len(zonas) >= n_zonas:
                    break
            if len(zonas) >= n_zonas:
                break
        
        # Crear GeoDataFrame con las zonas
        zonas_gdf = gpd.GeoDataFrame(zonas, geometry='geometry', crs='EPSG:4326')
        
        return zonas_gdf
    
    except Exception as e:
        st.error(f"Error generando zonas: {str(e)}")
        return None

# ============================================================================
# DATOS DE CONFIGURACIÓN
# ============================================================================
CULTIVOS = {
    'PALMA ACEITERA': {
        'nitrogeno_optimo': 160,
        'fosforo_optimo': 60,
        'potasio_optimo': 200,
        'produccion_base': 25.0,
        'ph_optimo': 5.5
    },
    'CACAO': {
        'nitrogeno_optimo': 140,
        'fosforo_optimo': 45,
        'potasio_optimo': 160,
        'produccion_base': 1.5,
        'ph_optimo': 6.0
    },
    'BANANO': {
        'nitrogeno_optimo': 230,
        'fosforo_optimo': 70,
        'potasio_optimo': 300,
        'produccion_base': 40.0,
        'ph_optimo': 6.2
    }
}

MESES = ["ENERO", "FEBRERO", "MARZO", "ABRIL", "MAYO", "JUNIO", 
         "JULIO", "AGOSTO", "SEPTIEMBRE", "OCTUBRE", "NOVIEMBRE", "DICIEMBRE"]

# ============================================================================
# FUNCIONES AUXILIARES
# ============================================================================
def crear_tarjeta_metrica(titulo: str, valor: str, unidad: str = "", color: str = "#2E7D32"):
    """Crea HTML para una tarjeta de métrica estable."""
    return f"""
    <div class="metric-card">
        <div class="metric-title">{titulo}</div>
        <div style="display: flex; align-items: baseline;">
            <div class="metric-value" style="color: {color};">{valor}</div>
            <div style="color: #888; font-size: 0.9rem; margin-left: 0.5rem;">{unidad}</div>
        </div>
    </div>
    """

def generar_datos_muestra(cultivo: str, n_zonas: int = 16, zonas_gdf=None):
    """Genera datos de muestra para análisis."""
    np.random.seed(42)
    params = CULTIVOS.get(cultivo, CULTIVOS['PALMA ACEITERA'])
    
    if zonas_gdf is not None and not zonas_gdf.empty:
        # Usar las zonas reales del polígono
        n_zonas = min(n_zonas, len(zonas_gdf))
        datos = {
            'id_zona': zonas_gdf['id_zona'].head(n_zonas).tolist(),
            'area_ha': zonas_gdf['area_ha'].head(n_zonas).round(2).tolist(),
            'centroid_lat': zonas_gdf['centroid_lat'].head(n_zonas).tolist(),
            'centroid_lon': zonas_gdf['centroid_lon'].head(n_zonas).tolist()
        }
    else:
        # Datos simulados
        datos = {
            'id_zona': list(range(1, n_zonas + 1)),
            'area_ha': np.random.uniform(5, 20, n_zonas).round(2),
            'centroid_lat': np.random.uniform(4.0, 4.5, n_zonas),
            'centroid_lon': np.random.uniform(-75.0, -74.5, n_zonas)
        }
    
    # Datos de suelo y nutrientes (simulados)
    datos.update({
        'nitrogeno': np.random.normal(params['nitrogeno_optimo'], params['nitrogeno_optimo'] * 0.15, n_zonas).clip(0),
        'fosforo': np.random.normal(params['fosforo_optimo'], params['fosforo_optimo'] * 0.15, n_zonas).clip(0),
        'potasio': np.random.normal(params['potasio_optimo'], params['potasio_optimo'] * 0.15, n_zonas).clip(0),
        'ph': np.random.normal(params['ph_optimo'], 0.4, n_zonas).clip(4.5, 7.5),
        'materia_organica': np.random.uniform(2.0, 4.5, n_zonas),
        'ndvi': np.random.uniform(0.5, 0.85, n_zonas)
    })
    
    df = pd.DataFrame(datos)
    
    # Calcular índice de fertilidad
    df['indice_fertilidad'] = (
        (df['nitrogeno'] / params['nitrogeno_optimo'] * 0.25) +
        (df['fosforo'] / params['fosforo_optimo'] * 0.20) +
        (df['potasio'] / params['potasio_optimo'] * 0.20) +
        (df['materia_organica'] / 5.0 * 0.15) +
        (1 - abs(df['ph'] - params['ph_optimo']) / 3.0 * 0.10) +
        (df['ndvi'] * 0.10)
    ).clip(0.2, 0.95)
    
    # Clasificar fertilidad
    condiciones = [
        df['indice_fertilidad'] >= 0.80,
        df['indice_fertilidad'] >= 0.65,
        df['indice_fertilidad'] >= 0.50,
        df['indice_fertilidad'] >= 0.35,
        df['indice_fertilidad'] < 0.35
    ]
    categorias = ['EXCELENTE', 'BUENA', 'MEDIA', 'BAJA', 'MUY BAJA']
    df['categoria'] = np.select(condiciones, categorias, default='MEDIA')
    
    # Asignar prioridad
    mapa_prioridad = {
        'EXCELENTE': 'BAJA',
        'BUENA': 'MEDIA-BAJA',
        'MEDIA': 'MEDIA',
        'BAJA': 'ALTA',
        'MUY BAJA': 'URGENTE'
    }
    df['prioridad'] = df['categoria'].map(mapa_prioridad)
    
    # Calcular potencial de cosecha
    df['potencial_cosecha'] = (params['produccion_base'] * df['indice_fertilidad']).round(1)
    
    return df

def obtener_datos_climaticos(cultivo: str, mes: str, lat=None, lon=None):
    """Obtiene datos climáticos simulados."""
    mes_idx = MESES.index(mes) if mes in MESES else 0
    
    if cultivo == 'PALMA ACEITERA':
        temp_base = 28.0
        precip_base = 6.0
    elif cultivo == 'CACAO':
        temp_base = 25.0
        precip_base = 8.0
    else:  # BANANO
        temp_base = 26.0
        precip_base = 7.0
    
    # Variación mensual
    temp = temp_base + 2 * np.sin(2 * np.pi * mes_idx / 12)
    precip = precip_base + 3 * np.sin(2 * np.pi * mes_idx / 12 + np.pi/2)
    
    return {
        'temperatura': round(temp, 1),
        'precipitacion': round(max(1.0, precip), 1),
        'radiacion_solar': round(18.0 + 4 * np.sin(2 * np.pi * mes_idx / 12), 1),
        'humedad_relativa': round(70 + 10 * np.sin(2 * np.pi * mes_idx / 12), 1),
        'velocidad_viento': round(2.5 + 0.5 * np.sin(2 * np.pi * mes_idx / 12), 1)
    }

# ============================================================================
# INTERFAZ DE USUARIO
# ============================================================================
def mostrar_header():
    """Muestra el encabezado de la aplicación."""
    st.markdown("""
    <div class="main-header">
        <h1 style="margin: 0; font-size: 2.2rem; font-weight: 700;">🌱 ANALIZADOR DE CULTIVOS DIGITAL TWIN</h1>
        <p style="margin: 0.5rem 0 0 0; font-size: 1rem; opacity: 0.95;">
            Plataforma profesional de análisis agrícola con carga de polígonos KML
        </p>
    </div>
    """, unsafe_allow_html=True)

def mostrar_sidebar():
    """Muestra la barra lateral de configuración."""
    with st.sidebar:
        st.markdown("### 📁 CARGA DE POLÍGONO")
        st.markdown("---")
        
        # Uploader de archivo KML
        uploaded_file = st.file_uploader(
            "Sube tu archivo KML/KMZ",
            type=['kml', 'kmz'],
            help="Sube un archivo KML o KMZ con los polígonos de tu parcela"
        )
        
        if uploaded_file is not None:
            with st.spinner("Procesando archivo KML..."):
                gdf = procesar_archivo_kml(uploaded_file)
                
                if gdf is not None:
                    st.session_state['gdf_poligono'] = gdf
                    st.session_state['archivo_cargado'] = True
                    
                    # Mostrar información del archivo
                    st.markdown(f"""
                    <div class="uploaded-file-info">
                        <strong>✅ Archivo cargado exitosamente</strong><br>
                        <small>Polígonos: {len(gdf)}<br>
                        Área total: {gdf['area_ha'].sum():.2f} ha</small>
                    </div>
                    """, unsafe_allow_html=True)
        
        st.markdown("---")
        st.markdown("### ⚙️ CONFIGURACIÓN DEL ANÁLISIS")
        st.markdown("---")
        
        # Selectores de configuración
        cultivo = st.selectbox(
            "**Cultivo principal**",
            list(CULTIVOS.keys()),
            index=0,
            key="cultivo_select"
        )
        
        mes = st.selectbox(
            "**Mes de análisis**",
            MESES,
            index=datetime.now().month - 1,
            key="mes_select"
        )
        
        n_zonas = st.slider(
            "**Número de zonas de análisis**",
            min_value=4,
            max_value=30,
            value=12,
            step=1,
            key="n_zonas_slider"
        )
        
        st.markdown("---")
        
        # Botón para ejecutar análisis
        if st.button("🚀 **EJECUTAR ANÁLISIS COMPLETO**", type="primary", use_container_width=True):
            st.session_state['analisis_ejecutado'] = True
            st.session_state['cultivo'] = cultivo
            st.session_state['mes'] = mes
            st.session_state['n_zonas'] = n_zonas
            
            # Generar zonas si hay polígono cargado
            if 'gdf_poligono' in st.session_state:
                gdf_poligono = st.session_state['gdf_poligono']
                zonas_gdf = generar_zonas_desde_poligono(gdf_poligono, n_zonas)
                st.session_state['zonas_gdf'] = zonas_gdf
        
        st.markdown("---")
        
        # Información adicional
        with st.expander("ℹ️ Información técnica"):
            params = CULTIVOS[cultivo]
            st.markdown(f"""
            **Parámetros para {cultivo}:**
            - Nitrógeno: {params['nitrogeno_optimo']} kg/ha
            - Fósforo: {params['fosforo_optimo']} kg/ha
            - Potasio: {params['potasio_optimo']} kg/ha
            - pH óptimo: {params['ph_optimo']}
            
            **Configuración actual:**
            - Cultivo: {cultivo}
            - Mes: {mes}
            - Zonas: {n_zonas}
            
            **Archivo cargado:** {'✅ Sí' if 'archivo_cargado' in st.session_state else '❌ No'}
            """)

def mostrar_mapa_poligono():
    """Muestra el mapa interactivo con el polígono cargado."""
    st.markdown("## 🗺️ VISUALIZACIÓN DEL POLÍGONO")
    
    if 'gdf_poligono' not in st.session_state:
        st.info("""
        ### 📁 Sube un archivo KML para comenzar
        
        1. Usa la barra lateral para subir un archivo KML/KMZ
        2. El archivo debe contener polígonos válidos
        3. Una vez cargado, se mostrará aquí en el mapa
        
        **Formatos aceptados:** .kml, .kmz
        **Recomendación:** Usa polígonos de Google Earth o QGIS
        """)
        return
    
    gdf = st.session_state['gdf_poligono']
    
    # Mostrar información del polígono
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Polígonos", len(gdf))
    
    with col2:
        st.metric("Área Total", f"{gdf['area_ha'].sum():.2f} ha")
    
    with col3:
        # Obtener tipo de geometría predominante
        geom_types = gdf.geometry.geom_type.value_counts()
        main_type = geom_types.index[0] if len(geom_types) > 0 else "Desconocido"
        st.metric("Tipo", main_type)
    
    st.markdown("---")
    
    # Crear y mostrar el mapa
    with st.spinner("Generando mapa interactivo..."):
        mapa = crear_mapa_esri(gdf)
        
        if mapa:
            # Mostrar el mapa con streamlit-folium
            st_folium(mapa, width=800, height=600, returned_objects=[])
            
            # Botón para descargar información
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("📊 Ver datos del polígono", use_container_width=True):
                    st.dataframe(gdf[['area_ha']].round(2), use_container_width=True)
            
            with col2:
                # Crear archivo GeoJSON para descarga
                geojson = gdf.to_json()
                st.download_button(
                    label="💾 Descargar como GeoJSON",
                    data=geojson,
                    file_name="poligono_exportado.geojson",
                    mime="application/json",
                    use_container_width=True
                )
        else:
            st.error("No se pudo generar el mapa. Verifica que el archivo KML contenga geometrías válidas.")

def mostrar_dashboard(df, datos_clima):
    """Muestra el dashboard principal."""
    st.markdown("## 📊 DASHBOARD PRINCIPAL")
    
    # Métricas en 4 columnas
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        fert_prom = df['indice_fertilidad'].mean()
        color = "#2E7D32" if fert_prom >= 0.6 else "#FF9800"
        st.markdown(crear_tarjeta_metrica(
            "Fertilidad Promedio",
            f"{fert_prom:.3f}",
            "índice",
            color
        ), unsafe_allow_html=True)
    
    with col2:
        area_total = df['area_ha'].sum()
        st.markdown(crear_tarjeta_metrica(
            "Área Total",
            f"{area_total:.1f}",
            "hectáreas",
            "#2196F3"
        ), unsafe_allow_html=True)
    
    with col3:
        pot_prom = df['potencial_cosecha'].mean()
        st.markdown(crear_tarjeta_metrica(
            "Potencial Cosecha",
            f"{pot_prom:.1f}",
            "ton/ha",
            "#4CAF50"
        ), unsafe_allow_html=True)
    
    with col4:
        zonas_urg = len(df[df['prioridad'] == 'URGENTE'])
        color = "#F44336" if zonas_urg > 0 else "#4CAF50"
        st.markdown(crear_tarjeta_metrica(
            "Zonas Críticas",
            f"{zonas_urg}",
            "zonas",
            color
        ), unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Datos climáticos
    st.markdown("## 🌦️ CONDICIONES CLIMÁTICAS")
    
    cols = st.columns(5)
    clima_items = [
        ("🌡️", "Temperatura", f"{datos_clima['temperatura']}°C", "#FF5722"),
        ("🌧️", "Precipitación", f"{datos_clima['precipitacion']} mm/d", "#2196F3"),
        ("☀️", "Radiación Solar", f"{datos_clima['radiacion_solar']} MJ/m²", "#FFC107"),
        ("💧", "Humedad", f"{datos_clima['humedad_relativa']}%", "#03A9F4"),
        ("💨", "Viento", f"{datos_clima['velocidad_viento']} m/s", "#9E9E9E")
    ]
    
    for idx, (icono, nombre, valor, color) in enumerate(clima_items):
        with cols[idx]:
            st.markdown(f"""
            <div style="text-align: center; padding: 1rem; background: white; 
                        border-radius: 10px; box-shadow: 0 2px 6px rgba(0,0,0,0.05);">
                <div style="font-size: 1.8rem; margin-bottom: 0.5rem;">{icono}</div>
                <div style="font-size: 0.85rem; color: #666; margin-bottom: 0.25rem;">
                    {nombre}
                </div>
                <div style="font-size: 1.3rem; font-weight: 700; color: {color};">
                    {valor}
                </div>
            </div>
            """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Gráficos principales
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### Distribución de Fertilidad")
        fig = px.histogram(
            df, 
            x='indice_fertilidad',
            nbins=12,
            color_discrete_sequence=['#2E7D32']
        )
        fig.update_layout(
            height=300,
            showlegend=False,
            xaxis_title="Índice de Fertilidad",
            yaxis_title="Número de Zonas"
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.markdown("#### Prioridad por Zonas")
        prioridad_counts = df['prioridad'].value_counts().reset_index()
        prioridad_counts.columns = ['Prioridad', 'Cantidad']
        
        fig = px.bar(
            prioridad_counts,
            x='Prioridad',
            y='Cantidad',
            color='Prioridad',
            color_discrete_sequence=px.colors.sequential.Reds_r
        )
        fig.update_layout(
            height=300,
            showlegend=False,
            xaxis_title="Prioridad",
            yaxis_title="Número de Zonas"
        )
        st.plotly_chart(fig, use_container_width=True)

def mostrar_analisis_detallado(df):
    """Muestra análisis detallado por zona."""
    st.markdown("## 🔬 ANÁLISIS DETALLADO POR ZONA")
    
    zona_seleccionada = st.selectbox(
        "Seleccionar zona:",
        df['id_zona'].tolist(),
        format_func=lambda x: f"Zona {x}",
        key="zona_select"
    )
    
    datos_zona = df[df['id_zona'] == zona_seleccionada].iloc[0]
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.markdown(f"### Zona {zona_seleccionada}")
        st.markdown(f"**Área:** {datos_zona['area_ha']:.2f} ha")
        
        if 'centroid_lat' in datos_zona and 'centroid_lon' in datos_zona:
            st.markdown(f"**Ubicación:** {datos_zona['centroid_lat']:.4f}, {datos_zona['centroid_lon']:.4f}")
        
        st.markdown(f"**Fertilidad:** {datos_zona['indice_fertilidad']:.3f}")
        st.markdown(f"**Categoría:** {datos_zona['categoria']}")
        st.markdown(f"**Prioridad:** {datos_zona['prioridad']}")
        st.markdown(f"**Potencial:** {datos_zona['potencial_cosecha']:.1f} ton/ha")
        
        if datos_zona['prioridad'] == 'URGENTE':
            st.error("🚨 Intervención urgente requerida")
        elif datos_zona['prioridad'] == 'ALTA':
            st.warning("⚠️ Atención prioritaria recomendada")
        else:
            st.success("✅ Condiciones adecuadas")
    
    with col2:
        # Gráfico de nutrientes
        nutrientes = ['Nitrógeno', 'Fósforo', 'Potasio']
        valores = [
            datos_zona['nitrogeno'],
            datos_zona['fosforo'],
            datos_zona['potasio']
        ]
        
        cultivo_actual = st.session_state.get('cultivo', 'PALMA ACEITERA')
        optimos = [
            CULTIVOS[cultivo_actual]['nitrogeno_optimo'],
            CULTIVOS[cultivo_actual]['fosforo_optimo'],
            CULTIVOS[cultivo_actual]['potasio_optimo']
        ]
        
        fig = go.Figure()
        
        fig.add_trace(go.Bar(
            x=nutrientes,
            y=valores,
            name='Valor Actual',
            marker_color=['#FF5722', '#2196F3', '#4CAF50']
        ))
        
        # Líneas para valores óptimos
        for i, nutriente in enumerate(nutrientes):
            fig.add_shape(
                type='line',
                x0=i-0.4, x1=i+0.4,
                y0=optimos[i], y1=optimos[i],
                line=dict(color='red', width=2, dash='dash')
            )
            fig.add_annotation(
                x=i,
                y=optimos[i] * 1.05,
                text="Óptimo",
                showarrow=False,
                font=dict(size=10, color='red')
            )
        
        fig.update_layout(
            title="Niveles de Nutrientes",
            height=350,
            yaxis_title="kg/ha",
            showlegend=False
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    # Tabla de todas las zonas
    st.markdown("---")
    st.markdown("### 📋 RESUMEN DE TODAS LAS ZONAS")
    
    columnas = ['id_zona', 'area_ha', 'indice_fertilidad', 'categoria', 'prioridad', 'potencial_cosecha']
    if 'centroid_lat' in df.columns and 'centroid_lon' in df.columns:
        columnas.extend(['centroid_lat', 'centroid_lon'])
    
    df_display = df[columnas].copy()
    
    # Formatear números
    df_display['area_ha'] = df_display['area_ha'].round(2)
    df_display['indice_fertilidad'] = df_display['indice_fertilidad'].round(3)
    df_display['potencial_cosecha'] = df_display['potencial_cosecha'].round(1)
    
    if 'centroid_lat' in df_display.columns:
        df_display['centroid_lat'] = df_display['centroid_lat'].round(6)
        df_display['centroid_lon'] = df_display['centroid_lon'].round(6)
    
    st.dataframe(
        df_display,
        use_container_width=True,
        column_config={
            'id_zona': 'ID Zona',
            'area_ha': st.column_config.NumberColumn('Área (ha)', format='%.2f'),
            'indice_fertilidad': st.column_config.NumberColumn('Fertilidad', format='%.3f'),
            'categoria': 'Categoría',
            'prioridad': 'Prioridad',
            'potencial_cosecha': st.column_config.NumberColumn('Potencial (t/ha)', format='%.1f')
        },
        hide_index=True
    )

def mostrar_bienvenida():
    """Muestra pantalla de bienvenida."""
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.markdown("""
        ## 👋 ¡Bienvenido al Analizador de Cultivos Digital Twin!
        
        ### 🌟 **NUEVA FUNCIONALIDAD: Carga de polígonos KML**
        
        Ahora puedes subir tus propios polígonos de parcela en formato KML/KMZ
        y visualizarlos en mapas satelitales de alta resolución.
        
        ### 🚀 **¿Cómo empezar?**
        
        1. **Sube tu archivo KML** en la barra lateral
        2. **Configura los parámetros** del análisis
        3. **Ejecuta el análisis completo**
        4. **Explora los resultados** en las diferentes pestañas
        
        ### 📊 **Características principales**
        
        ✅ **Carga de polígonos KML/KMZ**  
        ✅ **Mapas interactivos con Esri Satellite**  
        ✅ **Análisis de fertilidad por zonas**  
        ✅ **Datos climáticos estacionales**  
        ✅ **Reportes exportables en múltiples formatos**  
        
        ### 🗺️ **Sobre los archivos KML**
        
        Puedes crear archivos KML usando:
        - Google Earth
        - QGIS
        - ArcGIS
        - Cualquier software GIS que exporte a KML
        """)
    
    with col2:
        st.info("""
        **Versión:** 3.0 con KML  
        **Estado:** Listo para uso  
        **Formatos:** KML, KMZ  
        **Mapas:** Esri Satellite  
        **Cultivos:** 3 disponibles  
        """)

def mostrar_footer():
    """Muestra el pie de página."""
    st.markdown("---")
    
    st.markdown("""
    <div style="text-align: center; color: #666; padding: 1rem 0;">
        <p style="margin: 0; font-size: 0.9rem;">
            🌿 <strong>Analizador de Cultivos Digital Twin v3.0</strong> | 
            Con soporte para KML y mapas satelitales | 
            © 2024 AgTech Solutions
        </p>
        <p style="margin: 0.5rem 0 0 0; font-size: 0.8rem;">
            Desarrollado para agricultura de precisión | 
            <a href="#" style="color: #2E7D32; text-decoration: none;">Soporte</a> | 
            <a href="#" style="color: #2E7D32; text-decoration: none;">Documentación</a>
        </p>
    </div>
    """, unsafe_allow_html=True)

# ============================================================================
# FUNCIÓN PRINCIPAL
# ============================================================================
def main():
    """Función principal de la aplicación."""
    
    # Inicializar session state
    if 'analisis_ejecutado' not in st.session_state:
        st.session_state['analisis_ejecutado'] = False
    if 'archivo_cargado' not in st.session_state:
        st.session_state['archivo_cargado'] = False
    
    # Mostrar encabezado
    mostrar_header()
    
    # Mostrar barra lateral
    mostrar_sidebar()
    
    # Determinar qué pestañas mostrar
    if st.session_state['archivo_cargado']:
        # Mostrar pestañas incluyendo el mapa
        tab1, tab2, tab3, tab4 = st.tabs(["🗺️ Mapa", "📊 Dashboard", "🔬 Análisis", "📄 Reportes"])
        
        with tab1:
            mostrar_mapa_poligono()
        
        # Contenido de análisis si se ha ejecutado
        if st.session_state['analisis_ejecutado']:
            with tab2:
                # Obtener parámetros
                cultivo = st.session_state.get('cultivo', 'PALMA ACEITERA')
                mes = st.session_state.get('mes', 'ENERO')
                n_zonas = st.session_state.get('n_zonas', 12)
                
                # Generar datos usando zonas del polígono si existen
                zonas_gdf = st.session_state.get('zonas_gdf', None)
                
                with st.spinner("🔄 Generando análisis..."):
                    df = generar_datos_muestra(cultivo, n_zonas, zonas_gdf)
                    datos_clima = obtener_datos_climaticos(cultivo, mes)
                
                mostrar_dashboard(df, datos_clima)
            
            with tab3:
                if 'df' in locals():
                    mostrar_analisis_detallado(df)
            
            with tab4:
                if 'df' in locals():
                    st.markdown("## 📄 REPORTES Y EXPORTACIÓN")
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        # Exportar CSV
                        csv = df.to_csv(index=False, encoding='utf-8')
                        st.download_button(
                            label="📥 Exportar CSV",
                            data=csv,
                            file_name=f"analisis_{cultivo}_{datetime.now().strftime('%Y%m%d')}.csv",
                            mime="text/csv",
                            use_container_width=True
                        )
                    
                    with col2:
                        # Exportar Excel
                        buffer = io.BytesIO()
                        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                            df.to_excel(writer, sheet_name='Análisis', index=False)
                        
                        st.download_button(
                            label="📊 Exportar Excel",
                            data=buffer.getvalue(),
                            file_name=f"analisis_{cultivo}_{datetime.now().strftime('%Y%m%d')}.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            use_container_width=True
                        )
                    
                    # Vista previa
                    st.markdown("---")
                    st.markdown("### 👁️ VISTA PREVIA DEL REPORTE")
                    
                    with st.expander("Ver estadísticas"):
                        col1, col2, col3 = st.columns(3)
                        
                        with col1:
                            st.metric("Fertilidad Promedio", f"{df['indice_fertilidad'].mean():.3f}")
                        
                        with col2:
                            st.metric("Potencial Total", f"{df['potencial_cosecha'].sum():.0f} ton")
                        
                        with col3:
                            zonas_bajas = len(df[df['categoria'].isin(['BAJA', 'MUY BAJA'])])
                            st.metric("Zonas Problemáticas", zonas_bajas)
        else:
            with tab2:
                st.info("Ejecuta el análisis desde la barra lateral para ver los resultados.")
            with tab3:
                st.info("Ejecuta el análisis desde la barra lateral para ver los resultados.")
            with tab4:
                st.info("Ejecuta el análisis desde la barra lateral para ver los resultados.")
    
    elif st.session_state['analisis_ejecutado']:
        # Análisis ejecutado sin archivo KML (datos simulados)
        tab1, tab2, tab3 = st.tabs(["📊 Dashboard", "🔬 Análisis", "📄 Reportes"])
        
        # Obtener parámetros
        cultivo = st.session_state.get('cultivo', 'PALMA ACEITERA')
        mes = st.session_state.get('mes', 'ENERO')
        n_zonas = st.session_state.get('n_zonas', 12)
        
        with st.spinner("🔄 Generando análisis con datos simulados..."):
            df = generar_datos_muestra(cultivo, n_zonas)
            datos_clima = obtener_datos_climaticos(cultivo, mes)
        
        with tab1:
            mostrar_dashboard(df, datos_clima)
        
        with tab2:
            mostrar_analisis_detallado(df)
        
        with tab3:
            st.markdown("## 📄 REPORTES Y EXPORTACIÓN")
            
            col1, col2 = st.columns(2)
            
            with col1:
                csv = df.to_csv(index=False, encoding='utf-8')
                st.download_button(
                    label="📥 Exportar CSV",
                    data=csv,
                    file_name=f"analisis_{cultivo}_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv",
                    use_container_width=True
                )
            
            with col2:
                buffer = io.BytesIO()
                with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                    df.to_excel(writer, sheet_name='Análisis', index=False)
                
                st.download_button(
                    label="📊 Exportar Excel",
                    data=buffer.getvalue(),
                    file_name=f"analisis_{cultivo}_{datetime.now().strftime('%Y%m%d')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )
    
    else:
        # Pantalla de bienvenida inicial
        mostrar_bienvenida()
    
    # Mostrar footer
    mostrar_footer()

# ============================================================================
# EJECUCIÓN
# ============================================================================
if __name__ == "__main__":
    main()
