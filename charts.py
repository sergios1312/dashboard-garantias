import plotly.express as px
import pandas as pd
import numpy as np
from config import colores_semaforo

def crear_pie_sucursal(df_donut_1):
    if df_donut_1.empty: return None
    resumen = df_donut_1.groupby("Sucursal DJI AGRAS - QTC:").size().reset_index(name="Cantidad")
    fig = px.pie(resumen, names="Sucursal DJI AGRAS - QTC:", values="Cantidad", hole=0.5, template="plotly_white")
    return fig

def crear_pie_estado(df_donut_2):
    if df_donut_2.empty: return None
    a_tiempo = (df_donut_2["Clasificacion"] == "A TIEMPO").sum()
    aplazado = (df_donut_2["Clasificacion"] == "APLAZADO").sum()
    atrasado = (df_donut_2["Clasificacion"] == "ATRASADO").sum()
    
    df_grafico = pd.DataFrame({
        "Estado": ["ETD (A tiempo)", "TAT (Aplazados)", "Atrasados"], 
        "Cantidad": [a_tiempo, aplazado, atrasado]
    })
    
    df_grafico = df_grafico[df_grafico["Cantidad"] > 0]
    if not df_grafico.empty:
        fig = px.pie(df_grafico, names="Estado", values="Cantidad", hole=0.4, template="plotly_white", color="Estado", color_discrete_map=colores_semaforo)
        fig.update_traces(textinfo="label+percent+value")
        return fig
    return None

def crear_semaforo_evolucion(df, cond_sucursal, cond_garantia, cond_solo_cerrados):
    df_tab1 = df[cond_sucursal & cond_garantia & cond_solo_cerrados].copy()
    if df_tab1.empty: return None
    
    df_g1 = df_tab1.groupby("Periodo").agg(
        Total_Validos=("Clasificacion", "count"),
        A_Tiempo=("Clasificacion", lambda x: (x == "A TIEMPO").sum()),
        Aplazado=("Clasificacion", lambda x: (x == "APLAZADO").sum())
    ).reset_index()
    
    df_g1["ETD (A tiempo)"] = np.where(df_g1["Total_Validos"]>0, (df_g1["A_Tiempo"]/df_g1["Total_Validos"])*100, 0).round(1)
    df_g1["TAT (Aplazado)"] = np.where(df_g1["Total_Validos"]>0, (df_g1["Aplazado"]/df_g1["Total_Validos"])*100, 0).round(1)
    
    df_melt = df_g1.melt(id_vars=["Periodo"], value_vars=["ETD (A tiempo)", "TAT (Aplazado)"], var_name="Clasificacion", value_name="Porcentaje")
    df_melt = df_melt.sort_values(by="Periodo")
    
    fig = px.bar(df_melt, x="Periodo", y="Porcentaje", color="Clasificacion", barmode="stack", text="Porcentaje", template="plotly_white", color_discrete_map=colores_semaforo, labels={"Porcentaje": "Composición (%)"})
    fig.update_layout(yaxis=dict(range=[0, 100], ticksuffix="%"), margin=dict(t=20))
    fig.update_traces(texttemplate='%{text:.1f}', textposition='inside')
    return fig

def crear_semaforo_sucursal(df, cond_periodo, cond_garantia, cond_solo_cerrados):
    df_tab2 = df[cond_periodo & cond_garantia & cond_solo_cerrados].copy()
    if df_tab2.empty: return None
    
    df_g2 = df_tab2.groupby("Sucursal DJI AGRAS - QTC:").agg(
        Total_Validos=("Clasificacion", "count"),
        A_Tiempo=("Clasificacion", lambda x: (x == "A TIEMPO").sum()),
        Aplazado=("Clasificacion", lambda x: (x == "APLAZADO").sum())
    ).reset_index()
    
    df_g2["ETD (A tiempo)"] = np.where(df_g2["Total_Validos"]>0, (df_g2["A_Tiempo"]/df_g2["Total_Validos"])*100, 0).round(1)
    df_g2["TAT (Aplazado)"] = np.where(df_g2["Total_Validos"]>0, (df_g2["Aplazado"]/df_g2["Total_Validos"])*100, 0).round(1)
    
    df_g2 = df_g2.sort_values(by="ETD (A tiempo)", ascending=False)
    
    df_melt = df_g2.melt(id_vars=["Sucursal DJI AGRAS - QTC:"], value_vars=["ETD (A tiempo)", "TAT (Aplazado)"], var_name="Clasificacion", value_name="Porcentaje")
    
    fig = px.bar(df_melt, x="Sucursal DJI AGRAS - QTC:", y="Porcentaje", color="Clasificacion", barmode="stack", text="Porcentaje", template="plotly_white", color_discrete_map=colores_semaforo, labels={"Sucursal DJI AGRAS - QTC:": "Sucursal", "Porcentaje": "Composición (%)"})
    fig.update_layout(yaxis=dict(range=[0, 100], ticksuffix="%"), margin=dict(t=20))
    fig.update_traces(texttemplate='%{text:.1f}', textposition='inside')
    return fig


