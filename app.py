import streamlit as st
import pandas as pd
from config import plazos_dict
from data_processing import cargar_datos, formatear_fechas_visual
from filters import renderizar_filtros, aplicar_filtros, renderizar_switches_visualizacion
from charts import (
    crear_pie_sucursal, crear_pie_estado, crear_semaforo_evolucion, 
    crear_semaforo_sucursal, crear_barras_garantia, 
    crear_barras_desviacion, crear_histograma, crear_matriz_sla
)

st.set_page_config(page_title="Dashboard Garantías", layout="wide")
st.title("📊 Dashboard Casos de Garantía")

# --- 1. DATA LOADING ---
df = cargar_datos()

# --- 2. FILTERS CONFIG ---
sucursal, estado, garantia, opciones_periodo, periodos_seleccionados, estado_caso = renderizar_filtros(df)

df_tabla_principal, df_donut_1, df_est, df_donut_2, df_barras, filtros_usados = aplicar_filtros(
    df, sucursal, estado, garantia, opciones_periodo, periodos_seleccionados, estado_caso
)

# --- 3. VISUALIZATION SWITCHES ---
(mostrar_kpis, mostrar_tabla_principal, mostrar_donut1, mostrar_stats_sucursal, 
 mostrar_donut2, mostrar_prom_mediana, mostrar_desviacion, 
 mostrar_histograma, mostrar_composicion_semaforo, mostrar_sla) = renderizar_switches_visualizacion()

# --- 4. RENDER UI COMPONENTS ---

total = len(df_tabla_principal)
abiertos = len(df_tabla_principal[df_tabla_principal["ESTADO GENERAL"] == "ABIERTO"])
cerrados = len(df_tabla_principal[df_tabla_principal["ESTADO GENERAL"] == "CERRADO"])
porcentaje_abiertos = (abiertos / total * 100) if total > 0 else 0

if mostrar_kpis:
    col_kpis, col_tabla_plazos = st.columns([1, 1.2]) 
    
    with col_kpis:
        st.write("") 
        fila1_col1, fila1_col2 = st.columns(2)
        fila1_col1.metric("Total Casos", total)
        fila1_col2.metric("Abiertos", abiertos)
        
        st.write("<br>", unsafe_allow_html=True) 
        
        fila2_col1, fila2_col2 = st.columns(2)
        fila2_col1.metric("Cerrados", cerrados)
        fila2_col2.metric("% Abiertos", f"{porcentaje_abiertos:.1f}%")
    
    with col_tabla_plazos:
        st.markdown("<p style='text-align: center; margin-bottom: 5px;'>Plazos de reparación</p>", unsafe_allow_html=True)
        plazos_tabla = pd.DataFrame({
            "TIPO DE TRABAJO": list(plazos_dict.keys()),
            "ETD (Plazo ideal)": [f"{v} Dias" for v in plazos_dict.values()],
            "TAT (Plazo máximo)": [f"{v*2} Dias" for v in plazos_dict.values()]
        })
        st.dataframe(plazos_tabla, use_container_width=True, hide_index=True)
    
    st.markdown("---")

if mostrar_tabla_principal:
    columnas_visibles = [
        "Numeración", "ESTADO GENERAL", "Sucursal DJI AGRAS - QTC:", "Cliente",
        "Fecha de ingreso", "Fecha de salida", "Duracion (Dias)", "GARANTÍA",
        "ESTADO DE CASO", "TIPO DE TRABAJO"
    ]
    df_mostrar = df_tabla_principal[[col for col in columnas_visibles if col in df_tabla_principal.columns]]
    df_mostrar = df_mostrar.rename(columns={"Duracion (Dias)": "RTAT (Duración)"})
    df_mostrar = formatear_fechas_visual(df_mostrar)
    st.dataframe(df_mostrar, use_container_width=True, hide_index=True)

if mostrar_donut1:
    fig_pie = crear_pie_sucursal(df_donut_1)
    if fig_pie: 
        st.plotly_chart(fig_pie, use_container_width=True)

if mostrar_stats_sucursal:
    st.markdown("## 📊 Estadísticas por Sucursal")
    if not df_est.empty:
        df_resumen = df_est.groupby("Sucursal DJI AGRAS - QTC:").agg(
            Casos_Totales=("ESTADO GENERAL", "count"),
            Casos_Abiertos=("ESTADO GENERAL", lambda x: (x == "ABIERTO").sum()),
            Casos_con_Garantia=("GARANTÍA", lambda x: (x == "CON GARANTIA").sum()),
            Casos_No_Ingresados=("Fecha de ingreso", lambda x: x.isna().sum()),
            Casos_Cerrados_a_Tiempo=("Clasificacion", lambda x: (x == "A TIEMPO").sum()),
            Casos_Aplazados=("Clasificacion", lambda x: (x == "APLAZADO").sum()),
            Casos_Atrasados=("Clasificacion", lambda x: (x == "ATRASADO").sum())
        ).reset_index()
        df_resumen.columns = ["Sucursal", "Casos Totales", "Casos Abiertos", "Casos con Garantía", "Casos No Ingresados", "ETD (a tiempo)", "TAT (aplazados)", "Casos Atrasados"]
        st.dataframe(df_resumen, use_container_width=True, hide_index=True)

