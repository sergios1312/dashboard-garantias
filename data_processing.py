import pandas as pd
import numpy as np
import streamlit as st
from datetime import datetime
from config import plazos_dict, sucursales_baneadas, trabajos_baneados

@st.cache_data
def cargar_datos():
    df = pd.read_csv("casos.csv")
    df["ESTADO DE CASO"] = df["ESTADO DE CASO"].fillna("").astype(str)
    
    df["Fecha de ingreso"] = pd.to_datetime(df["Fecha de ingreso"], errors="coerce")
    df["Fecha de salida"] = pd.to_datetime(df["Fecha de salida"], errors="coerce")
    
    df.loc[df["Fecha de ingreso"].isna(), "ESTADO DE CASO"] = "NO INGRESADO"
    df.loc[df["ESTADO DE CASO"].str.strip() == "", "ESTADO DE CASO"] = "SIN ESTADO"
    
    df["ESTADO GENERAL"] = df["ESTADO GENERAL"].str.upper()
    df["GARANTÍA"] = df["GARANTÍA"].str.upper()
    df["Periodo"] = df["Fecha de salida"].dt.to_period("M").astype(str)
    
    hoy = datetime.today().date()
    
    def calcular_dias(row):
        fecha_ing = row["Fecha de ingreso"]
        fecha_sal = row["Fecha de salida"]
        
        if pd.isna(fecha_ing): return None
        if pd.isna(fecha_sal): d2 = hoy
        else: d2 = fecha_sal.date()
            
        d1 = fecha_ing.date()
        if d2 < d1: return 0
            
        d2_inclusivo = d2 + pd.Timedelta(days=1)
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
    
    df = df[~df["Sucursal DJI AGRAS - QTC:"].isin(sucursales_baneadas)]
    df = df[~df["TIPO DE TRABAJO"].str.upper().isin(trabajos_baneados)]
    
    return df

def formatear_fechas_visual(dataframe):
    df_vis = dataframe.copy()
    if "Fecha de ingreso" in df_vis.columns:
        df_vis["Fecha de ingreso"] = df_vis["Fecha de ingreso"].dt.strftime('%d/%m/%Y')
    if "Fecha de salida" in df_vis.columns:
        df_vis["Fecha de salida"] = df_vis["Fecha de salida"].dt.strftime('%d/%m/%Y')
    return df_vis
