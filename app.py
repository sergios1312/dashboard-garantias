import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import textwrap # <--- Añadido para el ajuste de texto de los nombres
from datetime import datetime

st.set_page_config(page_title="Dashboard Garantías", layout="wide")

st.title("📊 Dashboard Casos de Garantía")

# 1. UNIFICAR DICCIONARIO DE PLAZOS
plazos_dict = {
    "REPARACION ELECTRONICA": 5,
    "REPARACION DE GENERADOR": 7,
    "REPARACION COMPLEJA GENERADOR": 14,
    "REPARACION MECANICA": 5,
    "SCRAP BATERIA": 7,
    "REPARACION DE CONTROL REMOTO": 5,
    "REPARACION COMPLEJA RC": 7,
    "CASO CRASH": 7,
    "REPARACION DE CARGADOR": 5
}

# CARGAR CSV Y PREPROCESAR
@st.cache_data
def cargar_datos():
    df = pd.read_csv("casos.csv")
    df["ESTADO DE CASO"] = df["ESTADO DE CASO"].fillna("").astype(str)
    
    # Convertir fechas a datetime
    df["Fecha de ingreso"] = pd.to_datetime(df["Fecha de ingreso"], errors="coerce")
    df["Fecha de salida"] = pd.to_datetime(df["Fecha de salida"], errors="coerce")
    
    df.loc[df["Fecha de ingreso"].isna(), "ESTADO DE CASO"] = "NO INGRESADO"
    df.loc[df["ESTADO DE CASO"].str.strip() == "", "ESTADO DE CASO"] = "SIN ESTADO"
    
    df["ESTADO GENERAL"] = df["ESTADO GENERAL"].str.upper()
    df["GARANTÍA"] = df["GARANTÍA"].str.upper()
    df["Periodo"] = df["Fecha de salida"].dt.to_period("M").astype(str)
    
    hoy = datetime.today().date()
    
    # CÁLCULO DE DÍAS (Lunes a Sábado, inclusivo, sin negativos)
    def calcular_dias(row):
        fecha_ing = row["Fecha de ingreso"]
        fecha_sal = row["Fecha de salida"]
        
        if pd.isna(fecha_ing): 
            return None
            
        if pd.isna(fecha_sal): 
            d2 = hoy
        else:
            d2 = fecha_sal.date()
            
        d1 = fecha_ing.date()
        
        # Corrección de datos: si salio "antes" de ingresar, es 0
        if d2 < d1:
            return 0
            
        # busday_count no incluye el día final, así que le sumamos 1 día para que sea inclusivo
        d2_inclusivo = d2 + pd.Timedelta(days=1)
        
        # weekmask '1111110' significa Lunes a Sábado (1=laborable, 0=no laborable)
        dias_habiles = np.busday_count(d1, d2_inclusivo, weekmask='1111110')
        return int(dias_habiles)
        
    df["Duracion (Dias)"] = df.apply(calcular_dias, axis=1)
    df["Plazo"] = df["TIPO DE TRABAJO"].map(plazos_dict)
    
    def clasificar(row):
        if row["ESTADO GENERAL"] != "CERRADO": return None
        if pd.isna(row["Fecha de ingreso"]) or pd.isna(row["Fecha de salida"]): return None
        if pd.isna(row["Plazo"]): return None
        
        dias = row["Duracion (Dias)"]
        if dias <= row["Plazo"]: return "A TIEMPO"
        elif dias <= row["Plazo"] * 2: return "APLAZADO"
        else: return "ATRASADO"
        
    df["Clasificacion"] = df.apply(clasificar, axis=1)
    
    return df

df = cargar_datos()

# FILTROS PRINCIPALES
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

# MÁSCARAS
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

# APLICAR FILTROS
df_tabla_principal = df[cond_sucursal & cond_estado & cond_garantia & cond_estado_caso & cond_periodo_kpi].copy()
df_donut_1 = df[cond_estado & cond_garantia & cond_estado_caso & cond_periodo_kpi].copy()
df_est = df[cond_periodo].copy()
df_donut_2 = df[cond_periodo & cond_sucursal].copy()

# Datos para el gráfico de barras (afectado por Sucursal, Periodo y Garantía)
df_barras = df[cond_sucursal & cond_periodo & cond_garantia].copy()

