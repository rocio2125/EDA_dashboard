import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from scipy.stats import mannwhitneyu, kruskal, f_oneway
import folium
from streamlit_folium import st_folium

st.set_page_config(page_title="¿Cómo usamos el metro?", layout="wide")

st.title("Dashboard - ¿Cómo usamos el Metro?")

# === CARGA DE DATOS DIRECTA ===
@st.cache_data
def load_data():
    ev_diaria = pd.read_csv('./data/ev_diaria.csv', index_col=0) # Fig 1 y 2
    entradas_historico = pd.read_csv('./data/entradas_historico.csv', index_col=0) # Fig 3
    semana = pd.read_csv('./data/demanda_semanal.csv') # Fig 4
    anual = pd.read_csv('./data/demanda_anual.csv') # Fig 5
    ranking_estaciones = pd.read_csv('./data/media_entradas.csv', index_col=0)
    estaciones_mapa = pd.read_csv('./data/estaciones_ranked.csv', index_col=0) # Mapa
    return ev_diaria, entradas_historico, semana, anual, ranking_estaciones, estaciones_mapa

try:
    ev_diaria, entradas_historico, semana, anual, ranking_estaciones, estaciones_mapa = load_data()
except Exception as e:
    st.error(f"❌ No se pudieron cargar los datos: {e}")
    st.stop()

# === TABS === PESTAÑAS
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "⏳ Registro histórico",
    "🚇 Demanda diaria y otros medios de transporte",
    "📈 Distribucion semanal y anual",
    "📌 Zona tarifaria",
    "⭐ Ranking de estaciones",
    "🗺️ Mapa de estaciones",
])

# === TAB 1 ===
with tab1:
    # Registro histórico de entradas
    st.header("Entradas históricas")

    fechas = entradas_historico.columns[3:]
    df_evol = pd.DataFrame({
        "fecha": pd.to_datetime(fechas, format="%Y-%m"),
        "entradas_totales": entradas_historico[fechas].sum().values
    })
    fig3 = px.scatter(df_evol, x="fecha", y="entradas_totales", trendline="ols",
                      title="Evolución de entradas totales 2015–2025", template="plotly_white")
    fig3.add_scatter(x=df_evol["fecha"], y=df_evol["entradas_totales"], mode="lines+markers", name="Evolución")
    st.plotly_chart(fig3, use_container_width=True)

    st.markdown(
    """
    Podemos ver cómo ha evolucionado el número total de entradas en el sistema de transporte público de Madrid desde 2015 
    hasta 2025. Se pueden observar los ciclos anuales y las tendencias generales en el uso del transporte público. 
    ### Resumen:
    - La evolución histórica de las entradas totales muestra una tendencia creciente, con un aumento moderado.
    - Acontecimientos como la pandemia de COVID-19 en 2020 provocaron una caída significativa en las entradas. Afectando
    a la movilidad urbana y el uso del transporte público. Posteriormente, se observa una recuperación gradual en los años siguientes.
    """, 
    unsafe_allow_html=True)

# === TAB 2 ===
with tab2:
    # Demanda diaria del metro
    st.header("Demandada diaria de usuarios del metro")
    media_metro = ev_diaria["metro"].mean()
    fig1 = go.Figure()
    fig1.add_trace(go.Scatter(x=ev_diaria["fecha"], y=ev_diaria["metro"], mode="lines+markers", name="Metro"))
    fig1.add_trace(go.Scatter(x=ev_diaria["fecha"], y=[media_metro]*len(ev_diaria), mode="lines",
                              name=f"Media {media_metro:.0f}", line=dict(color="red", dash="dash")))
    fig1.update_layout(template="plotly_white", xaxis_title="Fecha", yaxis_title="Usuarios")
    st.plotly_chart(fig1, use_container_width=True)

    st.markdown(
    """
    En la grafica podemos ver los ciclos semanales y anuales en la demanda diaria del metro de Madrid. La linea roja
    representa la media diaria de usuarios.
    ### Resumen:
    - La demanda diaria del metro de Madrid muestra una clara tendencia estacional, con picos en los meses de invierno y 
    valles en verano. 
    - La media diaria de usuarios del metro es de aproximadamente 1.9 millones.
    - Se observan picos significativos en días específicos:
        * Día de mayor demanda: 29 de Noviembre de 2024 (2.78 millones de usuarios). Black Friday de ese año.
        * Día de menor demanda: 25 de Diciembre de 2023 (0.67 millones de usuarios). Navidad de ese año.
    """, 
    unsafe_allow_html=True
    )   

    # Otros medios de transporte    
    st.header("Resto de medios de transporte público")

    medias_diarias = ev_diaria[["metro", "EMT", "conc_carretera", "cercanias"]].mean().round(2)
    df_media = medias_diarias.to_frame("usuarios").assign(
    millones=lambda df: (df["usuarios"] / 1_000_000).round(2)
    )

    fig2 = px.bar(
        df_media,
        x=df_media.index,
        y="millones",
        color=df_media.index,
        text="millones",
        title="Media diaria de usuarios por modo de transporte (millones)",
    )
    fig2.update_traces(textposition="outside")
    fig2.update_layout(template="plotly_white")
    st.plotly_chart(fig2, use_container_width=True)

    st.markdown(
    """
    ### Resumen:
    El metro concentra la mayor demanda, seguido por los autobuses urbanos, 
    mientras que los servicios interurbanos y Cercanías tienen un uso menor.
    """, 
    unsafe_allow_html=True
    )