if mostrar_donut2:
    st.markdown("## 📌 Eficiencia por sucursal")
    fig_estado = crear_pie_estado(df_donut_2)
    if fig_estado: 
        st.plotly_chart(fig_estado, use_container_width=True)

if mostrar_composicion_semaforo:
    st.markdown("---")
    st.markdown("## 📊 Comparativa de eficiencias")
    
    tab1, tab2 = st.tabs(["📅 Evolución Temporal", "🏢 Comparativa por Sucursal"])
    
    with tab1:
        fig_evol = crear_semaforo_evolucion(df, filtros_usados["cond_sucursal"], filtros_usados["cond_garantia"], filtros_usados["cond_solo_cerrados"])
        if fig_evol: 
            st.plotly_chart(fig_evol, use_container_width=True)
        else: 
            st.info("No hay datos para mostrar.")
            
    with tab2:
        fig_suc = crear_semaforo_sucursal(df, filtros_usados["cond_periodo"], filtros_usados["cond_garantia"], filtros_usados["cond_solo_cerrados"])
        if fig_suc: 
            st.plotly_chart(fig_suc, use_container_width=True)
        else: 
            st.info("No hay datos para mostrar.")

if mostrar_prom_mediana:
    st.markdown("---")
    st.markdown("## ⚖️ Demora Promedio: Con Garantía vs Sin Garantía")
    fig_prom = crear_barras_garantia(df, filtros_usados["cond_periodo"], filtros_usados["cond_estado_caso"], filtros_usados["cond_solo_cerrados"])
    if fig_prom: 
        st.plotly_chart(fig_prom, use_container_width=True)
    else: 
        st.info("No hay casos suficientes (o cerrados) para analizar la comparativa de garantías.")

if mostrar_desviacion:
    st.markdown("---")
    st.markdown("## 🎯 Desviación del plazo del tiempo de trabajo")
    
    col_desv1, col_desv2 = st.columns([1, 4])
    with col_desv1:
        tipo_plazo_desv = st.radio("Tipo de plazo:", ["Tiempo ideal (ETD)", "Tiempo máximo (TAT)"])
    with col_desv2:
        st.caption("Muestra cuántos días, en promedio, se excede o se ahorra el equipo técnico frente a la meta (barras hacia la izquierda significan ahorro, hacia la derecha es demora extra).")
        
    fig_desv = crear_barras_desviacion(df_barras, tipo_plazo=tipo_plazo_desv)
    if fig_desv: 
        st.plotly_chart(fig_desv, use_container_width=True)
    else: 
        st.info("No hay casos suficientes (o cerrados) para analizar la desviación del plazo.")

if mostrar_histograma:
    st.markdown("---")
    st.markdown("## 📈 Distribución de Tiempos de Reparación (Volumen)")
    fig_hist = crear_histograma(df_barras)
    if fig_hist: 
        st.plotly_chart(fig_hist, use_container_width=True)
    else: 
        st.info("No hay casos suficientes (o cerrados) para mostrar el histograma.")

if mostrar_sla:
    st.markdown("---")
    st.markdown("## 🎯 Matriz de SLA (Nivel de Servicio)")
    
    col_sla1, col_sla2, col_sla3 = st.columns([1, 1, 3])
    with col_sla1:
        eje_x_sla = st.radio("Clasificar matriz por:", ["Periodo", "TIPO DE TRABAJO"])
    with col_sla2:
        meta_sla_opcion = st.radio("Meta SLA:", ["ETD (A tiempo)", "TAT (Tiempo máximo)"])
    with col_sla3:
        st.caption("Visualiza el porcentaje de reparaciones completadas dentro de la meta seleccionada en relación con el total de casos cerrados (100% es el escenario ideal).")
    
    fig_sla = crear_matriz_sla(df_barras, eje_x=eje_x_sla, meta_sla=meta_sla_opcion)
    if fig_sla:
        st.plotly_chart(fig_sla, use_container_width=True)
    else:
        st.info("No hay casos cerrados suficientes para generar la matriz de SLA con los filtros actuales.")