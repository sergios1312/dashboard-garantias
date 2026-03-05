import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

st.set_page_config(page_title="Dashboard Garantías", layout="wide")

st.title("📊 Dashboard Casos de Garantía")

# CARGAR CSV

@st.cache_data
def cargar_datos():
    df = pd.read_csv("casos.csv") #Aactualizado el 03/03, recordar actualizar interdiario
    df["ESTADO DE CASO"] = df["ESTADO DE CASO"].fillna("").astype(str)
    df.loc[df["Fecha de ingreso"].isna(), "ESTADO DE CASO"] = "NO INGRESADO"
    df.loc[df["ESTADO DE CASO"].str.strip() == "", "ESTADO DE CASO"] = "SIN ESTADO"
    df["ESTADO GENERAL"] = df["ESTADO GENERAL"].str.upper()
    df["GARANTÍA"] = df["GARANTÍA"].str.upper()
    df["Fecha de salida"] = pd.to_datetime(df["Fecha de salida"], errors="coerce")
    df["Fecha de ingreso"] = pd.to_datetime(df["Fecha de ingreso"], errors="coerce")
    df["Periodo"] = df["Fecha de salida"].dt.to_period("M").astype(str)
    return df

df = cargar_datos()

hoy = pd.Timestamp(datetime.today().date())
def calcular_dias_proceso(row):
    
    fecha_ing = row["Fecha de ingreso"]
    fecha_sal = row["Fecha de salida"]
    
    if pd.isna(fecha_ing):
        return None
    
    if pd.isna(fecha_sal):
        return (hoy - fecha_ing).days
    
    return (fecha_sal - fecha_ing).days

df["Duracion (Dias)"] = df.apply(calcular_dias_proceso, axis=1)

# FILTRO PRINCIPALES

st.sidebar.header("Filtros")

sucursal = st.sidebar.selectbox(
    "Sucursal",
    ["Todos"] + sorted(df["Sucursal DJI AGRAS - QTC:"].dropna().unique())
)

estado = st.sidebar.selectbox(
    "Estado",
    ["Todos", "ABIERTO", "CERRADO", "DEVUELTO"] # no voy a poner activaciones, no jodan
)

garantia = st.sidebar.selectbox(
    "Garantía",
    ["Todos", "CON GARANTIA", "SIN GARANTIA"]
)

periodo = st.sidebar.selectbox(
    "Periodo",
    ["Todos"] + sorted(df["Periodo"].dropna().unique())
)
estado_caso = st.sidebar.selectbox(
    "Estado de Caso",
    ["Todos"] + sorted(df["ESTADO DE CASO"].dropna().unique())
)

# FILTRAR

df_filtrado = df.copy()

if sucursal != "Todos":
    df_filtrado = df_filtrado[df_filtrado["Sucursal DJI AGRAS - QTC:"] == sucursal]

if estado == "ABIERTO":
    df_filtrado = df_filtrado[df_filtrado["ESTADO GENERAL"] == "ABIERTO"]

elif estado == "CERRADO":
    df_filtrado = df_filtrado[df_filtrado["ESTADO GENERAL"] == "CERRADO"]

elif estado == "DEVUELTO":
    df_filtrado = df_filtrado[
        df_filtrado["ESTADO DE CASO"].str.upper() == "DEVUELTO"
    ]

if garantia != "Todos":
    df_filtrado = df_filtrado[df_filtrado["GARANTÍA"] == garantia]

# Aplicar periodo solo si no está filtrando por abierto, jesus no se acuerda xd
if estado != "ABIERTO":
    if periodo != "Todos":
        df_filtrado = df_filtrado[df_filtrado["Periodo"] == periodo]
if estado_caso != "Todos":
    df_filtrado = df_filtrado[
        df_filtrado["ESTADO DE CASO"] == estado_caso
    ]

# KPIs subanme el sueldo csm

total = len(df_filtrado)
abiertos = len(df_filtrado[df_filtrado["ESTADO GENERAL"] == "ABIERTO"])
cerrados = len(df_filtrado[df_filtrado["ESTADO GENERAL"] == "CERRADO"])
porcentaje_abiertos = (abiertos / total * 100) if total > 0 else 0

