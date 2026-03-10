import streamlit as st
import pandas as pd

def renderizar_filtros(df):
    st.sidebar.header("Filtros")

    sucursal = st.sidebar.selectbox(
        "Sucursal",
        ["Todos"] + sorted(df["Sucursal DJI AGRAS - QTC:"].dropna().unique())
    )

    estado = st.sidebar.selectbox(
        "Estado",
        ["Todos", "ABIERTO", "CERRADO", "DEVUELTO"]
    )

    garantia = st.sidebar.selectbox(
        "Garantía",
        ["Todos", "CON GARANTIA", "SIN GARANTIA"]
    )

    opciones_periodo = [p for p in df["Periodo"].dropna().unique() if p != "NaT"]
    opciones_periodo = sorted(opciones_periodo)

    periodos_seleccionados = st.sidebar.multiselect(
        "Periodo",
        options=opciones_periodo,
        default=opciones_periodo
    )

    estado_caso = st.sidebar.selectbox(
        "Estado de Caso",
        ["Todos"] + sorted(df["ESTADO DE CASO"].dropna().unique())
    )
    
    return sucursal, estado, garantia, opciones_periodo, periodos_seleccionados, estado_caso

def aplicar_filtros(df, sucursal, estado, garantia, opciones_periodo, periodos_seleccionados, estado_caso):
    cond_sucursal = df["Sucursal DJI AGRAS - QTC:"] == sucursal if sucursal != "Todos" else pd.Series(True, index=df.index)

    cond_estado = pd.Series(True, index=df.index)
    if estado == "ABIERTO": cond_estado = df["ESTADO GENERAL"] == "ABIERTO"
    elif estado == "CERRADO": cond_estado = df["ESTADO GENERAL"] == "CERRADO"
    elif estado == "DEVUELTO": cond_estado = df["ESTADO DE CASO"].str.upper() == "DEVUELTO"

    cond_garantia = df["GARANTÍA"] == garantia if garantia != "Todos" else pd.Series(True, index=df.index)
    cond_estado_caso = df["ESTADO DE CASO"] == estado_caso if estado_caso != "Todos" else pd.Series(True, index=df.index)

    if len(periodos_seleccionados) == len(opciones_periodo) or not periodos_seleccionados:
        cond_periodo = pd.Series(True, index=df.index)
    else:
        cond_periodo = df["Periodo"].isin(periodos_seleccionados)

    cond_periodo_kpi = cond_periodo if estado != "ABIERTO" else pd.Series(True, index=df.index)
    
    cond_solo_cerrados = df["ESTADO GENERAL"] == "CERRADO"

    df_tabla_principal = df[cond_sucursal & cond_estado & cond_garantia & cond_estado_caso & cond_periodo_kpi].copy()
    df_donut_1 = df[cond_estado & cond_garantia & cond_estado_caso & cond_periodo_kpi].copy()
    df_est = df[cond_periodo].copy()
    df_donut_2 = df[cond_periodo & cond_sucursal].copy()
    
    df_barras = df[cond_sucursal & cond_periodo & cond_garantia & cond_solo_cerrados].copy()
    
    filtros_usados = {
        "cond_sucursal": cond_sucursal,
        "cond_periodo": cond_periodo,
        "cond_garantia": cond_garantia,
        "cond_estado_caso": cond_estado_caso,
        "cond_solo_cerrados": cond_solo_cerrados
    }

    return df_tabla_principal, df_donut_1, df_est, df_donut_2, df_barras, filtros_usados

def renderizar_switches_visualizacion():
    st.sidebar.markdown("---")
    st.sidebar.header("👁️ Visualización")

    mostrar_kpis = st.sidebar.checkbox("KPIs y Plazos", value=True)
    mostrar_tabla_principal = st.sidebar.checkbox("Tabla Principal", value=True)
    mostrar_donut1 = st.sidebar.checkbox("Distribución por Sucursal (Pie)", value=True)
    mostrar_stats_sucursal = st.sidebar.checkbox("Estadísticas por Sucursal (Tabla)", value=True)
    mostrar_donut2 = st.sidebar.checkbox("Distribución por Estado (Pie)", value=True)
    mostrar_prom_mediana = st.sidebar.checkbox("Promedio vs Mediana", value=True)
    mostrar_desviacion = st.sidebar.checkbox("Desviación del Plazo", value=True)
    mostrar_histograma = st.sidebar.checkbox("Distribución de Tiempos (Volumen)", value=True)
    mostrar_composicion_semaforo = st.sidebar.checkbox("Semáforo de Tiempos (Evolución y Sucursal)", value=True)
    mostrar_sla = st.sidebar.checkbox("Matriz de SLA (Nivel de Servicio)", value=True)
    
    return (mostrar_kpis, mostrar_tabla_principal, mostrar_donut1, mostrar_stats_sucursal, 
            mostrar_donut2, mostrar_prom_mediana, 
            mostrar_desviacion, mostrar_histograma, mostrar_composicion_semaforo, mostrar_sla)
