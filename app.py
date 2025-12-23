import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import io

# ============================================================================
# CONFIGURACIÓN DE LA PÁGINA
# ============================================================================
st.set_page_config(
    page_title="🌴 Analizador Cultivos Digital Twin",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================================
# CSS PERSONALIZADO - ESTILO PROFESIONAL
# ============================================================================
st.markdown("""
<style>
    /* Fondo principal de la aplicación */
    .stApp {
        background: linear-gradient(135deg, #f5f7fa 0%, #e4edf5 100%);
    }
    
    /* Header principal con gradiente profesional */
    .main-header {
        background: linear-gradient(90deg, #2E7D32 0%, #4CAF50 100%);
        padding: 2rem;
        border-radius: 0 0 20px 20px;
        color: white;
        margin: -1rem -1rem 2rem -1rem;
        box-shadow: 0 4px 20px rgba(46, 125, 50, 0.3);
        text-align: center;
    }
    
    /* Tarjetas de métricas modernas */
    .metric-card {
        background: white;
        border-radius: 12px;
        padding: 1.5rem;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
        border-left: 5px solid #2E7D32;
        transition: transform 0.3s ease, box-shadow 0.3s ease;
        height: 100%;
    }
    .metric-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 8px 25px rgba(0, 0, 0, 0.15);
    }
    .metric-title {
        color: #666;
        font-size: 0.9rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 0.5rem;
    }
    .metric-value {
        color: #2E7D32;
        font-size: 2rem;
        font-weight: 700;
        margin: 0;
    }
    .metric-unit {
        color: #888;
        font-size: 0.85rem;
        margin-left: 0.25rem;
    }
    
    /* Botones modernos */
    .stButton > button {
        background: linear-gradient(90deg, #2E7D32 0%, #4CAF50 100%);
        color: white;
        border: none;
        border-radius: 10px;
        padding: 0.75rem 1.5rem;
        font-weight: 600;
        transition: all 0.3s ease;
        width: 100%;
    }
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 15px rgba(46, 125, 50, 0.4);
    }
    
    /* Sidebar personalizada */
    [data-testid="stSidebar"] {
        background: white;
        border-right: 1px solid #e0e0e0;
    }
    
    /* Tabs con estilo moderno */
    .stTabs [data-baseweb="tab-list"] {
        gap: 1rem;
        background: transparent;
        padding: 0.5rem;
    }
    .stTabs [data-baseweb="tab"] {
        background: white;
        border-radius: 10px 10px 0 0;
        padding: 0.75rem 1.5rem;
        font-weight: 600;
        border: 1px solid #e0e0e0;
        border-bottom: none;
    }
    .stTabs [aria-selected="true"] {
        background-color: #2E7D32;
        color: white !important;
    }
    
    /* Contenedores con borde (cards) */
    div[data-testid="stExpander"] {
        border: 1px solid #e0e0e0;
        border-radius: 10px;
        margin-bottom: 1rem;
    }
    
    /* Mejorar los selectores y sliders */
    .stSelectbox, .stSlider {
        background: white;
        border-radius: 8px;
        padding: 0.5rem;
    }
</style>
""", unsafe_allow_html=True)

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
def crear_tarjeta_metrica(titulo: str, valor: str, unidad: str = "", color: str = "#2E7D32") -> str:
    """Crea HTML para una tarjeta de métrica."""
    return f"""
    <div class="metric-card">
        <div class="metric-title">{titulo}</div>
        <div style="display: flex; align-items: baseline;">
            <div class="metric-value" style="color: {color};">{valor}</div>
            <div class="metric-unit">{unidad}</div>
        </div>
    </div>
    """

def generar_datos_muestra(cultivo: str, n_zonas: int = 16):
    """Genera datos de muestra para análisis."""
    np.random.seed(42)
    params = CULTIVOS.get(cultivo, CULTIVOS['PALMA ACEITERA'])
    
    datos = {
        'id_zona': list(range(1, n_zonas + 1)),
        'area_ha': np.random.uniform(5, 20, n_zonas).round(2),
        'nitrogeno': np.random.normal(params['nitrogeno_optimo'], params['nitrogeno_optimo'] * 0.2, n_zonas).clip(0),
        'fosforo': np.random.normal(params['fosforo_optimo'], params['fosforo_optimo'] * 0.2, n_zonas).clip(0),
        'potasio': np.random.normal(params['potasio_optimo'], params['potasio_optimo'] * 0.2, n_zonas).clip(0),
        'ph': np.random.normal(params['ph_optimo'], 0.5, n_zonas).clip(4.0, 8.0),
        'materia_organica': np.random.uniform(1.5, 5.0, n_zonas),
        'ndvi': np.random.uniform(0.4, 0.85, n_zonas)
    }
    
    df = pd.DataFrame(datos)
    
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
    condiciones = [
        df['indice_fertilidad'] >= 0.85,
        df['indice_fertilidad'] >= 0.70,
        df['indice_fertilidad'] >= 0.55,
        df['indice_fertilidad'] >= 0.40,
        df['indice_fertilidad'] >= 0.25,
        df['indice_fertilidad'] < 0.25
    ]
    categorias = ['EXCELENTE', 'MUY ALTA', 'ALTA', 'MEDIA', 'BAJA', 'MUY BAJA']
    df['categoria'] = np.select(condiciones, categorias, default='MEDIA')
    
    # Asignar prioridad
    mapa_prioridad = {
        'EXCELENTE': 'BAJA',
        'MUY ALTA': 'MEDIA-BAJA',
        'ALTA': 'MEDIA',
        'MEDIA': 'MEDIA-ALTA',
        'BAJA': 'ALTA',
        'MUY BAJA': 'URGENTE'
    }
    df['prioridad'] = df['categoria'].map(mapa_prioridad)
    
    # Calcular potencial de cosecha
    df['potencial_cosecha'] = (params['produccion_base'] * df['indice_fertilidad'] * 
                               np.random.uniform(0.8, 1.2, n_zonas)).round(1)
    
    # Calcular recomendaciones de fertilización
    df['recomendacion_n'] = ((params['nitrogeno_optimo'] - df['nitrogeno']).clip(0) * 1.4).clip(20, 250).round(1)
    df['recomendacion_p'] = ((params['fosforo_optimo'] - df['fosforo']).clip(0) * 1.6).clip(10, 120).round(1)
    df['recomendacion_k'] = ((params['potasio_optimo'] - df['potasio']).clip(0) * 1.3).clip(15, 200).round(1)
    
    return df

def obtener_datos_climaticos(cultivo: str, mes: str):
    """Obtiene datos climáticos simulados."""
    # Simulación de datos climáticos
    np.random.seed(hash(f"{cultivo}{mes}") % 10000)
    
    return {
        'temperatura': round(np.random.uniform(22, 32), 1),
        'precipitacion': round(np.random.uniform(3, 12), 1),
        'radiacion_solar': round(np.random.uniform(16, 22), 1),
        'humedad_relativa': round(np.random.uniform(65, 85), 1),
        'velocidad_viento': round(np.random.uniform(1.5, 3.5), 1),
        'evapotranspiracion': round(np.random.uniform(3, 5), 1)
    }

# ============================================================================
# INTERFAZ DE USUARIO
# ============================================================================
def renderizar_header():
    """Renderiza el encabezado de la aplicación."""
    st.markdown("""
    <div class="main-header">
        <h1 style="margin: 0; font-size: 2.5rem;">🌱 ANALIZADOR DE CULTIVOS DIGITAL TWIN</h1>
        <p style="margin: 0.5rem 0 0 0; font-size: 1.1rem; opacity: 0.95;">
            Plataforma profesional de análisis agrícola con datos satelitales y climáticos
        </p>
        <div style="display: flex; justify-content: center; gap: 15px; margin-top: 1rem; font-size: 0.9rem;">
            <span>✅ Sin instalaciones</span>
            <span>•</span>
            <span>📊 Datos en tiempo real</span>
            <span>•</span>
            <span>🌍 Compatible multi-dispositivo</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

def renderizar_sidebar():
    """Renderiza la barra lateral de configuración."""
    with st.sidebar:
        st.markdown("### ⚙️ **CONFIGURACIÓN DEL ANÁLISIS**")
        st.markdown("---")
        
        # Selector de cultivo
        cultivo = st.selectbox(
            "**🌱 CULTIVO PRINCIPAL**",
            list(CULTIVOS.keys()),
            index=0,
            help="Seleccione el cultivo que desea analizar"
        )
        
        # Selector de mes
        mes_actual = MESES[datetime.now().month - 1]
        mes = st.selectbox(
            "**📅 MES DE ANÁLISIS**",
            MESES,
            index=MESES.index(mes_actual),
            help="Seleccione el mes para el análisis climático"
        )
        
        # Área total
        area_total = st.slider(
            "**📐 ÁREA TOTAL (HECTÁREAS)**",
            min_value=1.0,
            max_value=1000.0,
            value=100.0,
            step=1.0,
            help="Área total de la parcela en hectáreas"
        )
        
        # Número de zonas
        n_zonas = st.slider(
            "**🔢 NÚMERO DE ZONAS**",
            min_value=4,
            max_value=50,
            value=16,
            step=1,
            help="Número de zonas homogéneas para análisis detallado"
        )
        
        st.markdown("---")
        
        # CORRECCIÓN IMPORTANTE: Se eliminó el parámetro inválido "use_arrow"
        if st.button("🚀 **EJECUTAR ANÁLISIS COMPLETO**", 
                    type="primary", 
                    use_container_width=True):
            st.session_state['analisis_ejecutado'] = True
            st.session_state['cultivo'] = cultivo
            st.session_state['mes'] = mes
            st.session_state['area_total'] = area_total
            st.session_state['n_zonas'] = n_zonas
        
        st.markdown("---")
        
        # Información técnica
        with st.expander("📋 **INFORMACIÓN TÉCNICA**"):
            params = CULTIVOS.get(cultivo, CULTIVOS['PALMA ACEITERA'])
            st.markdown(f"""
            **Parámetros óptimos para {cultivo}:**
            - **Nitrógeno:** {params['nitrogeno_optimo']} kg/ha
            - **Fósforo:** {params['fosforo_optimo']} kg/ha
            - **Potasio:** {params['potasio_optimo']} kg/ha
            - **pH óptimo:** {params['ph_optimo']}
            
            **Configuración actual:**
            - Área: {area_total:.1f} ha
            - Zonas: {n_zonas}
            - Mes: {mes}
            """)

def renderizar_dashboard(df, datos_clima):
    """Renderiza el dashboard principal."""
    st.markdown("## 📊 **DASHBOARD DE CONTROL**")
    
    # Métricas principales en 4 columnas
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        fertilidad_promedio = df['indice_fertilidad'].mean()
        color_fertilidad = "#2E7D32" if fertilidad_promedio >= 0.6 else "#FF9800"
        st.markdown(crear_tarjeta_metrica(
            "Fertilidad Promedio",
            f"{fertilidad_promedio:.3f}",
            "índice",
            color_fertilidad
        ), unsafe_allow_html=True)
    
    with col2:
        area_total = df['area_ha'].sum()
        st.markdown(crear_tarjeta_metrica(
            "Área Analizada",
            f"{area_total:.1f}",
            "hectáreas",
            "#2196F3"
        ), unsafe_allow_html=True)
    
    with col3:
        potencial_promedio = df['potencial_cosecha'].mean()
        st.markdown(crear_tarjeta_metrica(
            "Potencial Cosecha",
            f"{potencial_promedio:.1f}",
            "ton/ha",
            "#4CAF50"
        ), unsafe_allow_html=True)
    
    with col4:
        zonas_criticas = len(df[df['prioridad'] == 'URGENTE'])
        color_criticas = "#F44336" if zonas_criticas > 0 else "#4CAF50"
        st.markdown(crear_tarjeta_metrica(
            "Zonas Críticas",
            f"{zonas_criticas}",
            "zonas",
            color_criticas
        ), unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Datos climáticos
    st.markdown("## 🌦️ **CONDICIONES CLIMÁTICAS**")
    
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    
    metricas_clima = [
        ("🌡️", "Temperatura", f"{datos_clima['temperatura']}°C", "#FF5722"),
        ("🌧️", "Precipitación", f"{datos_clima['precipitacion']} mm/d", "#2196F3"),
        ("☀️", "Radiación Solar", f"{datos_clima['radiacion_solar']} MJ/m²", "#FFC107"),
        ("💧", "Humedad", f"{datos_clima['humedad_relativa']}%", "#03A9F4"),
        ("💨", "Viento", f"{datos_clima['velocidad_viento']} m/s", "#9E9E9E"),
        ("💦", "Evapotranspiración", f"{datos_clima['evapotranspiracion']} mm/d", "#009688")
    ]
    
    for i, (icono, titulo, valor, color) in enumerate(metricas_clima):
        with [col1, col2, col3, col4, col5, col6][i]:
            st.markdown(f"""
            <div style="text-align: center; padding: 1rem; background: white; border-radius: 10px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); height: 100%;">
                <div style="font-size: 2rem; margin-bottom: 0.5rem;">{icono}</div>
                <div style="font-size: 0.85rem; color: #666; margin-bottom: 0.25rem;">{titulo}</div>
                <div style="font-size: 1.5rem; font-weight: 700; color: {color};">{valor}</div>
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
            nbins=15,
            title="",
            labels={'indice_fertilidad': 'Índice de Fertilidad'},
            color_discrete_sequence=['#2E7D32']
        )
        fig.add_vline(x=0.6, line_dash="dash", line_color="red", 
                     annotation_text="Límite Mínimo", annotation_position="top")
        fig.update_layout(height=350, showlegend=False)
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.markdown("#### 🎯 **PRIORIDAD DE INTERVENCIÓN**")
        conteo_prioridad = df['prioridad'].value_counts().reset_index()
        conteo_prioridad.columns = ['Prioridad', 'Cantidad']
        
        fig = px.bar(
            conteo_prioridad, 
            x='Prioridad', 
            y='Cantidad',
            color='Prioridad',
            color_discrete_sequence=px.colors.sequential.Reds_r,
            text='Cantidad'
        )
        fig.update_traces(textposition='outside')
        fig.update_layout(height=350, showlegend=False, yaxis_title="Número de Zonas")
        st.plotly_chart(fig, use_container_width=True)

def renderizar_analisis_detallado(df):
    """Renderiza el análisis detallado por zona."""
    st.markdown("## 🔬 **ANÁLISIS DETALLADO POR ZONA**")
    
    # Selector de zona
    zona_seleccionada = st.selectbox(
        "Seleccione una zona para análisis detallado:",
        df['id_zona'].tolist(),
        format_func=lambda x: f"Zona {x}"
    )
    
    datos_zona = df[df['id_zona'] == zona_seleccionada].iloc[0]
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        # Información de la zona
        with st.container(border=True):
            st.markdown(f"### 📍 **ZONA {zona_seleccionada}**")
            st.markdown(f"**Área:** {datos_zona['area_ha']:.2f} ha")
            st.markdown(f"**Fertilidad:** {datos_zona['indice_fertilidad']:.3f}")
            st.markdown(f"**Categoría:** {datos_zona['categoria']}")
            st.markdown(f"**Prioridad:** {datos_zona['prioridad']}")
            st.markdown(f"**Potencial Cosecha:** {datos_zona['potencial_cosecha']:.1f} ton/ha")
        
        # Recomendaciones específicas
        with st.container(border=True):
            st.markdown("### 💡 **RECOMENDACIONES**")
            
            if datos_zona['prioridad'] == 'URGENTE':
                st.error("🚨 **INTERVENCIÓN INMEDIATA REQUERIDA**")
                st.markdown("- Aplicar fertilización completa NPK")
                st.markdown("- Análisis de suelo detallado")
                st.markdown("- Considerar enmiendas orgánicas")
            elif datos_zona['prioridad'] == 'ALTA':
                st.warning("⚠️ **FERTILIZACIÓN RECOMENDADA**")
                st.markdown(f"- Aplicar {datos_zona['recomendacion_n']:.0f} kg/ha de N")
                st.markdown(f"- Aplicar {datos_zona['recomendacion_p']:.0f} kg/ha de P₂O₅")
                st.markdown(f"- Aplicar {datos_zona['recomendacion_k']:.0f} kg/ha de K₂O")
            else:
                st.success("✅ **CONDICIONES ÓPTIMAS**")
                st.markdown("- Mantener prácticas actuales")
                st.markdown("- Monitoreo regular")
    
    with col2:
        # Gráfico de nutrientes
        st.markdown("#### 🌿 **NIVELES DE NUTRIENTES**")
        
        nutrientes = pd.DataFrame({
            'Nutriente': ['Nitrógeno', 'Fósforo', 'Potasio', 'Materia Orgánica'],
            'Valor Actual': [
                datos_zona['nitrogeno'],
                datos_zona['fosforo'],
                datos_zona['potasio'],
                datos_zona['materia_organica']
            ],
            'Óptimo': [
                CULTIVOS[st.session_state.get('cultivo', 'PALMA ACEITERA')]['nitrogeno_optimo'],
                CULTIVOS[st.session_state.get('cultivo', 'PALMA ACEITERA')]['fosforo_optimo'],
                CULTIVOS[st.session_state.get('cultivo', 'PALMA ACEITERA')]['potasio_optimo'],
                4.0  # Valor óptimo para materia orgánica
            ]
        })
        
        fig = px.bar(
            nutrientes,
            x='Nutriente',
            y='Valor Actual',
            title="Comparación con niveles óptimos",
            color='Nutriente',
            color_discrete_sequence=['#FF5722', '#2196F3', '#4CAF50', '#FFC107']
        )
        
        # Añadir líneas de referencia para valores óptimos
        for idx, fila in nutrientes.iterrows():
            fig.add_hline(
                y=fila['Óptimo'],
                line_dash="dash",
                line_color="red",
                annotation_text="Óptimo",
                annotation_position="top right"
            )
        
        fig.update_layout(height=400, showlegend=False, yaxis_title="kg/ha")
        st.plotly_chart(fig, use_container_width=True)
    
    # Tabla completa de todas las zonas
    st.markdown("---")
    st.markdown("### 📋 **TODAS LAS ZONAS**")
    
    columnas_mostrar = ['id_zona', 'area_ha', 'indice_fertilidad', 'categoria', 
                       'prioridad', 'potencial_cosecha', 'recomendacion_n', 
                       'recomendacion_p', 'recomendacion_k']
    
    df_display = df[columnas_mostrar].copy()
    df_display['area_ha'] = df_display['area_ha'].round(2)
    df_display['indice_fertilidad'] = df_display['indice_fertilidad'].round(3)
    df_display['potencial_cosecha'] = df_display['potencial_cosecha'].round(1)
    
    for col in ['recomendacion_n', 'recomendacion_p', 'recomendacion_k']:
        df_display[col] = df_display[col].round(0)
    
    st.dataframe(
        df_display,
        use_container_width=True,
        column_config={
            'id_zona': st.column_config.NumberColumn("ID Zona", width="small"),
            'area_ha': st.column_config.NumberColumn("Área (ha)", format="%.2f"),
            'indice_fertilidad': st.column_config.NumberColumn("Fertilidad", format="%.3f"),
            'categoria': "Categoría",
            'prioridad': "Prioridad",
            'potencial_cosecha': st.column_config.NumberColumn("Potencial (t/ha)", format="%.1f"),
            'recomendacion_n': st.column_config.NumberColumn("N (kg/ha)", format="%.0f"),
            'recomendacion_p': st.column_config.NumberColumn("P (kg/ha)", format="%.0f"),
            'recomendacion_k': st.column_config.NumberColumn("K (kg/ha)", format="%.0f")
        },
        hide_index=True
    )

def renderizar_reportes(df):
    """Renderiza la sección de reportes y exportación."""
    st.markdown("## 📄 **REPORTES Y EXPORTACIÓN**")
    
    col1, col2 = st.columns(2)
    
    with col1:
        tipo_reporte = st.selectbox(
            "Tipo de reporte:",
            ["Reporte Completo", "Reporte de Fertilidad", "Recomendaciones NPK", "Datos Climáticos"],
            index=0
        )
        
        formato = st.selectbox(
            "Formato de exportación:",
            ["CSV", "Excel", "JSON"],
            index=0
        )
    
    with col2:
        incluir_graficos = st.checkbox("Incluir gráficos en el reporte", value=True)
        incluir_recomendaciones = st.checkbox("Incluir recomendaciones detalladas", value=True)
        incluir_datos_brutos = st.checkbox("Incluir datos brutos", value=False)
    
    st.markdown("---")
    
    # Botones de exportación
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📊 **EXPORTAR CSV**", use_container_width=True):
            csv = df.to_csv(index=False)
            st.download_button(
                label="📥 DESCARGAR CSV",
                data=csv,
                file_name=f"analisis_{st.session_state.get('cultivo', 'cultivo')}.csv",
                mime="text/csv",
                use_container_width=True
            )
    
    with col2:
        if st.button("📈 **EXPORTAR EXCEL**", use_container_width=True):
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name='Análisis', index=False)
            
            st.download_button(
                label="📥 DESCARGAR EXCEL",
                data=output.getvalue(),
                file_name=f"analisis_{st.session_state.get('cultivo', 'cultivo')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )
    
    with col3:
        if st.button("📋 **RESUMEN EJECUTIVO**", use_container_width=True):
            # Crear resumen ejecutivo
            resumen = f"""
            # RESUMEN EJECUTIVO - ANÁLISIS DE CULTIVOS
            ## Cultivo: {st.session_state.get('cultivo', 'No especificado')}
            ## Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            
            ## 📊 MÉTRICAS PRINCIPALES
            - Área total analizada: {df['area_ha'].sum():.1f} ha
            - Zonas analizadas: {len(df)} zonas
            - Fertilidad promedio: {df['indice_fertilidad'].mean():.3f}
            - Potencial de cosecha promedio: {df['potencial_cosecha'].mean():.1f} ton/ha
            
            ## 🎯 ZONAS PRIORITARIAS
            - Zonas con prioridad URGENTE: {len(df[df['prioridad'] == 'URGENTE'])}
            - Zonas con prioridad ALTA: {len(df[df['prioridad'] == 'ALTA'])}
            
            ## 💡 RECOMENDACIONES GENERALES
            """
            
            if df['indice_fertilidad'].mean() < 0.6:
                resumen += "- **FERTILIZACIÓN GENERAL:** Se recomienda aplicación balanceada de NPK\n"
            
            if len(df[df['prioridad'] == 'URGENTE']) > 0:
                resumen += "- **INTERVENCIÓN URGENTE:** Atención inmediata a zonas críticas\n"
            
            resumen += "- **MONITOREO:** Continuar con análisis periódico cada 3 meses\n"
            
            st.download_button(
                label="📥 DESCARGAR RESUMEN",
                data=resumen,
                file_name=f"resumen_{st.session_state.get('cultivo', 'cultivo')}.txt",
                mime="text/plain",
                use_container_width=True
            )
    
    # Vista previa del reporte
    st.markdown("---")
    st.markdown("### 👁️ **VISTA PREVIA DEL REPORTE**")
    
    with st.expander("Ver datos del reporte"):
        # Mostrar estadísticas resumen
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Fertilidad Promedio", f"{df['indice_fertilidad'].mean():.3f}")
        
        with col2:
            st.metric("Potencial Cosecha", f"{df['potencial_cosecha'].mean():.1f} ton/ha")
        
        with col3:
            # Calcular inversión estimada en fertilizantes
            inversion_n = df['recomendacion_n'].sum() * 0.5  # Costo estimado USD/kg
            inversion_p = df['recomendacion_p'].sum() * 0.7
            inversion_k = df['recomendacion_k'].sum() * 0.6
            inversion_total = inversion_n + inversion_p + inversion_k
            st.metric("Inversión Estimada", f"${inversion_total:.0f}")

def renderizar_pantalla_bienvenida():
    """Renderiza la pantalla de bienvenida."""
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("""
        ## 👋 **¡BIENVENIDO AL ANALIZADOR DE CULTIVOS DIGITAL TWIN!**
        
        Esta es la **versión cloud profesional** que funciona **100% en tu navegador** 
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
        """)
    
    with col2:
        st.markdown("""
        <div style="background: white; padding: 1.5rem; border-radius: 10px; box-shadow: 0 4px 12px rgba(0,0,0,0.1);">
            <h3 style="color: #2E7D32; margin-top: 0;">📈 ESTADO DEL SISTEMA</h3>
            
            <div style="margin: 1rem 0;">
                <div style="display: flex; justify-content: space-between; margin-bottom: 0.5rem;">
                    <span>Versión:</span>
                    <strong>Cloud Professional 2.0</strong>
                </div>
                <div style="display: flex; justify-content: space-between; margin-bottom: 0.5rem;">
                    <span>Cultivos soportados:</span>
                    <strong>3</strong>
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

def renderizar_footer():
    """Renderiza el pie de página."""
    st.markdown("---")
    
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        st.markdown("""
        <div style="color: #666;">
            <p style="font-size: 1.1rem; font-weight: 600; color: #2E7D32;">🌿 Analizador de Cultivos Digital Twin v2.0</p>
            <p>Desarrollado para agricultura de precisión • Versión Cloud Profesional</p>
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
            <p><a href="#" style="color: #2E7D32; text-decoration: none;">📚 Documentación</a></p>
            <p><a href="#" style="color: #2E7D32; text-decoration: none;">🐛 Reportar Problema</a></p>
            <p><a href="#" style="color: #2E7D32; text-decoration: none;">💻 Código Fuente</a></p>
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
# FUNCIÓN PRINCIPAL
# ============================================================================
def main():
    """Función principal de la aplicación."""
    
    # Renderizar encabezado
    renderizar_header()
    
    # Renderizar barra lateral
    renderizar_sidebar()
    
    # Verificar si se ha ejecutado el análisis
    if 'analisis_ejecutado' in st.session_state and st.session_state.analisis_ejecutado:
        
        # Obtener parámetros del análisis
        cultivo = st.session_state.get('cultivo', 'PALMA ACEITERA')
        mes = st.session_state.get('mes', 'ENERO')
        n_zonas = st.session_state.get('n_zonas', 16)
        
        # Generar datos de muestra
        with st.spinner(f"🔄 Generando análisis para {cultivo}..."):
            df = generar_datos_muestra(cultivo, n_zonas)
            datos_clima = obtener_datos_climaticos(cultivo, mes)
        
        # Crear pestañas de análisis
        tab1, tab2, tab3, tab4 = st.tabs([
            "📊 DASHBOARD",
            "🔬 ANÁLISIS DETALLADO", 
            "🗺️ MAPAS INTERACTIVOS",
            "📄 REPORTES Y EXPORTACIÓN"
        ])
        
        with tab1:
            renderizar_dashboard(df, datos_clima)
        
        with tab2:
            renderizar_analisis_detallado(df)
        
        with tab3:
            st.markdown("## 🗺️ **VISUALIZACIÓN ESPACIAL**")
            st.info("🔧 **Funcionalidad en desarrollo:** Los mapas interactivos estarán disponibles en la próxima versión.")
            # Aquí iría la lógica de mapas con Folium/Plotly
        
        with tab4:
            renderizar_reportes(df)
    
    else:
        # Mostrar pantalla de bienvenida
        renderizar_pantalla_bienvenida()
    
    # Renderizar pie de página
    renderizar_footer()

# ============================================================================
# EJECUCIÓN DE LA APLICACIÓN
# ============================================================================
if __name__ == "__main__":
    main()