kpi_col, plazo_col = st.columns([3,2])

with kpi_col:

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Total Casos", total)
    col2.metric("Abiertos", abiertos)
    col3.metric("Cerrados", cerrados)
    col4.metric("% Abiertos", f"{porcentaje_abiertos:.1f}%")

with plazo_col:

    st.markdown("#### ⏱ Plazos de reparación")

    st.markdown("""
    <table style="font-size:13px">
    <tr>
        <th>Trabajo</th>
        <th>Ideal</th>
        <th>Máx</th>
    </tr>
    <tr><td>Rep. Electrónica</td><td>5 días</td><td>10 días</td></tr>
    <tr><td>Rep. Generador</td><td>7 días</td><td>14 días</td></tr>
    <tr><td>Rep. Comp. Generador</td><td>14 días</td><td>28 días</td></tr>
    <tr><td>Rep. Mecánica</td><td>5 días</td><td>10 días</td></tr>
    <tr><td>Scrap Batería</td><td>7 días</td><td>14 días</td></tr>
    <tr><td>Rep. Control</td><td>5 días</td><td>10 días</td></tr>
    <tr><td>Rep. Comp. RC</td><td>7 días</td><td>14 días</td></tr>
    <tr><td>Caso Crash</td><td>7 días</td><td>14 días</td></tr>
    <tr><td>Rep. Cargador</td><td>5 días</td><td>10 días</td></tr>
    </table>
    """, unsafe_allow_html=True)

st.markdown("---")

st.dataframe(
plazos_tabla,
use_container_width=True,
hide_index=True
)
#---------------------------------------------------------------------------------------------------------
# TABLA

columnas_visibles = [
    "Numeración",
    "ESTADO GENERAL",
    "Sucursal DJI AGRAS - QTC:",
    "Cliente",
    "Fecha de ingreso",
    "Fecha de salida",
    "Duracion (Dias)",
    "GARANTÍA",
    "ESTADO DE CASO",
    "TIPO DE TRABAJO"
]

columnas_finales = [col for col in columnas_visibles if col in df_filtrado.columns]

df_mostrar = df_filtrado[columnas_finales]

st.dataframe(df_mostrar, use_container_width=True, hide_index=True)

# ------------------------------------------------
# DONUT YA ME DIO HAMBRE XD

if total > 0:
    resumen = (
        df_filtrado
        .groupby("Sucursal DJI AGRAS - QTC:")
        .size()
        .reset_index(name="Cantidad")
    )

    fig_pie = px.pie(
        resumen,
        names="Sucursal DJI AGRAS - QTC:",
        values="Cantidad",
        hole=0.5,
        template="plotly_white"
    )

    st.plotly_chart(fig_pie, use_container_width=True)

#--------------------------------------------------------------------------------------------------------
# TABLA ESTADÍSTICA POR SUCURSAL
# (Solo afectada por filtro perido)

st.markdown("## 📊 Estadísticas por Sucursal")