# === TAB 3 ===
with tab3:

    # Distribución semanal
    st.header("Distribución semanal de entradas")
    
    fig4 = go.Figure()
    fig4.add_trace(go.Scatter(x=semana['dia_semana'], y=semana['metro'], mode='lines+markers',
                         name='Metro', line=dict(width=3)))
    fig4.add_trace(go.Scatter(x=semana['dia_semana'], y=semana['EMT'], mode='lines+markers',
                         name='EMT', line=dict(width=3)))
    fig4.add_trace(go.Scatter(x=semana['dia_semana'], y=semana['conc_carretera'], mode='lines+markers',
                         name='Concesiones carretera', line=dict(width=3)))
    fig4.add_trace(go.Scatter(x=semana['dia_semana'], y=semana['cercanias'], mode='lines+markers',
                         name='Cercanías', line=dict(width=3)))

    # Personalización del gráfico
    fig4.update_layout(
        title='Usuarios promedio (en millones) por día de la semana y modo de transporte',
        xaxis_title='Día de la semana',
        yaxis_title='Millones de usuarios',
        template='plotly_white',
        hovermode='x unified',
        legend_title='Modo de transporte'
    )
    st.plotly_chart(fig4, use_container_width=True)
    st.markdown(
    """
    ### Resumen:
    - La demanda de transporte público varía significativamente a lo largo de la semana.
    - Los días laborables (lunes a viernes) muestran una demanda considerablemente más alta en comparación con los fines de semana 
    (sábado y domingo).
    - Estas diferencias se aprecian en todos los modos de transporte analizados, reflejando patrones de movilidad urbana típicos.
    """, 
    unsafe_allow_html=True
    )   

    # Distribución anual
    st.header("Distribución anual de entradas")
    fig5 = go.Figure()

    # Añadir una línea por cada modo de transporte
    fig5.add_trace(go.Scatter(x=anual['mes'], y=anual['metro'], mode='lines+markers',
                         name='Metro', line=dict(width=3)))
    fig5.add_trace(go.Scatter(x=anual['mes'], y=anual['EMT'], mode='lines+markers',
                         name='EMT', line=dict(width=3)))
    fig5.add_trace(go.Scatter(x=anual['mes'], y=anual['conc_carretera'], mode='lines+markers',
                         name='Concesiones carretera', line=dict(width=3)))
    fig5.add_trace(go.Scatter(x=anual['mes'], y=anual['cercanias'], mode='lines+markers',
                         name='Cercanías', line=dict(width=3)))

    # Personalización del gráfico
    fig5.update_layout(
        title='Usuarios promedio (en millones) por mes y modo de transporte',
        xaxis_title='Mes',
        yaxis_title='Millones de usuarios',
        template='plotly_white',
        hovermode='x unified',
        legend_title='Modo de transporte'
    )   
    st.plotly_chart(fig5, use_container_width=True)
    st.markdown(
    """
    ### Resumen:
    - La demanda de transporte público presenta variaciones estacionales a lo largo del año.
    - Se observan picos de demanda en los meses de invierno (noviembre a febrero) y valles en los meses de verano (junio a agosto).
    - Estos patrones estacionales son consistentes en todos los modos de transporte analizados, reflejando cambios 
    en los hábitos de movilidad urbana según el mes del año.
    """, 
    unsafe_allow_html=True
    )   