def formatear_fechas_visual(dataframe):
    df_vis = dataframe.copy()
    if "Fecha de ingreso" in df_vis.columns:
        df_vis["Fecha de ingreso"] = df_vis["Fecha de ingreso"].dt.strftime('%d/%m/%Y')
    if "Fecha de salida" in df_vis.columns:
        df_vis["Fecha de salida"] = df_vis["Fecha de salida"].dt.strftime('%d/%m/%Y')
    return df_vis

# -------------------------------------------------------------------------
# RENDERIZADO DEL DASHBOARD
# -------------------------------------------------------------------------

total = len(df_tabla_principal)
abiertos = len(df_tabla_principal[df_tabla_principal["ESTADO GENERAL"] == "ABIERTO"])
cerrados = len(df_tabla_principal[df_tabla_principal["ESTADO GENERAL"] == "CERRADO"])
porcentaje_abiertos = (abiertos / total * 100) if total > 0 else 0

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
        "PLAZO IDEAL": [f"{v} Dias" for v in plazos_dict.values()],
        "PLAZO MAXIMO": [f"{v*2} Dias" for v in plazos_dict.values()]
    })
    
    st.dataframe(plazos_tabla, use_container_width=True, hide_index=True)

st.markdown("---")

# TABLA PRINCIPAL
columnas_visibles = [
    "Numeración", "ESTADO GENERAL", "Sucursal DJI AGRAS - QTC:", "Cliente",
    "Fecha de ingreso", "Fecha de salida", "Duracion (Dias)", "GARANTÍA",
    "ESTADO DE CASO", "TIPO DE TRABAJO"
]

columnas_finales = [col for col in columnas_visibles if col in df_tabla_principal.columns]
df_mostrar = df_tabla_principal[columnas_finales]
df_mostrar = formatear_fechas_visual(df_mostrar)
st.dataframe(df_mostrar, use_container_width=True, hide_index=True)

# DONUT 1
if not df_donut_1.empty:
    resumen_donut1 = df_donut_1.groupby("Sucursal DJI AGRAS - QTC:").size().reset_index(name="Cantidad")
    fig_pie = px.pie(
        resumen_donut1,
        names="Sucursal DJI AGRAS - QTC:",
        values="Cantidad",
        hole=0.5,
        template="plotly_white"
    )
    st.plotly_chart(fig_pie, use_container_width=True)

# TABLA ESTADÍSTICA
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

    df_resumen.columns = [
        "Sucursal", "Casos Totales", "Casos Abiertos", "Casos con Garantía",
        "Casos No Ingresados", "Casos Cerrados a Tiempo", "Casos Aplazados", "Casos Atrasados"
    ]
    st.dataframe(df_resumen, use_container_width=True, hide_index=True)

# PIE 2
st.markdown("## 📌 Distribución de Casos por Estado")
if not df_donut_2.empty:
    abiertos_pie2 = (df_donut_2["ESTADO GENERAL"] == "ABIERTO").sum()
    a_tiempo_pie2 = (df_donut_2["Clasificacion"] == "A TIEMPO").sum()
    aplazado_pie2 = (df_donut_2["Clasificacion"] == "APLAZADO").sum()
    atrasado_pie2 = (df_donut_2["Clasificacion"] == "ATRASADO").sum()

    df_grafico = pd.DataFrame({
        "Estado": ["Abiertos", "Cerrados a Tiempo", "Aplazados", "Atrasados"],
        "Cantidad": [abiertos_pie2, a_tiempo_pie2, aplazado_pie2, atrasado_pie2]
    })
    df_grafico = df_grafico[df_grafico["Cantidad"] > 0]

    if not df_grafico.empty:
        fig_estado = px.pie(
            df_grafico,
            names="Estado",
            values="Cantidad",
            hole=0.4,
            template="plotly_white"
        )
        fig_estado.update_traces(textinfo="label+percent+value")
        st.plotly_chart(fig_estado, use_container_width=True)


# -------------------------------------------------------------------------
# GRÁFICO DE BARRAS DE TIEMPO (CORREGIDO, AJUSTADO Y CON AJUSTE DE TEXTO)
# -------------------------------------------------------------------------
st.markdown("---")
st.markdown("## ⏱️ Tiempos de Reparación por Caso")

