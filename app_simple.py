# app_simple.py - Versión LIGERA para Streamlit Cloud
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import json

# Configurar página
st.set_page_config(
    page_title="🌱 Analizador Cultivos Cloud",
    page_icon="🌿",
    layout="wide"
)

# CSS personalizado
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 15px;
        color: white;
        margin-bottom: 2rem;
    }
    .metric-card {
        background: white;
        border-radius: 10px;
        padding: 1.5rem;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        border-left: 5px solid #2E7D32;
        margin: 10px 0;
    }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown("""
<div class="main-header">
    <h1>🌱 ANALIZADOR CULTIVOS - CLOUD EDITION</h1>
    <p>Versión ligera para Streamlit Cloud • Sin instalaciones</p>
</div>
""", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.title("⚙️ Configuración")
    
    cultivo = st.selectbox(
        "Selecciona cultivo:",
        ["Palma Aceitera", "Cacao", "Banano", "Café", "Maíz"]
    )
    
    hectáreas = st.slider("Área (hectáreas):", 1, 1000, 100)
    
    mes = st.selectbox("Mes de análisis:", 
                      ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
                       "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"])
    
    if st.button("🚀 Ejecutar Análisis", type="primary", use_container_width=True):
        st.session_state.analizar = True

# Contenido principal
if 'analizar' in st.session_state and st.session_state.analizar:
    # Métricas
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown("""
        <div class="metric-card">
            <h3>📐 Área</h3>
            <h1>{:.1f} ha</h1>
        </div>
        """.format(hectáreas), unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="metric-card">
            <h3>🌱 Fertilidad</h3>
            <h1>0.78</h1>
            <p>Índice NPK</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="metric-card">
            <h3>🌧️ Precipitación</h3>
            <h1>156 mm</h1>
            <p>Mensual</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown("""
        <div class="metric-card">
            <h3>📈 Potencial</h3>
            <h1>28 t/ha</h1>
            <p>Producción estimada</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Gráficos
    st.markdown("## 📊 Análisis Visual")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Gráfico de fertilidad
        data = pd.DataFrame({
            'Nutriente': ['Nitrógeno', 'Fósforo', 'Potasio', 'Materia Orgánica'],
            'Nivel': [85, 65, 78, 72],
            'Óptimo': [80, 70, 75, 75]
        })
        
        fig = px.bar(data, x='Nutriente', y='Nivel', 
                    title="Niveles de Nutrientes",
                    color='Nutriente')
        fig.add_hline(y=75, line_dash="dash", line_color="red", 
                     annotation_text="Nivel Óptimo")
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Gráfico de potencial
        meses = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 
                'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic']
        potencial = [20, 22, 25, 28, 30, 32, 30, 28, 26, 24, 22, 21]
        
        fig = px.line(x=meses, y=potencial, 
                     title="Potencial de Cosecha por Mes",
                     markers=True)
        fig.update_traces(line_color='#2E7D32', line_width=3)
        fig.update_layout(yaxis_title="Toneladas/Ha")
        st.plotly_chart(fig, use_container_width=True)
    
    # Mapa simulado
    st.markdown("## 🗺️ Distribución Espacial (Simulada)")
    
    # Generar datos aleatorios para mapa
    np.random.seed(42)
    lat = 4.0 + np.random.randn(50) * 0.1
    lon = -74.0 + np.random.randn(50) * 0.1
    fertilidad = np.random.uniform(0.3, 0.9, 50)
    
    map_data = pd.DataFrame({
        'lat': lat,
        'lon': lon,
        'fertilidad': fertilidad,
        'zona': [f"Z{i}" for i in range(50)]
    })
    
    st.map(map_data, latitude='lat', longitude='lon', size='fertilidad', 
           color='fertilidad', use_container_width=True)
    
    # Tabla de resultados
    st.markdown("## 📋 Resultados Detallados")
    
    resultados = pd.DataFrame({
        'Zona': [f'Zona {i}' for i in range(1, 11)],
        'Área (ha)': np.random.uniform(5, 20, 10).round(1),
        'Fertilidad': np.random.uniform(0.4, 0.95, 10).round(3),
        'N (kg/ha)': np.random.randint(80, 200, 10),
        'P (kg/ha)': np.random.randint(30, 90, 10),
        'K (kg/ha)': np.random.randint(120, 250, 10),
        'Prioridad': np.random.choice(['Alta', 'Media', 'Baja'], 10)
    })
    
    st.dataframe(resultados, use_container_width=True, hide_index=True)
    
    # Descargar resultados
    csv = resultados.to_csv(index=False)
    st.download_button(
        label="📥 Descargar CSV",
        data=csv,
        file_name="resultados_analisis.csv",
        mime="text/csv"
    )
    
else:
    # Pantalla de bienvenida
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("""
        ## 👋 ¡Bienvenido al Analizador Cloud!
        
        Esta es una versión **ligera y optimizada** que funciona 
        **directamente en tu navegador** sin instalar nada.
        
        ### 🚀 **Cómo usar:**
        1. Configura los parámetros en la barra lateral
        2. Haz clic en **"Ejecutar Análisis"**
        3. Explora los resultados en tiempo real
        
        ### 📊 **Características incluidas:**
        ✅ Análisis de fertilidad NPK  
        ✅ Mapas interactivos  
        ✅ Gráficos en tiempo real  
        ✅ Datos climáticos simulados  
        ✅ Exportación de resultados  
        
        ### ☁️ **Ventajas de la versión Cloud:**
        - No requiere instalación
        - Acceso desde cualquier dispositivo
        - Siempre actualizado
        - Sin consumo de recursos locales
        """)
    
    with col2:
        st.markdown("""
        <div style="background: #f0f9ff; padding: 20px; border-radius: 10px; border-left: 5px solid #2196F3;">
            <h3>📈 Estado del Sistema</h3>
            <p><strong>Versión:</strong> Cloud 2.0</p>
            <p><strong>Última actualización:</strong> Hoy</p>
            <p><strong>Cultivos soportados:</strong> 5</p>
            <p><strong>Análisis activos:</strong> 1</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.info("""
        **💡 Tip:** 
        Esta versión usa datos simulados. 
        Para análisis con datos reales, sube tu archivo en la versión completa.
        """)

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666;">
    <p>🌿 <b>Analizador Cloud v2.0</b> | Desarrollado para agricultura de precisión</p>
    <p>💻 Funciona 100% en tu navegador • Sin instalaciones • Gratuito</p>
</div>
""", unsafe_allow_html=True)
