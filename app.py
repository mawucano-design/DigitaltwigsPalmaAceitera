import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import io

# ============================================================================
# CONFIGURACIÓN DE LA PÁGINA - CON PREVENCIÓN DE ERRORES
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
# CSS SIMPLIFICADO - SIN EFECTOS COMPLEJOS QUE CAUSAN ERRORES
# ============================================================================
st.markdown("""
<style>
    /* ESTILOS BÁSICOS Y SEGUROS */
    .stApp {
        background-color: #f8f9fa;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    
    /* HEADER SIMPLIFICADO */
    .main-header {
        background: linear-gradient(90deg, #2E7D32 0%, #388E3C 100%);
        padding: 1.5rem 2rem;
        color: white;
        margin-bottom: 1.5rem;
        border-radius: 0 0 15px 15px;
        box-shadow: 0 4px 12px rgba(46, 125, 50, 0.2);
    }
    
    /* TARJETAS SEGURAS - SIN HOVER COMPLEJO */
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
    
    /* BOTONES ESTABLES */
    .stButton > button {
        background-color: #2E7D32;
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.7rem 1.5rem;
        font-weight: 600;
        font-size: 1rem;
        width: 100%;
        transition: background-color 0.2s ease;
    }
    
    .stButton > button:hover {
        background-color: #1B5E20;
    }
    
    /* MEJORAS PARA TABS */
    div[data-testid="stTabs"] {
        background-color: white;
        border-radius: 10px;
        padding: 0.5rem;
        margin-bottom: 1.5rem;
    }
    
    /* SIDEBAR ESTABLE */
    section[data-testid="stSidebar"] {
        background-color: white;
    }
    
    /* REMOVER EFECTOS PROBLEMÁTICOS */
    * {
        transition: none !important;
        animation: none !important;
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

def generar_datos_muestra(cultivo: str, n_zonas: int = 16):
    """Genera datos de muestra para análisis."""
    np.random.seed(42)
    params = CULTIVOS.get(cultivo, CULTIVOS['PALMA ACEITERA'])
    
    datos = {
        'id_zona': list(range(1, n_zonas + 1)),
        'area_ha': np.random.uniform(5, 20, n_zonas).round(2),
        'nitrogeno': np.random.normal(params['nitrogeno_optimo'], params['nitrogeno_optimo'] * 0.15, n_zonas).clip(0),
        'fosforo': np.random.normal(params['fosforo_optimo'], params['fosforo_optimo'] * 0.15, n_zonas).clip(0),
        'potasio': np.random.normal(params['potasio_optimo'], params['potasio_optimo'] * 0.15, n_zonas).clip(0),
        'ph': np.random.normal(params['ph_optimo'], 0.4, n_zonas).clip(4.5, 7.5),
        'materia_organica': np.random.uniform(2.0, 4.5, n_zonas),
        'ndvi': np.random.uniform(0.5, 0.85, n_zonas)
    }
    
    df = pd.DataFrame(datos)
    
    # Calcular índice de fertilidad
    df['indice_fertilidad'] = (
        (df['nitrogeno'] / params['nitrogeno_optimo'] * 0.25) +
        (df['fosforo'] / params['fosforo_optimo'] * 0.20) +
        (df['potasio'] / params['potasio_optimo'] * 0.20) +
        (df['materia_organica'] / 5.0 * 0.15) +
        (1 - abs(df['ph'] - params['ph_optimo']) / 3.0 * 0.10) +
        (df['ndvi'] * 0.10)
    ).clip(0.2, 0.95)  # Limitar para valores más realistas
    
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

def obtener_datos_climaticos(cultivo: str, mes: str):
    """Obtiene datos climáticos simulados."""
    # Simulación simple y estable
    mes_idx = MESES.index(mes) if mes in MESES else 0
    
    # Valores base según el cultivo
    if cultivo == 'PALMA ACEITERA':
        temp_base = 28.0
        precip_base = 6.0
    elif cultivo == 'CACAO':
        temp_base = 25.0
        precip_base = 8.0
    else:  # BANANO
        temp_base = 26.0
        precip_base = 7.0
    
    # Variación mensual simple
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
# INTERFAZ DE USUARIO - VERSION ESTABLE
# ============================================================================
def mostrar_header():
    """Muestra el encabezado de la aplicación."""
    st.markdown("""
    <div class="main-header">
        <h1 style="margin: 0; font-size: 2.2rem; font-weight: 700;">🌱 ANALIZADOR DE CULTIVOS</h1>
        <p style="margin: 0.5rem 0 0 0; font-size: 1rem; opacity: 0.95;">
            Plataforma de análisis agrícola con datos satelitales y climáticos
        </p>
    </div>
    """, unsafe_allow_html=True)

def mostrar_sidebar():
    """Muestra la barra lateral de configuración."""
    with st.sidebar:
        st.markdown("### ⚙️ CONFIGURACIÓN")
        st.markdown("---")
        
        cultivo = st.selectbox(
            "**Cultivo principal**",
            list(CULTIVOS.keys()),
            index=0
        )
        
        mes = st.selectbox(
            "**Mes de análisis**",
            MESES,
            index=datetime.now().month - 1
        )
        
        area_total = st.number_input(
            "**Área total (hectáreas)**",
            min_value=1.0,
            max_value=10000.0,
            value=100.0,
            step=10.0
        )
        
        n_zonas = st.slider(
            "**Número de zonas**",
            min_value=4,
            max_value=30,
            value=12,
            step=1
        )
        
        st.markdown("---")
        
        # BOTÓN CORREGIDO - sin use_arrow
        if st.button("🚀 **EJECUTAR ANÁLISIS**", type="primary", use_container_width=True):
            st.session_state['analisis_ejecutado'] = True
            st.session_state['cultivo'] = cultivo
            st.session_state['mes'] = mes
            st.session_state['area_total'] = area_total
            st.session_state['n_zonas'] = n_zonas
        
        st.markdown("---")
        
        with st.expander("ℹ️ Información"):
            params = CULTIVOS[cultivo]
            st.markdown(f"""
            **Parámetros para {cultivo}:**
            - Nitrógeno: {params['nitrogeno_optimo']} kg/ha
            - Fósforo: {params['fosforo_optimo']} kg/ha
            - Potasio: {params['potasio_optimo']} kg/ha
            - pH óptimo: {params['ph_optimo']}
            
            **Configuración actual:**
            - Área: {area_total:.1f} ha
            - Zonas: {n_zonas}
            - Mes: {mes}
            """)

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
    st.markdown("## 🔬 ANÁLISIS DETALLADO")
    
    zona_seleccionada = st.selectbox(
        "Seleccionar zona:",
        df['id_zona'].tolist(),
        format_func=lambda x: f"Zona {x}"
    )
    
    datos_zona = df[df['id_zona'] == zona_seleccionada].iloc[0]
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.markdown(f"### Zona {zona_seleccionada}")
        st.markdown(f"**Área:** {datos_zona['area_ha']:.2f} ha")
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
        
        # Barras para valores actuales
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
    st.markdown("### 📋 Resumen de Todas las Zonas")
    
    columnas = ['id_zona', 'area_ha', 'indice_fertilidad', 'categoria', 'prioridad', 'potencial_cosecha']
    df_display = df[columnas].copy()
    
    # Formatear números
    df_display['area_ha'] = df_display['area_ha'].round(2)
    df_display['indice_fertilidad'] = df_display['indice_fertilidad'].round(3)
    df_display['potencial_cosecha'] = df_display['potencial_cosecha'].round(1)
    
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

def mostrar_reportes(df):
    """Muestra la sección de reportes."""
    st.markdown("## 📄 REPORTES Y EXPORTACIÓN")
    
    col1, col2 = st.columns(2)
    
    with col1:
        tipo_reporte = st.selectbox(
            "Tipo de reporte:",
            ["Reporte Completo", "Fertilidad", "Clima", "Recomendaciones"],
            key="report_type"
        )
        
        formato = st.selectbox(
            "Formato:",
            ["CSV", "Excel", "Resumen PDF"],
            key="format_type"
        )
    
    with col2:
        st.markdown("**Opciones:**")
        incluir_detalles = st.checkbox("Incluir detalles por zona", value=True)
        incluir_graficos = st.checkbox("Incluir gráficos", value=True)
    
    st.markdown("---")
    
    # Botones de exportación
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📥 Exportar CSV", use_container_width=True):
            csv = df.to_csv(index=False, encoding='utf-8')
            st.download_button(
                label="Descargar CSV",
                data=csv,
                file_name=f"analisis_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv",
                use_container_width=True
            )
    
    with col2:
        if st.button("📊 Exportar Excel", use_container_width=True):
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name='Análisis', index=False)
            
            st.download_button(
                label="Descargar Excel",
                data=buffer.getvalue(),
                file_name=f"analisis_{datetime.now().strftime('%Y%m%d')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )
    
    # Vista previa
    st.markdown("---")
    st.markdown("### 👁️ Vista Previa del Reporte")
    
    with st.expander("Ver estadísticas"):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Fertilidad Promedio", f"{df['indice_fertilidad'].mean():.3f}")
        
        with col2:
            st.metric("Potencial Total", f"{df['potencial_cosecha'].sum():.0f} ton")
        
        with col3:
            zonas_bajas = len(df[df['categoria'].isin(['BAJA', 'MUY BAJA'])])
            st.metric("Zonas Problemáticas", zonas_bajas)

def mostrar_bienvenida():
    """Muestra pantalla de bienvenida."""
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.markdown("""
        ## 👋 ¡Bienvenido al Analizador de Cultivos!
        
        Esta plataforma permite realizar análisis avanzados de cultivos
        utilizando datos simulados basados en parámetros agronómicos reales.
        
        ### 🚀 ¿Cómo empezar?
        
        1. **Configura los parámetros** en la barra lateral
        2. **Haz clic en "EJECUTAR ANÁLISIS"**
        3. **Explora los resultados** en las diferentes secciones
        
        ### 📊 Características
        
        ✅ Análisis de fertilidad por zonas  
        ✅ Datos climáticos estacionales  
        ✅ Recomendaciones personalizadas  
        ✅ Reportes exportables  
        ✅ Interfaz moderna y estable  
        """)
    
    with col2:
        st.info("""
        **Versión:** 2.0 Estable  
        **Estado:** Listo para uso  
        **Cultivos:** 3 disponibles  
        **Actualización:** Automática  
        """)

def mostrar_footer():
    """Muestra el pie de página."""
    st.markdown("---")
    
    st.markdown("""
    <div style="text-align: center; color: #666; padding: 1rem 0;">
        <p style="margin: 0; font-size: 0.9rem;">
            🌿 <strong>Analizador de Cultivos Digital Twin</strong> | 
            Versión 2.0 Estable | 
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
    
    # Inicializar session state si no existe
    if 'analisis_ejecutado' not in st.session_state:
        st.session_state['analisis_ejecutado'] = False
    
    # Mostrar encabezado
    mostrar_header()
    
    # Mostrar barra lateral
    mostrar_sidebar()
    
    # Contenido principal basado en estado
    if st.session_state['analisis_ejecutado']:
        # Obtener parámetros
        cultivo = st.session_state.get('cultivo', 'PALMA ACEITERA')
        mes = st.session_state.get('mes', 'ENERO')
        n_zonas = st.session_state.get('n_zonas', 12)
        
        # Generar datos
        with st.spinner("🔄 Generando análisis..."):
            df = generar_datos_muestra(cultivo, n_zonas)
            datos_clima = obtener_datos_climaticos(cultivo, mes)
        
        # Crear pestañas
        tab1, tab2, tab3 = st.tabs(["📊 Dashboard", "🔬 Análisis", "📄 Reportes"])
        
        with tab1:
            mostrar_dashboard(df, datos_clima)
        
        with tab2:
            mostrar_analisis_detallado(df)
        
        with tab3:
            mostrar_reportes(df)
    
    else:
        # Pantalla de bienvenida
        mostrar_bienvenida()
    
    # Mostrar footer
    mostrar_footer()

# ============================================================================
# EJECUCIÓN
# ============================================================================
if __name__ == "__main__":
    main()