df_barras = df_barras.dropna(subset=["Duracion (Dias)"]).copy()

# NUEVO: Función auxiliar para formatear la etiqueta del eje Y con ajuste de texto automático
def formatear_etiqueta_eje(numeracion, cliente, ancho_max=25):
    # Aseguramos que el cliente sea una cadena y limpiamos espacios
    cliente_str = str(cliente).strip()
    
    # Usamos textwrap para dividir el nombre del cliente si supera el ancho máximo
    # No rompemos palabras largas por la mitad por estética.
    cliente_envuelto = textwrap.fill(cliente_str, width=ancho_max, break_long_words=False)
    
    # Reemplazamos los saltos de línea (\n) con etiquetas HTML (<br>)
    cliente_html = cliente_envuelto.replace('\n', '<br>')
    
    # Construimos la etiqueta final: Numeración arriba, Cliente ajustado abajo
    return (
        f"{numeracion}<br>"
        f"<span style='font-size:10px'>( {cliente_html} )</span>"
    )

if not df_barras.empty:
    df_barras["RTAT"] = df_barras["Duracion (Dias)"]
    df_barras["TAT"] = df_barras["Plazo"] * 2 
    
    # NUEVO: Aplicar la nueva función de formateo con ajuste de texto a cada fila
    # He puesto un ancho máximo de 25 caracteres para el nombre del cliente.
    # Si te parece mucho o poco, puedes cambiar ese número aquí abajo.
    ancho_max_cliente = 25 
    
    df_barras["Etiqueta"] = df_barras.apply(
        lambda row: formatear_etiqueta_eje(row["Numeración"], row["Cliente"], ancho_max=ancho_max_cliente),
        axis=1
    )
    
    df_barras = df_barras.sort_values("Fecha de ingreso", ascending=False)

    fig_barras = go.Figure()
    
    # Barra de RTAT con números visibles
    fig_barras.add_trace(go.Bar(
        y=df_barras["Etiqueta"],
        x=df_barras["RTAT"],
        name="RTAT: tiempo real de reparación",
        orientation='h',
        marker_color='#FF99B4',
        text=df_barras["RTAT"],
        textposition='outside' # Muestra el número fuera de la barra
    ))
    
    # Barra de TAT con números visibles
    fig_barras.add_trace(go.Bar(
        y=df_barras["Etiqueta"],
        x=df_barras["TAT"],
        name="TAT: tiempo ideal máximo",
        orientation='h',
        marker_color='#B4D82C',
        text=df_barras["TAT"],
        textposition='outside'
    ))
    
    # Calculamos una altura dinámica basada en la cantidad de filas de texto HTML (numeración + líneas de cliente).
    # Como los nombres ahora ocupan 2 o más renglones, aumentamos el factor de altura por caso.
    # Usaremos 90 píxeles por caso para dar aire al texto envuelto.
    altura_dinamica = max(400, len(df_barras) * 90) 
    
    fig_barras.update_layout(
        barmode='group', 
        height=altura_dinamica,
        yaxis=dict(
            autorange="reversed",
            tickfont=dict(size=11), # Achicamos un poco la letra para que ocupe menos espacio a la izquierda
            automargin=False, # NUEVO: Desactivamos el automargin para tener control total
        ),
        xaxis=dict(
            title="Duración (Días)",
            dtick=5, # Fuerzo a que marque cada 5 días
            showgrid=True,
            gridcolor='lightgray'
        ),
        legend=dict(
            orientation="h", 
            yanchor="bottom",
            y=1.01, # Acerqué la leyenda a la gráfica
            xanchor="center",
            x=0.5
        ),
        # NUEVO: Ajustamos los márgenes. l=10 pega mucho la gráfica a la izquierda pq el texto HTML ya no empuja.
        # t=30 reduce espacio arriba. b=20 reduce espacio abajo.
        margin=dict(l=10, r=20, t=30, b=20) 
    )
    
    with st.container(height=500):
        st.plotly_chart(fig_barras, use_container_width=True)
else:
    st.info("No hay datos suficientes para graficar los tiempos con los filtros actuales.")