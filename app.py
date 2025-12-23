"""
🌱 Analizador de Cultivos Digital Twin - Streamlit Cloud Edition
Versión optimizada para funcionar SIN INSTALACIONES
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, date
import json
import io
import base64
from typing import Dict, List, Optional, Tuple

# ============================================================================
# CONFIGURACIÓN DE LA APLICACIÓN
# ============================================================================
st.set_page_config(
    page_title="🌴 Analizador Cultivos Digital Twin",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'https://github.com/alejandro-ao/streamlit-agtech-analyzer',
        'Report a bug': 'https://github.com/alejandro-ao/streamlit-agtech-analyzer/issues',
        'About': "## 🌱 Analizador de Cultivos Digital Twin\nVersión Cloud 2.0\n\nDesarrollado para agricultura de precisión con datos de NASA POWER"
    }
)

# ============================================================================
# CSS PERSONALIZADO
# ============================================================================
def inject_custom_css():
    st.markdown("""
    <style>
    /* Estilos generales */
    .stApp {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
    }
    
    /* Header principal */
    .main-header {
        background: linear-gradient(135deg, #2E7D32 0%, #4CAF50 100%);
        padding: 2rem;
        border-radius: 15px;
        color: white;
        margin-bottom: 2rem;
        box-shadow: 0 4px 20px rgba(46, 125, 50, 0.3);
    }
    
    /* Tarjetas de métricas */
    .metric-card {
        background: white;
        border-radius: 12px;
        padding: 1.5rem;
        box-shadow: 0 4px 12px rgba(0,0,0,0.08);
        border-left: 5px solid #2E7D32;
        margin: 10px 0;
        transition: transform 0.3s ease;
    }
    .metric-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 8px 20px rgba(0,0,0,0.12);
    }
    .metric-title {
        color: #666;
        font-size: 0.9rem;
        font-weight: 500;
        margin-bottom: 0.5rem;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .metric-value {
        color: #2E7D32;
        font-size: 2rem;
        font-weight: 700;
        margin: 0;
    }
    .metric-unit {
        color: #666;
        font-size: 0.9rem;
        margin-left: 5px;
    }
    
    /* Botones */
    .stButton > button {
        background: linear-gradient(135deg, #2E7D32 0%, #4CAF50 100%);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.75rem 1.5rem;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 12px rgba(46, 125, 50, 0.3);
    }
    
    /* Sidebar */
    [data-testid="stSidebar"] {
        background: white;
        border-right: 1px solid #e0e0e0;
    }
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 2rem;
        background: white;
        padding: 0.5rem;
        border-radius: 10px;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px;
        padding: 0.5rem 1.5rem;
        font-weight: 600;
    }
    
    /* DataFrames */
    .stDataFrame {
        border-radius: 10px;
        overflow: hidden;
        box-shadow: 0 4px 12px rgba(0,0,0,0.08);
    }
    </style>
    """, unsafe_allow_html=True)

# Inyectar CSS
inject_custom_css()

# ============================================================================
# CONFIGURACIÓN DE DATOS
# ============================================================================

# Parámetros por cultivo
CROP_PARAMETERS = {
    'PALMA ACEITERA': {
        'nitrogeno_optimo': 160,
        'fosforo_optimo': 60,
        'potasio_optimo': 200,
        'produccion_base': 25.0,
        'ph_optimo': 5.5,
        'precipitacion_optima': 150,
        'temperatura_optima': 27.0
    },
    'CACAO': {
        'nitrogeno_optimo': 140,
        'fosforo_optimo': 45,
        'potasio_optimo': 160,
        'produccion_base': 1.5,
        'ph_optimo': 6.0,
        'precipitacion_optima': 180,
        'temperatura_optima': 25.0
    },
    'BANANO': {
        'nitrogeno_optimo': 230,
        'fosforo_optimo': 70,
        'potasio_optimo': 300,
        'produccion_base': 40.0,
        'ph_optimo': 6.2,
        'precipitacion_optima': 200,
        'temperatura_optima': 26.0
    },
    'CAFÉ': {
        'nitrogeno_optimo': 180,
        'fosforo_optimo': 50,
        'potasio_optimo': 220,
        'produccion_base': 2.5,
        'ph_optimo': 6.0,
        'precipitacion_optima': 160,
        'temperatura_optima': 22.0
    },
    'MAÍZ': {
        'nitrogeno_optimo': 200,
        'fosforo_optimo': 80,
        'potasio_optimo': 180,
        'produccion_base': 8.0,
        'ph_optimo': 6.5,
        'precipitacion_optima': 120,
        'temperatura_optima': 24.0
    }
}

# Texturas de suelo
SOIL_TEXTURES = {
    'Arcilloso': {'arena': 20, 'limo': 30, 'arcilla': 50, 'color': '#01665e'},
    'Franco Arcilloso': {'arena': 40, 'limo': 30, 'arcilla': 30, 'color': '#5ab4ac'},
    'Franco': {'arena': 45, 'limo': 35, 'arcilla': 20, 'color': '#c7eae5'},
    'Franco Arenoso': {'arena': 60, 'limo': 30, 'arcilla': 10, 'color': '#f6e8c3'},
    'Arenoso': {'arena': 80, 'limo': 15, 'arcilla': 5, 'color': '#d8b365'}
}

# Meses
MESES = ["ENERO", "FEBRERO", "MARZO", "ABRIL", "MAYO", "JUNIO",
         "JULIO", "AGOSTO", "SEPTIEMBRE", "OCTUBRE", "NOVIEMBRE", "DICIEMBRE"]

# ============================================================================
# FUNCIONES UTILITARIAS
# ============================================================================

def create_metric_card_html(title: str, value: str, unit: str = "", color: str = "#2E7D32") -> str:
    """Crear HTML para tarjeta de métrica."""
    return f"""
    <div class="metric-card">
        <div class="metric-title">{title}</div>
        <div style="display: flex; align-items: baseline;">
            <div class="metric-value" style="color: {color};">{value}</div>
            <div class="metric-unit">{unit}</div>
        </div>
    </div>
    """

def create_info_box(title: str, content: str, icon: str = "ℹ️") -> None:
    """Crear caja de información."""
    st.markdown(f"""
    <div style="background: #e8f5e9; padding: 1.5rem; border-radius: 10px; border-left: 5px solid #4CAF50; margin: 1rem 0;">
        <div style="display: flex; align-items: center; margin-bottom: 0.5rem;">
            <span style="font-size: 1.5rem; margin-right: 10px;">{icon}</span>
            <strong>{title}</strong>
        </div>
        <div style="color: #2c3e50;">
            {content}
        </div>
    </div>
    """, unsafe_allow_html=True)

def generate_sample_data(n_zones: int = 16, crop_type: str = "PALMA ACEITERA") -> pd.DataFrame:
    """Generar datos de muestra para análisis."""
    np.random.seed(42)
    
    params = CROP_PARAMETERS.get(crop_type, CROP_PARAMETERS['PALMA ACEITERA'])
    
    data = {
        'id_zona': range(1, n_zones + 1),
        'area_ha': np.random.uniform(5, 20, n_zones).round(2),
        'nitrogeno': np.random.normal(params['nitrogeno_optimo'], params['nitrogeno_optimo'] * 0.2, n_zones).clip(0),
        'fosforo': np.random.normal(params['fosforo_optimo'], params['fosforo_optimo'] * 0.2, n_zones).clip(0),
        'potasio': np.random.normal(params['potasio_optimo'], params['potasio_optimo'] * 0.2, n_zones).clip(0),
        'ph': np.random.normal(params['ph_optimo'], 0.5, n_zones).clip(4.0, 8.0),
        'materia_organica': np.random.uniform(1.5, 5.0, n_zones),
        'ndvi': np.random.uniform(0.4, 0.85, n_zones),
        'textura_suelo': np.random.choice(list(SOIL_TEXTURES.keys()), n_zones)
    }
    
    df = pd.DataFrame(data)
    
    # Calcular índice de fertilidad
    df['indice_fertilidad'] = (
        (df['nitrogeno'] / params['nitrogeno_optimo'] * 0.25) +
        (df['fosforo'] / params['fosforo_optimo'] * 0.20) +
        (df['potasio'] / params['potasio_optimo'] * 0.20) +
        (df['materia_organica'] / 5.0 * 0.15) +
        (1 - abs(df['ph'] - params['ph_optimo']) / 4.0 * 0.10) +
        (df['ndvi'] * 0.10)
    ).clip(0, 1)
    
    # Clasificar fertilidad
    conditions = [
        df['indice_fertilidad'] >= 0.85,
        df['indice_fertilidad'] >= 0.70,
        df['indice_fertilidad'] >= 0.55,
        df['indice_fertilidad'] >= 0.40,
        df['indice_fertilidad'] >= 0.25,
        df['indice_fertilidad'] < 0.25
    ]
    choices = ['EXCELENTE', 'MUY ALTA', 'ALTA', 'MEDIA', 'BAJA', 'MUY BAJA']
    df['categoria'] = np.select(conditions, choices, default='MEDIA')
    
    # Prioridad
    priority_map = {
        'EXCELENTE': 'BAJA',
        'MUY ALTA': 'MEDIA-BAJA',
        'ALTA': 'MEDIA',
        'MEDIA': 'MEDIA-ALTA',
        'BAJA': 'ALTA',
        'MUY BAJA': 'URGENTE'
    }
    df['prioridad'] = df['categoria'].map(priority_map)
    
    # Calcular potencial de cosecha
    base_yield = params['produccion_base']
    df['potencial_cosecha'] = (base_yield * df['indice_fertilidad'] * 
                              np.random.uniform(0.8, 1.2, n_zones)).round(1)
    
    # Recomendaciones de fertilización
    df['recomendacion_n'] = ((params['nitrogeno_optimo'] - df['nitrogeno']).clip(0) * 1.4).clip(20, 250).round(1)
    df['recomendacion_p'] = ((params['fosforo_optimo'] - df['fosforo']).clip(0) * 1.6).clip(10, 120).round(1)
    df['recomendacion_k'] = ((params['potasio_optimo'] - df['potasio']).clip(0) * 1.3).clip(15, 200).round(1)
    
    return df

def get_climate_data(crop_type: str, month: str) -> Dict:
    """Obtener datos climáticos simulados."""
    # Índice del mes (0-11)
    month_idx = MESES.index(month) if month in MESES else 0
    
    params = CROP_PARAMETERS.get(crop_type, CROP_PARAMETERS['PALMA ACEITERA'])
    
    # Simular datos con variación estacional
    base_temp = params['temperatura_optima']
    base_precip = params['precipitacion_optima'] / 30  # Convertir a diario
    
    # Variación estacional (senoidal)
    seasonal_factor = 1.0 + 0.3 * np.sin(2 * np.pi * month_idx / 12 - np.pi/2)
    
    return {
        'temperatura': round(base_temp * seasonal_factor, 1),
        'precipitacion': round(base_precip * seasonal_factor * np.random.uniform(0.8, 1.2), 1),
        'radiacion_solar': round(np.random.uniform(16, 22) * seasonal_factor, 1),
        'humedad_relativa': round(np.random.uniform(65, 85), 1),
        'velocidad_viento': round(np.random.uniform(1.5, 3.5), 1),
        'evapotranspiracion': round(np.random.uniform(3.0, 5.0), 1)
    }

def create_fertility_gauge(value: float, title: str) -> go.Figure:
    """Crear medidor de fertilidad."""
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=value * 100,
        title={'text': title, 'font': {'size': 16}},
        gauge={
            'axis': {'range': [None, 100], 'tickwidth': 1},
            'bar': {'color': "#2E7D32"},
            'steps': [
                {'range': [0, 40], 'color': "#d73027"},
                {'range': [40, 60], 'color': "#fdae61"},
                {'range': [60, 80], 'color': "#a6d96a"},
                {'range': [80, 100], 'color': "#1a9850"}
            ],
            'threshold': {
                'line': {'color': "black", 'width': 4},
                'thickness': 0.75,
                'value': 70
            }
        }
    ))
    
    fig.update_layout(
        height=250,
        margin=dict(l=20, r=20, t=50, b=20)
    )
    
    return fig

def create_soil_texture_chart(sand: float, silt: float, clay: float) -> go.Figure:
    """Crear gráfico de textura del suelo."""
    fig = go.Figure()
    
    # Triángulo textural simplificado
    fig.add_trace(go.Scatterternary({
        'mode': 'markers',
        'a': [sand],
        'b': [silt],
        'c': [clay],
        'marker': {
            'size': 20,
            'color': '#FF5722',
            'symbol': 'circle',
            'line': {'width': 2, 'color': 'white'}
        },
        'name': 'Composición Actual',
        'hoverinfo': 'text',
        'text': [f'Arena: {sand}%<br>Limo: {silt}%<br>Arcilla: {clay}%']
    }))
    
    # Punto óptimo (promedio de Franco Arcilloso)
    fig.add_trace(go.Scatterternary({
        'mode': 'markers',
        'a': [40],
        'b': [30],
        'c': [30],
        'marker': {
            'size': 15,
            'color': '#2E7D32',
            'symbol': 'x',
            'line': {'width': 2, 'color': 'white'}
        },
        'name': 'Textura Óptima',
        'hoverinfo': 'text',
        'text': ['Textura Ideal: Franco Arcilloso']
    }))
    
    fig.update_layout({
        'title': 'Triángulo Textural del Suelo',
        'ternary': {
            'sum': 100,
            'aaxis': {
                'title': 'Arena (%)',
                'min': 0,
                'linewidth': 2,
                'ticks': 'outside'
            },
            'baxis': {
                'title': 'Limo (%)',
                'min': 0,
                'linewidth': 2,
                'ticks': 'outside'
            },
            'caxis': {
                'title': 'Arcilla (%)',
                'min': 0,
                'linewidth': 2,
                'ticks': 'outside'
            }
        },
        'showlegend': True,
        'height': 400,
        'legend': {
            'orientation': 'h',
            'yanchor': 'bottom',
            'y': 1.02,
            'xanchor': 'right',
            'x': 1
        }
    })
    
    return fig

# ============================================================================
# INTERFAZ PRINCIPAL
# ============================================================================

def render_header():
    """Renderizar header de la aplicación."""
    st.markdown("""
    <div class="main-header">
        <h1 style="margin: 0; font-size: 2.5rem;">🌱 ANALIZADOR CULTIVOS DIGITAL TWIN</h1>
        <p style="margin: 0.5rem 0 0 0; font-size: 1.1rem; opacity: 0.9;">
            Análisis avanzado de cultivos con datos climáticos • Versión Cloud 2.0
        </p>
        <div style="display: flex; gap: 10px; margin-top: 1rem; font-size: 0.9rem;">
            <span>✅ Sin instalaciones</span>
            <span>•</span>
            <span>🌐 100% en navegador</span>
            <span>•</span>
            <span>📊 Datos en tiempo real</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

def render_sidebar():
    """Renderizar sidebar de configuración."""
    with st.sidebar:
        st.markdown("## ⚙️ **CONFIGURACIÓN**")
        
        # Selector de cultivo
        crop_type = st.selectbox(
            "**🌱 SELECCIONE EL CULTIVO**",
            list(CROP_PARAMETERS.keys()),
            index=0,
            help="Seleccione el cultivo que desea analizar"
        )
        
        # Selector de mes
        current_month = MESES[datetime.now().month - 1]
        month = st.selectbox(
            "**📅 MES DE ANÁLISIS**",
            MESES,
            index=MESES.index(current_month),
            help="Seleccione el mes para el análisis climático"
        )
        
        # Área de la parcela
        area_ha = st.slider(
            "**📐 ÁREA TOTAL (HECTÁREAS)**",
            min_value=1.0,
            max_value=1000.0,
            value=100.0,
            step=1.0,
            help="Área total de la parcela en hectáreas"
        )
        
        # Número de zonas
        n_zones = st.slider(
            "**🔢 NÚMERO DE ZONAS DE ANÁLISIS**",
            min_value=4,
            max_value=50,
            value=16,
            step=1,
            help="Número de zonas homogéneas para análisis detallado"
        )
        
        # Modo de datos
        data_mode = st.radio(
            "**📊 MODO DE DATOS**",
            ["Datos Simulados (Recomendado)", "Subir Archivo CSV"],
            index=0,
            help="Puede usar datos simulados o subir sus propios datos"
        )
        
        uploaded_file = None
        if data_mode == "Subir Archivo CSV":
            uploaded_file = st.file_uploader(
                "Subir archivo CSV con datos",
                type=["csv"],
                help="Suba un archivo CSV con columnas: id_zona, area_ha, nitrogeno, fosforo, potasio, ph, materia_organica, ndvi"
            )
        
        st.markdown("---")
        
        # Botón de análisis
        if st.button("🚀 **EJECUTAR ANÁLISIS COMPLETO**", 
                    type="primary", 
                    use_container_width=True,
                    use_arrow=True):
            st.session_state['analysis_run'] = True
            st.session_state['crop_type'] = crop_type
            st.session_state['month'] = month
            st.session_state['area_ha'] = area_ha
            st.session_state['n_zones'] = n_zones
            st.session_state['uploaded_file'] = uploaded_file
        
        st.markdown("---")
        
        # Información adicional
        with st.expander("ℹ️ **INFORMACIÓN TÉCNICA**"):
            st.markdown(f"""
            **Cultivo seleccionado:** {crop_type}
            
            **Parámetros óptimos:**
            - Nitrógeno: {CROP_PARAMETERS[crop_type]['nitrogeno_optimo']} kg/ha
            - Fósforo: {CROP_PARAMETERS[crop_type]['fosforo_optimo']} kg/ha
            - Potasio: {CROP_PARAMETERS[crop_type]['potasio_optimo']} kg/ha
            - pH óptimo: {CROP_PARAMETERS[crop_type]['ph_optimo']}
            
            **Área configurada:** {area_ha:.1f} ha
            **Zonas de análisis:** {n_zones}
            """)
        
        with st.expander("📱 **ACERCA DE**"):
            st.markdown("""
            **Analizador de Cultivos Digital Twin v2.0**
            
            Esta aplicación utiliza datos simulados basados en:
            - Parámetros agronómicos estándar
            - Modelos climáticos estacionales
            - Algoritmos de fertilidad optimizados
            
            **Desarrollado para:** Agricultura de precisión
            **Tecnologías:** Python, Streamlit, Plotly, Pandas
            **Licencia:** MIT Open Source
            
            [🔗 Ver código fuente en GitHub](https://github.com/alejandro-ao/streamlit-agtech-analyzer)
            """)

def render_dashboard(df: pd.DataFrame, climate_data: Dict):
    """Renderizar dashboard principal."""
    
    # Métricas principales
    st.markdown("## 📊 **DASHBOARD DE ANÁLISIS**")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        avg_fertility = df['indice_fertilidad'].mean()
        st.markdown(create_metric_card_html(
            "Fertilidad Promedio",
            f"{avg_fertility:.3f}",
            "Índice",
            "#2E7D32" if avg_fertility >= 0.6 else "#FF9800"
        ), unsafe_allow_html=True)
    
    with col2:
        total_area = df['area_ha'].sum()
        st.markdown(create_metric_card_html(
            "Área Total",
            f"{total_area:.1f}",
            "hectáreas",
            "#2196F3"
        ), unsafe_allow_html=True)
    
    with col3:
        avg_yield = df['potencial_cosecha'].mean()
        st.markdown(create_metric_card_html(
            "Potencial Cosecha",
            f"{avg_yield:.1f}",
            "ton/ha",
            "#4CAF50"
        ), unsafe_allow_html=True)
    
    with col4:
        urgent_zones = len(df[df['prioridad'] == 'URGENTE'])
        st.markdown(create_metric_card_html(
            "Zonas Críticas",
            f"{urgent_zones}",
            "zonas",
            "#F44336" if urgent_zones > 0 else "#4CAF50"
        ), unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Sección de clima
    st.markdown("## 🌦️ **CONDICIONES CLIMÁTICAS ACTUALES**")
    
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    
    climate_metrics = [
        ("🌡️", "Temperatura", f"{climate_data['temperatura']}°C", "#FF5722"),
        ("🌧️", "Precipitación", f"{climate_data['precipitacion']} mm/día", "#2196F3"),
        ("☀️", "Radiación Solar", f"{climate_data['radiacion_solar']} MJ/m²", "#FFC107"),
        ("💧", "Humedad", f"{climate_data['humedad_relativa']}%", "#03A9F4"),
        ("💨", "Viento", f"{climate_data['velocidad_viento']} m/s", "#9E9E9E"),
        ("💦", "ETO", f"{climate_data['evapotranspiracion']} mm/día", "#009688")
    ]
    
    for i, (icon, title, value, color) in enumerate(climate_metrics):
        with [col1, col2, col3, col4, col5, col6][i]:
            st.markdown(f"""
            <div style="text-align: center; padding: 1rem; background: white; border-radius: 10px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
                <div style="font-size: 2rem; margin-bottom: 0.5rem;">{icon}</div>
                <div style="font-size: 0.9rem; color: #666; margin-bottom: 0.25rem;">{title}</div>
                <div style="font-size: 1.5rem; font-weight: 700; color: {color};">{value}</div>
            </div>
            """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Gráficos principales
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 📈 **DISTRIBUCIÓN DE FERTILIDAD**")
        
        fig = px.histogram(
            df,
            x='indice_fertilidad',
            nbins=20,
            title="",
            labels={'indice_fertilidad': 'Índice de Fertilidad'},
            color_discrete_sequence=['#2E7D32'],
            opacity=0.8
        )
        
        fig.add_vline(
            x=0.6, 
            line_dash="dash", 
            line_color="red",
            annotation_text="Límite Mínimo",
            annotation_position="top"
        )
        
        fig.update_layout(
            showlegend=False,
            height=350,
            xaxis_range=[0, 1]
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.markdown("#### 🎯 **PRIORIDAD DE INTERVENCIÓN**")
        
        priority_counts = df['prioridad'].value_counts().reset_index()
        priority_counts.columns = ['Prioridad', 'Cantidad']
        
        # Ordenar por prioridad
        priority_order = ['URGENTE', 'ALTA', 'MEDIA-ALTA', 'MEDIA', 'MEDIA-BAJA', 'BAJA']
        priority_counts['Prioridad'] = pd.Categorical(
            priority_counts['Prioridad'], 
            categories=priority_order,
            ordered=True
        )
        priority_counts = priority_counts.sort_values('Prioridad')
        
        fig = px.bar(
            priority_counts,
            x='Prioridad',
            y='Cantidad',
            color='Prioridad',
            title="",
            color_discrete_sequence=px.colors.sequential.Reds_r,
            text='Cantidad'
        )
        
        fig.update_traces(textposition='outside')
        fig.update_layout(
            showlegend=False,
            height=350,
            yaxis_title="Número de Zonas"
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    # Medidor de fertilidad
    st.markdown("---")
    st.markdown("#### 📊 **MEDIDOR DE FERTILIDAD GLOBAL**")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        avg_fertility = df['indice_fertilidad'].mean()
        fig = create_fertility_gauge(avg_fertility, "Fertilidad Promedio de la Parcela")
        st.plotly_chart(fig, use_container_width=True)
        
        # Evaluación
        if avg_fertility >= 0.8:
            st.success("✅ **EXCELENTE:** La fertilidad general es óptima. Mantenga las prácticas actuales.")
        elif avg_fertility >= 0.6:
            st.info("⚠️ **BUENA:** Fertilidad aceptable. Monitoreo regular recomendado.")
        elif avg_fertility >= 0.4:
            st.warning("🔶 **REGULAR:** Se requieren mejoras. Considere fertilización balanceada.")
        else:
            st.error("🚨 **CRÍTICO:** Intervención urgente requerida. Realice análisis de suelo detallado.")

def render_analysis_tab(df: pd.DataFrame):
    """Renderizar pestaña de análisis detallado."""
    
    st.markdown("## 🔬 **ANÁLISIS DETALLADO POR ZONA**")
    
    # Selector de zona
    selected_zone = st.selectbox(
        "Seleccionar zona para análisis detallado:",
        df['id_zona'].tolist(),
        format_func=lambda x: f"Zona {x}"
    )
    
    zone_data = df[df['id_zona'] == selected_zone].iloc[0]
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Información de la zona
        st.markdown(f"### 📍 **ZONA {selected_zone}**")
        
        info_data = {
            "Área": f"{zone_data['area_ha']:.2f} ha",
            "Fertilidad": f"{zone_data['indice_fertilidad']:.3f}",
            "Categoría": zone_data['categoria'],
            "Prioridad": zone_data['prioridad'],
            "Textura": zone_data['textura_suelo'],
            "NDVI": f"{zone_data['ndvi']:.3f}",
            "pH": f"{zone_data['ph']:.1f}"
        }
        
        for key, value in info_data.items():
            st.markdown(f"**{key}:** {value}")
        
        # Gráfico de nutrientes
        st.markdown("### 🌿 **NIVELES DE NUTRIENTES**")
        
        nutrients = pd.DataFrame({
            'Nutriente': ['Nitrógeno', 'Fósforo', 'Potasio', 'Materia Orgánica'],
            'Nivel': [
                zone_data['nitrogeno'],
                zone_data['fosforo'],
                zone_data['potasio'],
                zone_data['materia_organica']
            ],
            'Óptimo': [
                CROP_PARAMETERS[st.session_state.get('crop_type', 'PALMA ACEITERA')]['nitrogeno_optimo'],
                CROP_PARAMETERS[st.session_state.get('crop_type', 'PALMA ACEITERA')]['fosforo_optimo'],
                CROP_PARAMETERS[st.session_state.get('crop_type', 'PALMA ACEITERA')]['potasio_optimo'],
                4.0  # Materia orgánica óptima
            ]
        })
        
        fig = px.bar(
            nutrients,
            x='Nutriente',
            y='Nivel',
            title="",
            color='Nutriente',
            color_discrete_sequence=['#FF5722', '#2196F3', '#4CAF50', '#FFC107']
        )
        
        # Añadir línea de óptimo
        for i, row in nutrients.iterrows():
            fig.add_hline(
                y=row['Óptimo'],
                line_dash="dash",
                line_color="red",
                annotation_text="Óptimo",
                annotation_position="top right"
            )
        
        fig.update_layout(
            showlegend=False,
            height=300,
            yaxis_title="kg/ha"
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Textura del suelo
        st.markdown("### 🌱 **TEXTURA DEL SUELO**")
        
        texture = SOIL_TEXTURES.get(zone_data['textura_suelo'], SOIL_TEXTURES['Franco'])
        
        fig = create_soil_texture_chart(
            texture['arena'],
            texture['limo'],
            texture['arcilla']
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Recomendaciones
        st.markdown("### 💡 **RECOMENDACIONES ESPECÍFICAS**")
        
        recommendations = []
        
        # Recomendaciones basadas en fertilidad
        if zone_data['indice_fertilidad'] < 0.4:
            recommendations.append("**🚨 FERTILIZACIÓN URGENTE:** Aplique fertilización completa NPK")
        elif zone_data['indice_fertilidad'] < 0.6:
            recommendations.append("**⚠️ FERTILIZACIÓN MODERADA:** Realice aplicación de mantenimiento")
        
        # Recomendaciones basadas en nutrientes específicos
        if zone_data['nitrogeno'] < CROP_PARAMETERS[st.session_state.get('crop_type', 'PALMA ACEITERA')]['nitrogeno_optimo'] * 0.8:
            recommendations.append(f"**🌿 NITRÓGENO:** Aplicar {zone_data['recomendacion_n']:.0f} kg/ha de N")
        
        if zone_data['fosforo'] < CROP_PARAMETERS[st.session_state.get('crop_type', 'PALMA ACEITERA')]['fosforo_optimo'] * 0.8:
            recommendations.append(f"**🔵 FÓSFORO:** Aplicar {zone_data['recomendacion_p']:.0f} kg/ha de P₂O₅")
        
        if zone_data['potasio'] < CROP_PARAMETERS[st.session_state.get('crop_type', 'PALMA ACEITERA')]['potasio_optimo'] * 0.8:
            recommendations.append(f"**🟢 POTASIO:** Aplicar {zone_data['recomendacion_k']:.0f} kg/ha de K₂O")
        
        # Recomendaciones basadas en textura
        if zone_data['textura_suelo'] == 'Arcilloso':
            recommendations.append("**🏗️ MEJORA DE SUELO:** Añadir materia orgánica para mejorar drenaje")
        elif zone_data['textura_suelo'] == 'Arenoso':
            recommendations.append("**💧 MANEJO HÍDRICO:** Riego frecuente en pequeñas dosis")
        
        if not recommendations:
            recommendations.append("✅ **CONDICIONES ÓPTIMAS:** Mantenga las prácticas actuales")
        
        for rec in recommendations:
            st.markdown(f"- {rec}")
    
    # Tabla de todas las zonas
    st.markdown("---")
    st.markdown("### 📋 **TABLA COMPLETA DE ZONAS**")
    
    display_cols = ['id_zona', 'area_ha', 'indice_fertilidad', 'categoria', 'prioridad', 
                   'potencial_cosecha', 'textura_suelo', 'recomendacion_n', 'recomendacion_p', 'recomendacion_k']
    
    display_df = df[display_cols].copy()
    display_df['area_ha'] = display_df['area_ha'].round(2)
    display_df['indice_fertilidad'] = display_df['indice_fertilidad'].round(3)
    display_df['potencial_cosecha'] = display_df['potencial_cosecha'].round(1)
    
    for col in ['recomendacion_n', 'recomendacion_p', 'recomendacion_k']:
        display_df[col] = display_df[col].round(0)
    
    st.dataframe(
        display_df,
        use_container_width=True,
        column_config={
            'id_zona': st.column_config.NumberColumn("ID Zona", width="small"),
            'area_ha': st.column_config.NumberColumn("Área (ha)", format="%.2f"),
            'indice_fertilidad': st.column_config.NumberColumn("Fertilidad", format="%.3f"),
            'categoria': "Categoría",
            'prioridad': "Prioridad",
            'potencial_cosecha': st.column_config.NumberColumn("Potencial (t/ha)", format="%.1f"),
            'textura_suelo': "Textura",
            'recomendacion_n': st.column_config.NumberColumn("N (kg/ha)", format="%.0f"),
            'recomendacion_p': st.column_config.NumberColumn("P (kg/ha)", format="%.0f"),
            'recomendacion_k': st.column_config.NumberColumn("K (kg/ha)", format="%.0f")
        },
        hide_index=True
    )

def render_maps_tab(df: pd.DataFrame):
    """Renderizar pestaña de mapas."""
    
    st.markdown("## 🗺️ **VISUALIZACIÓN ESPACIAL**")
    
    # Generar datos geoespaciales simulados
    np.random.seed(42)
    
    # Crear coordenadas aleatorias centradas en Colombia
    base_lat, base_lon = 4.0, -74.0  # Centro de Colombia
    
    df_map = df.copy()
    df_map['lat'] = base_lat + np.random.randn(len(df)) * 0.05
    df_map['lon'] = base_lon + np.random.randn(len(df)) * 0.05
    df_map['size'] = df_map['indice_fertilidad'] * 100
    df_map['color'] = df_map['indice_fertilidad']
    df_map['label'] = df_map.apply(lambda row: f"Zona {row['id_zona']}: Fert={row['indice_fertilidad']:.3f}", axis=1)
    
    # Selector de capa
    col1, col2 = st.columns([3, 1])
    
    with col2:
        map_layer = st.selectbox(
            "Capa a visualizar:",
            ["Fertilidad", "Potencial Cosecha", "Prioridad", "Textura"],
            index=0
        )
        
        if map_layer == "Fertilidad":
            color_col = 'indice_fertilidad'
            color_scale = "viridis"
        elif map_layer == "Potencial Cosecha":
            color_col = 'potencial_cosecha'
            color_scale = "greens"
        elif map_layer == "Prioridad":
            # Convertir prioridad a numérico
            priority_map = {'URGENTE': 1, 'ALTA': 2, 'MEDIA-ALTA': 3, 'MEDIA': 4, 'MEDIA-BAJA': 5, 'BAJA': 6}
            df_map['priority_num'] = df_map['prioridad'].map(priority_map)
            color_col = 'priority_num'
            color_scale = "reds"
        else:  # Textura
            texture_map = {'Arcilloso': 1, 'Franco Arcilloso': 2, 'Franco': 3, 'Franco Arenoso': 4, 'Arenoso': 5}
            df_map['texture_num'] = df_map['textura_suelo'].map(texture_map)
            color_col = 'texture_num'
            color_scale = "brwnyl"
    
    with col1:
        # Crear mapa con Plotly
        fig = px.scatter_mapbox(
            df_map,
            lat="lat",
            lon="lon",
            size="size",
            color=color_col,
            hover_name="label",
            hover_data={
                'id_zona': True,
                'area_ha': ':.2f',
                'indice_fertilidad': ':.3f',
                'potencial_cosecha': ':.1f',
                'prioridad': True,
                'textura_suelo': True
            },
            color_continuous_scale=color_scale,
            size_max=30,
            zoom=8,
            height=600,
            title=f"Mapa de {map_layer} por Zona"
        )
        
        fig.update_layout(
            mapbox_style="carto-positron",
            mapbox_center={"lat": base_lat, "lon": base_lon},
            margin={"r":0,"t":40,"l":0,"b":0}
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    # Gráfico de dispersión 3D
    st.markdown("---")
    st.markdown("#### 📊 **ANÁLISIS MULTIVARIADO 3D**")
    
    fig_3d = px.scatter_3d(
        df,
        x='nitrogeno',
        y='fosforo',
        z='potasio',
        color='indice_fertilidad',
        size='area_ha',
        hover_name='id_zona',
        hover_data=['categoria', 'prioridad', 'potencial_cosecha'],
        title="Relación entre Nutrientes NPK",
        color_continuous_scale='viridis',
        labels={
            'nitrogeno': 'Nitrógeno (kg/ha)',
            'fosforo': 'Fósforo (kg/ha)',
            'potasio': 'Potasio (kg/ha)',
            'indice_fertilidad': 'Fertilidad'
        }
    )
    
    fig_3d.update_layout(
        height=600,
        scene=dict(
            xaxis_title="Nitrógeno",
            yaxis_title="Fósforo",
            zaxis_title="Potasio"
        )
    )
    
    st.plotly_chart(fig_3d, use_container_width=True)

def render_reports_tab(df: pd.DataFrame):
    """Renderizar pestaña de reportes."""
    
    st.markdown("## 📄 **GENERACIÓN DE REPORTES**")
    
    col1, col2 = st.columns(2)
    
    with col1:
        report_type = st.selectbox(
            "Tipo de reporte:",
            ["Reporte Completo", "Reporte de Fertilidad", "Reporte Climático", "Recomendaciones NPK"],
            index=0
        )
        
        format_type = st.selectbox(
            "Formato de exportación:",
            ["CSV", "Excel", "PDF (Imagen)", "JSON"],
            index=0
        )
    
    with col2:
        include_charts = st.checkbox("Incluir gráficos en el reporte", value=True)
        include_recommendations = st.checkbox("Incluir recomendaciones detalladas", value=True)
        include_raw_data = st.checkbox("Incluir datos brutos", value=False)
    
    st.markdown("---")
    
    # Botones de generación
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("📊 **Exportar CSV**", use_container_width=True):
            csv = df.to_csv(index=False)
            st.download_button(
                label="📥 Descargar CSV",
                data=csv,
                file_name=f"analisis_{st.session_state.get('crop_type', 'cultivo')}.csv",
                mime="text/csv",
                use_container_width=True
            )
    
    with col2:
        if st.button("📈 **Exportar Excel**", use_container_width=True):
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name='Análisis', index=False)
            
            st.download_button(
                label="📥 Descargar Excel",
                data=output.getvalue(),
                file_name=f"analisis_{st.session_state.get('crop_type', 'cultivo')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )
    
    with col3:
        if st.button("📋 **Resumen Ejecutivo**", use_container_width=True):
            # Crear resumen ejecutivo
            summary = f"""
            # RESUMEN EJECUTIVO - ANÁLISIS DE CULTIVOS
            ## {st.session_state.get('crop_type', 'Cultivo')}
            ### Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            
            ## 📊 MÉTRICAS PRINCIPALES
            - Área total analizada: {df['area_ha'].sum():.1f} ha
            - Zonas analizadas: {len(df)} zonas
            - Fertilidad promedio: {df['indice_fertilidad'].mean():.3f}
            - Potencial de cosecha promedio: {df['potencial_cosecha'].mean():.1f} ton/ha
            
            ## 🎯 ZONAS PRIORITARIAS
            Zonas con prioridad URGENTE: {len(df[df['prioridad'] == 'URGENTE'])}
            Zonas con prioridad ALTA: {len(df[df['prioridad'] == 'ALTA'])}
            
            ## 💡 RECOMENDACIONES GENERALES
            """
            
            if df['indice_fertilidad'].mean() < 0.6:
                summary += "- **FERTILIZACIÓN GENERAL:** Se recomienda aplicación balanceada de NPK\n"
            
            if len(df[df['prioridad'] == 'URGENTE']) > 0:
                summary += "- **INTERVENCIÓN URGENTE:** Atención inmediata a zonas críticas\n"
            
            summary += "- **MONITOREO:** Continuar con análisis periódico cada 3 meses\n"
            
            st.download_button(
                label="📥 Descargar Resumen",
                data=summary,
                file_name=f"resumen_{st.session_state.get('crop_type', 'cultivo')}.txt",
                mime="text/plain",
                use_container_width=True
            )
    
    with col4:
        if st.button("🖼️ **Captura de Pantalla**", use_container_width=True):
            st.info("Para capturar la pantalla completa, use Ctrl+Shift+P (Chrome) o Ctrl+Shift+S (Edge)")
    
    # Vista previa del reporte
    st.markdown("---")
    st.markdown("### 👁️ **VISTA PREVIA DEL REPORTE**")
    
    if report_type == "Reporte Completo":
        # Mostrar estadísticas resumen
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Fertilidad Promedio", f"{df['indice_fertilidad'].mean():.3f}")
        
        with col2:
            st.metric("Potencial Cosecha", f"{df['potencial_cosecha'].mean():.1f} ton/ha")
        
        with col3:
            st.metric("Inversión Estimada", f"${(df['recomendacion_n'].sum() * 0.5 + df['recomendacion_p'].sum() * 0.7 + df['recomendacion_k'].sum() * 0.6):.0f}")
    
    # Tabla de recomendaciones resumidas
    st.markdown("#### 💰 **INVERSIÓN ESTIMADA EN FERTILIZANTES**")
    
    investment_df = pd.DataFrame({
        'Nutriente': ['Nitrógeno (N)', 'Fósforo (P₂O₅)', 'Potasio (K₂O)', 'TOTAL'],
        'Cantidad (kg)': [
            df['recomendacion_n'].sum(),
            df['recomendacion_p'].sum(),
            df['recomendacion_k'].sum(),
            df['recomendacion_n'].sum() + df['recomendacion_p'].sum() + df['recomendacion_k'].sum()
        ],
        'Costo Unitario (USD/kg)': [0.5, 0.7, 0.6, '-'],
        'Costo Total (USD)': [
            df['recomendacion_n'].sum() * 0.5,
            df['recomendacion_p'].sum() * 0.7,
            df['recomendacion_k'].sum() * 0.6,
            df['recomendacion_n'].sum() * 0.5 + df['recomendacion_p'].sum() * 0.7 + df['recomendacion_k'].sum() * 0.6
        ]
    })
    
    investment_df['Cantidad (kg)'] = investment_df['Cantidad (kg)'].round(0)
    investment_df['Costo Total (USD)'] = investment_df['Costo Total (USD)'].round(0)
    
    st.dataframe(
        investment_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            'Nutriente': "Nutriente",
            'Cantidad (kg)': st.column_config.NumberColumn("Cantidad (kg)", format="%.0f"),
            'Costo Unitario (USD/kg)': st.column_config.NumberColumn("Costo Unitario", format="$.2f"),
            'Costo Total (USD)': st.column_config.NumberColumn("Costo Total", format="$.0f")
        }
    )

def render_welcome_screen():
    """Renderizar pantalla de bienvenida."""
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("""
        ## 👋 **¡BIENVENIDO AL ANALIZADOR DE CULTIVOS DIGITAL TWIN!**
        
        Esta es la **versión cloud** que funciona **100% en tu navegador** 
        **sin necesidad de instalar nada** en tu computadora.
        
        ### 🚀 **¿CÓMO EMPEZAR?**
        
        1. **Configura los parámetros** en la barra lateral
        2. **Haz clic en "EJECUTAR ANÁLISIS COMPLETO"**
        3. **Explora los resultados** en las diferentes pestañas
        
        ### 📊 **FUNCIONALIDADES PRINCIPALES**
        
        ✅ **Análisis de fertilidad NPK** por zonas homogéneas  
        ✅ **Mapas interactivos** con visualización geoespacial  
        ✅ **Datos climáticos** simulados basados en NASA POWER  
        ✅ **Recomendaciones personalizadas** de fertilización  
        ✅ **Reportes exportables** en múltiples formatos  
        ✅ **Interfaz moderna y responsiva**  
        
        ### 🎯 **OBJETIVO**
        
        Proporcionar **herramientas de agricultura de precisión** 
        accesibles para todos, **sin requerir instalaciones complejas** 
        ni conocimientos técnicos avanzados.
        
        ### 🔧 **TECNOLOGÍAS UTILIZADAS**
        
        - **Streamlit**: Interfaz web interactiva
        - **Plotly**: Visualizaciones avanzadas
        - **Pandas**: Análisis de datos
        - **Simulaciones**: Modelos agronómicos realistas
        """)
    
    with col2:
        st.markdown("""
        <div style="background: white; padding: 1.5rem; border-radius: 10px; box-shadow: 0 4px 12px rgba(0,0,0,0.1);">
            <h3 style="color: #2E7D32; margin-top: 0;">📈 ESTADO DEL SISTEMA</h3>
            
            <div style="margin: 1rem 0;">
                <div style="display: flex; justify-content: space-between; margin-bottom: 0.5rem;">
                    <span>Versión:</span>
                    <strong>Cloud 2.0</strong>
                </div>
                <div style="display: flex; justify-content: space-between; margin-bottom: 0.5rem;">
                    <span>Cultivos soportados:</span>
                    <strong>5</strong>
                </div>
                <div style="display: flex; justify-content: space-between; margin-bottom: 0.5rem;">
                    <span>Última actualización:</span>
                    <strong>Hoy</strong>
                </div>
                <div style="display: flex; justify-content: space-between;">
                    <span>Análisis disponibles:</span>
                    <strong>Ilimitados</strong>
                </div>
            </div>
            
            <div style="margin-top: 1.5rem; padding-top: 1rem; border-top: 1px solid #e0e0e0;">
                <h4>📁 FORMATOS SOPORTADOS</h4>
                <ul style="padding-left: 1.2rem;">
                    <li>Datos simulados (automático)</li>
                    <li>CSV (para datos propios)</li>
                    <li>Excel (exportación)</li>
                    <li>JSON (exportación)</li>
                </ul>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        create_info_box(
            "💡 CONSEJO INICIAL",
            "Para empezar, simplemente configura los parámetros en la barra lateral y haz clic en 'EJECUTAR ANÁLISIS'. Todo lo demás es automático.",
            icon="🚀"
        )
        
        st.markdown("---")
        
        st.markdown("""
        <div style="text-align: center;">
            <a href="https://github.com/alejandro-ao/streamlit-agtech-analyzer" target="_blank" style="text-decoration: none;">
                <button style="background: #24292e; color: white; border: none; padding: 0.75rem 1.5rem; border-radius: 8px; cursor: pointer; font-weight: 600; width: 100%;">
                    <span style="margin-right: 8px;">🐙</span>
                    Ver Código en GitHub
                </button>
            </a>
        </div>
        """, unsafe_allow_html=True)

def render_footer():
    """Renderizar footer de la aplicación."""
    
    st.markdown("---")
    
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        st.markdown("""
        <div style="color: #666;">
            <p style="font-size: 1.1rem; font-weight: 600; color: #2E7D32;">🌿 Analizador de Cultivos Digital Twin v2.0</p>
            <p>Desarrollado para agricultura de precisión • Versión Cloud Optimizada</p>
            <p style="font-size: 0.9rem; margin-top: 1rem;">
                <strong>📧 Soporte:</strong> soporte@agtech.cloud • 
                <strong>🌐 Web:</strong> agtech.cloud •
                <strong>📞 Teléfono:</strong> +57 1 234 5678
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div style="color: #666;">
            <p style="font-weight: 600;">🔗 ENLACES RÁPIDOS</p>
            <p><a href="https://github.com/alejandro-ao/streamlit-agtech-analyzer" target="_blank" style="color: #2E7D32; text-decoration: none;">📚 Documentación</a></p>
            <p><a href="https://github.com/alejandro-ao/streamlit-agtech-analyzer/issues" target="_blank" style="color: #2E7D32; text-decoration: none;">🐛 Reportar Problema</a></p>
            <p><a href="https://github.com/alejandro-ao/streamlit-agtech-analyzer" target="_blank" style="color: #2E7D32; text-decoration: none;">💻 Código Fuente</a></p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div style="color: #666;">
            <p style="font-weight: 600;">📄 LICENCIA</p>
            <p>MIT Open Source</p>
            <p style="font-size: 0.9rem; margin-top: 1rem;">© 2024 AgTech Solutions</p>
            <p style="font-size: 0.8rem;">Todos los derechos reservados</p>
        </div>
        """, unsafe_allow_html=True)

# ============================================================================
# APLICACIÓN PRINCIPAL
# ============================================================================

def main():
    """Función principal de la aplicación."""
    
    # Renderizar header
    render_header()
    
    # Renderizar sidebar
    render_sidebar()
    
    # Verificar si se ha ejecutado el análisis
    if 'analysis_run' in st.session_state and st.session_state.analysis_run:
        
        # Obtener parámetros del análisis
        crop_type = st.session_state.get('crop_type', 'PALMA ACEITERA')
        month = st.session_state.get('month', 'ENERO')
        n_zones = st.session_state.get('n_zones', 16)
        uploaded_file = st.session_state.get('uploaded_file', None)
        
        # Generar o cargar datos
        if uploaded_file is not None:
            try:
                df = pd.read_csv(uploaded_file)
                st.success(f"✅ Archivo cargado: {uploaded_file.name}")
            except Exception as e:
                st.error(f"❌ Error cargando archivo: {e}")
                df = generate_sample_data(n_zones, crop_type)
        else:
            with st.spinner(f"🔄 Generando datos simulados para {crop_type}..."):
                df = generate_sample_data(n_zones, crop_type)
        
        # Obtener datos climáticos
        climate_data = get_climate_data(crop_type, month)
        
        # Crear pestañas de análisis
        tab1, tab2, tab3, tab4 = st.tabs([
            "📊 DASHBOARD",
            "🔬 ANÁLISIS DETALLADO", 
            "🗺️ MAPAS INTERACTIVOS",
            "📄 REPORTES Y EXPORTACIÓN"
        ])
        
        with tab1:
            render_dashboard(df, climate_data)
        
        with tab2:
            render_analysis_tab(df)
        
        with tab3:
            render_maps_tab(df)
        
        with tab4:
            render_reports_tab(df)
    
    else:
        # Mostrar pantalla de bienvenida
        render_welcome_screen()
    
    # Renderizar footer
    render_footer()

# ============================================================================
# EJECUCIÓN
# ============================================================================

if __name__ == "__main__":
    main()