# Diccionario de plazos
plazos = {
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

df_est = df.copy()

# Solo filtrar por PERIODO
if periodo != "Todos":
    df_est = df_est[df_est["Periodo"] == periodo]

# Convertir fechas
df_est["Fecha de ingreso"] = pd.to_datetime(df_est["Fecha de ingreso"], errors="coerce")
df_est["Fecha de salida"] = pd.to_datetime(df_est["Fecha de salida"], errors="coerce")

hoy = pd.Timestamp(datetime.today().date())

def calcular_dias(row):
    fecha_ing = row["Fecha de ingreso"]
    fecha_sal = row["Fecha de salida"]
    
    if pd.isna(fecha_ing):
        return 0  # No hay fecha ingreso
    
    if pd.isna(fecha_sal):
        return (hoy - fecha_ing).days  # Caso abierto
    
    return (fecha_sal - fecha_ing).days  # Caso cerrado

df_est["Dias"] = df_est.apply(calcular_dias, axis=1)

# Asignar plazo según tipo
df_est["Plazo"] = df_est["TIPO DE TRABAJO"].map(plazos)

# Clasificación
def clasificar(row):
    # Solo se clasifican casos CERRADOS
    if row["ESTADO GENERAL"] != "CERRADO":
        return None
    
    # Si no hay fecha de ingreso o salida → no clasificar
    if pd.isna(row["Fecha de ingreso"]) or pd.isna(row["Fecha de salida"]):
        return None
    
    if pd.isna(row["Plazo"]):
        return None
    
    if row["Dias"] <= row["Plazo"]:
        return "A TIEMPO"
    elif row["Dias"] <= row["Plazo"] * 2:
        return "APLAZADO"
    else:
        return "ATRASADO"

df_est["Clasificacion"] = df_est.apply(clasificar, axis=1)

# Agrupar por sucursal
resumen = []

for suc in sorted(df["Sucursal DJI AGRAS - QTC:"].dropna().unique()):
    df_suc = df_est[df_est["Sucursal DJI AGRAS - QTC:"] == suc]
    
    total = len(df_suc)
    abiertos = len(df_suc[df_suc["ESTADO GENERAL"] == "ABIERTO"])
    garantia = len(df_suc[df_suc["GARANTÍA"] == "CON GARANTIA"])
    no_ingresados = len(df_suc[df_suc["Fecha de ingreso"].isna()])
    a_tiempo = len(df_suc[df_suc["Clasificacion"] == "A TIEMPO"])
    aplazado = len(df_suc[df_suc["Clasificacion"] == "APLAZADO"])
    atrasado = len(df_suc[df_suc["Clasificacion"] == "ATRASADO"])
    
    resumen.append([
        suc,
        total,
        abiertos,
        garantia,
        no_ingresados,
        a_tiempo,
        aplazado,
        atrasado
    ])

df_resumen = pd.DataFrame(resumen, columns=[
    "Sucursal",
    "Casos Totales",
    "Casos Abiertos",
    "Casos con Garantía",
    "Casos No Ingresados",
    "Casos Cerrados a Tiempo",
    "Casos Aplazados",
    "Casos Atrasados"
])

st.dataframe(df_resumen, use_container_width=True, hide_index=True)
# =============================
# PIE POR SUCURSAL (solo filtro sucursal)
# =============================

st.markdown("## 📌 Distribución de Casos por Estado")

df_pie = df.copy()

# Aplicar solo filtro de sucursal
if sucursal != "Todos":
    df_pie = df_pie[df_pie["Sucursal DJI AGRAS - QTC:"] == sucursal]

# Recalcular clasificación para este dataframe
df_pie["Fecha de ingreso"] = pd.to_datetime(df_pie["Fecha de ingreso"], errors="coerce")
df_pie["Fecha de salida"] = pd.to_datetime(df_pie["Fecha de salida"], errors="coerce")

df_pie["Dias"] = df_pie.apply(calcular_dias, axis=1)
df_pie["Plazo"] = df_pie["TIPO DE TRABAJO"].map(plazos)
df_pie["Clasificacion"] = df_pie.apply(clasificar, axis=1)

abiertos = len(df_pie[df_pie["ESTADO GENERAL"] == "ABIERTO"])
a_tiempo = len(df_pie[df_pie["Clasificacion"] == "A TIEMPO"])
aplazado = len(df_pie[df_pie["Clasificacion"] == "APLAZADO"])
atrasado = len(df_pie[df_pie["Clasificacion"] == "ATRASADO"])

df_grafico = pd.DataFrame({
    "Estado": [
        "Abiertos",
        "Cerrados a Tiempo",
        "Aplazados",
        "Atrasados"
    ],
    "Cantidad": [
        abiertos,
        a_tiempo,
        aplazado,
        atrasado
    ]
})

df_grafico = df_grafico[df_grafico["Cantidad"] > 0]

if len(df_grafico) > 0:
    fig_estado = px.pie(
        df_grafico,
        names="Estado",
        values="Cantidad",
        hole=0.4,
        template="plotly_white"
    )

    fig_estado.update_traces(
        textinfo="label+percent+value"
    )

    st.plotly_chart(fig_estado, use_container_width=True)