def crear_barras_garantia(df, cond_periodo, cond_estado_caso, cond_solo_cerrados):
    df_garantia_vs_sin = df[cond_periodo & cond_estado_caso & cond_solo_cerrados].copy()
    df_garantia_vs_sin = df_garantia_vs_sin.dropna(subset=["GARANTÍA", "Duracion (Dias)"])
    if df_garantia_vs_sin.empty: return None
    
    df_metricas_garantia = df_garantia_vs_sin.groupby(["Sucursal DJI AGRAS - QTC:", "GARANTÍA"]).agg(Promedio_Dias=("Duracion (Dias)", "mean")).reset_index().round(1)
    
    fig = px.bar(df_metricas_garantia, x="Sucursal DJI AGRAS - QTC:", y="Promedio_Dias", color="GARANTÍA", barmode="group", text="Promedio_Dias", template="plotly_white", labels={"Sucursal DJI AGRAS - QTC:": "Sucursal", "Promedio_Dias": "Demora Promedio (Días)"})
    fig.update_traces(texttemplate='%{text}', textposition='outside')
    fig.update_layout(margin=dict(t=30))
    return fig

def crear_barras_desviacion(df_barras, tipo_plazo="Tiempo ideal (ETD)"):
    df_desviacion = df_barras.copy()
    
    # Excluir ACTIVACION
    df_desviacion = df_desviacion[df_desviacion["TIPO DE TRABAJO"].str.upper() != "ACTIVACION"]
    
    if df_desviacion.empty: return None
    
    if tipo_plazo == "Tiempo ideal (ETD)":
        df_desviacion["Desviacion"] = df_desviacion["Duracion (Dias)"] - df_desviacion["Plazo"]
    else:
        # TAT es Plazo * 2
        df_desviacion["Desviacion"] = df_desviacion["Duracion (Dias)"] - (df_desviacion["Plazo"] * 2)
        
    df_desv_agrupado = df_desviacion.groupby(["TIPO DE TRABAJO"]).agg(Desviacion_Promedio=("Desviacion", "mean")).reset_index()
    df_desv_agrupado["Desviacion_Promedio"] = df_desv_agrupado["Desviacion_Promedio"].round(1)
    df_desv_agrupado = df_desv_agrupado.sort_values(by="Desviacion_Promedio", ascending=True)

    fig = px.bar(df_desv_agrupado, x="Desviacion_Promedio", y="TIPO DE TRABAJO", orientation="h", text="Desviacion_Promedio", template="plotly_white", labels={"Desviacion_Promedio": f"Desviación al {tipo_plazo} (Días)", "TIPO DE TRABAJO": "Tipo de Trabajo"})
    fig.add_vline(x=0, line_width=2, line_dash="dash", line_color="red")
    fig.update_traces(textposition='outside', marker_color='#4C78A8')
    fig.update_layout(yaxis=dict(automargin=True), margin=dict(l=20, r=20, t=30, b=20))
    return fig

def crear_histograma(df_barras):
    df_hist = df_barras.dropna(subset=["Duracion (Dias)"]).copy()
    if df_hist.empty: return None
    
    fig = px.histogram(df_hist, x="Duracion (Dias)", color="Sucursal DJI AGRAS - QTC:", nbins=20, barmode="overlay", marginal="box", template="plotly_white", labels={"Sucursal DJI AGRAS - QTC:": "Sucursal", "Duracion (Dias)": "Días de Reparación"})
    fig.update_traces(opacity=0.75, selector=dict(type='histogram'))
    fig.update_layout(xaxis_title_text='Días que demoró el caso', yaxis_title_text='Cantidad de Casos', margin=dict(t=30))
    return fig


def crear_matriz_sla(df_barras, eje_x="Periodo", meta_sla="ETD (A tiempo)"):
    """
    Crea un Heatmap de Cumplimiento SLA.
    meta_sla define si usar "A TIEMPO" o la suma de "A TIEMPO" y "APLAZADO".
    """
    if df_barras.empty: return None
    
    df_agrupado = df_barras.groupby(["Sucursal DJI AGRAS - QTC:", eje_x]).agg(
        Total_Validos=("Clasificacion", "count"),
        Cumple_Meta=("Clasificacion", lambda x: (x == "A TIEMPO").sum() if meta_sla == "ETD (A tiempo)" else x.isin(["A TIEMPO", "APLAZADO"]).sum())
    ).reset_index()
    
    # Calcular SLA (%) y evitar división por cero
    df_agrupado["SLA (%)"] = np.where(df_agrupado["Total_Validos"] > 0, (df_agrupado["Cumple_Meta"] / df_agrupado["Total_Validos"] * 100), 0).round(1)
    
    if df_agrupado.empty: return None
    
    # Pivotar los datos para el Heatmap
    matriz_sla = df_agrupado.pivot(index="Sucursal DJI AGRAS - QTC:", columns=eje_x, values="SLA (%)")
    
    fig = px.imshow(
        matriz_sla,
        text_auto=".1f", # Mostrar el número con 1 decimal
        aspect="auto",
        color_continuous_scale="RdYlGn", # Verde pa lo bueno, rojo pa lo malo
        range_color=[0, 100], # El SLA va siempre de 0 a 100
        labels=dict(color="SLA (%)", x=eje_x, y="Sucursal"),
        template="plotly_white"
    )
    
    fig.update_layout(
        xaxis_title=eje_x,
        yaxis_title="Sucursal",
        margin=dict(t=20, l=100, r=20, b=50),
        xaxis=dict(tickangle=-45) # Inclinar labels por si son largos
    )
    
    return fig