# === TAB 4 ===
with tab4:
    # ZONA TARIFARIA
    st.subheader("Distribución por zona tarifaria")
    fig6 = px.box(ranking_estaciones, y="zona", x="media_miles", color="zona",
                  points=False, title="Media de entradas por zona", template="plotly_white")
    st.plotly_chart(fig6, use_container_width=True)

    st.markdown(
    """
    ### Resumen:
    La grafica muestra la distribución de valores medios de entrada por estación. Los valores están separados por zona tarifaria: A, B1 y B2.
    Existe una relación entre la zona tarifaria y la demanda. Siendo la zona A la que tiene valores más altos y 
    disminuyendo los valores medios según nos alejamos del centro de la ciudad.
    """, 
    unsafe_allow_html=True
    )  
# === TAB 5 ===
with tab5:
    st.header("⭐ Ranking de estaciones")
 
    df = estaciones_mapa.copy()

    # --- Filtros interactivos ---
    col1, col2, col3 = st.columns([1, 1, 1.5])

    with col1:
        zonas = sorted(df["zona"].dropna().unique())
        zona_sel = st.multiselect(
            "Selecciona zona tarifaria:",
            zonas,
            default=zonas,
            key="zona_ranking"  
        )

    with col2:
        max_rank = int(df["ranking"].max())
        rango_rank = st.slider(
            "Rango de ranking:",
            1, max_rank, (1, 50),
            key="rango_ranking" 
        )

    with col3:
        busqueda = st.text_input(
            "🔍 Buscar por nombre o población:",
            "",
            key="busqueda_ranking"  
        )
    # --- Filtrado de datos ---
    df_filtrado = df[
        (df["zona"].isin(zona_sel)) &
        (df["ranking"].between(rango_rank[0], rango_rank[1]))
    ]

    if busqueda:
        busqueda_lower = busqueda.lower()
        df_filtrado = df_filtrado[
            df_filtrado["nombre"].str.lower().str.contains(busqueda_lower)
            | df_filtrado["poblacion"].str.lower().str.contains(busqueda_lower)
        ]

    df_filtrado = df_filtrado.sort_values("ranking")

    st.write(f"Mostrando **{len(df_filtrado)}** estaciones filtradas.")

    # --- Mostrar tabla con estilo ---
    st.dataframe(
        df_filtrado[
            [
                "ranking", "nombre", "zona", "poblacion",
                "direccion", "correspondencias",
                "media_miles"
            ]
        ].rename(columns={
            "ranking": "Ranking",
            "nombre": "Nombre",
            "zona": "Zona",
            "poblacion": "Población",
            "direccion": "Dirección",
            "correspondencias": "Correspondencias",
            "media_miles": "Entradas medias (miles)"
        }),
        use_container_width=True,
        hide_index=True
    )

    # --- Descarga CSV ---
    csv = df_filtrado.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="📥 Descargar CSV filtrado",
        data=csv,
        file_name="ranking_estaciones_filtrado.csv",
        mime="text/csv"
    )

# === TAB 6 ===
with tab6:
    st.header("🗺️ Mapa interactivo de estaciones")

    # --- Filtros ---
    zonas_disponibles = sorted(estaciones_mapa["zona"].dropna().unique())
    zona_seleccionada = st.multiselect(
        "Selecciona zona tarifaria:",
        zonas_disponibles,
        default=zonas_disponibles
    )

    top_n = st.slider(
        "Número de estaciones a mostrar (según ranking):",
        min_value=5,
        max_value=len(estaciones_mapa),
        value=len(estaciones_mapa),
        step=5
    )

    # --- Filtrado de datos ---
    df_filtrado = estaciones_mapa[
        estaciones_mapa["zona"].isin(zona_seleccionada)
    ].nsmallest(top_n, "ranking")  # ranking bajo = mejor puesto

    st.write(f"Mostrando **{len(df_filtrado)}** estaciones seleccionadas.")

    # --- Mapa ---
    m = folium.Map(location=[40.4168, -3.7038], zoom_start=11, tiles="CartoDB positron")

    for _, f in df_filtrado.iterrows():
        color = "blue" if f["zona"] == "A" else "green"
        folium.CircleMarker(
            location=[f["latitud"], f["longitud"]],
            radius=6 + f["media_miles"] / 500,
            color=color,
            fill=True,
            fill_opacity=0.7,
            popup=(
                f"<b>{f['nombre']}</b><br>"
                f"Zona: {f['zona']}<br>"
                f"Ranking: {f['ranking']}<br>"
                f"Entradas: {f['media_miles']:.0f} miles"
            ),
        ).add_to(m)

    st_folium(m, width=900, height=600)


