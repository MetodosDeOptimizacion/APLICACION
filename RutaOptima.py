import streamlit as st 
import folium
from streamlit_folium import folium_static, st_folium
from scipy.spatial.distance import euclidean
from itertools import permutations

# 📌 Función para calcular la ruta óptima con un punto de origen fijo
def calcular_ruta_optima(puntos, origen):
    num_puntos = len(puntos)
    if num_puntos < 2:
        return []

    # Separar el punto de origen del resto de los puntos
    puntos_sin_origen = [p for p in puntos if p != origen]
    
    mejor_ruta = None
    menor_distancia = float("inf")

    # Evaluar todas las permutaciones de los puntos (sin contar el origen)
    for perm in permutations(puntos_sin_origen):
        # Agregar la distancia desde el origen al primer punto
        distancia_total = euclidean(origen, perm[0])
        # Sumar distancias entre puntos consecutivos
        distancia_total += sum(euclidean(perm[i], perm[i+1]) for i in range(len(perm) - 1))

        if distancia_total < menor_distancia:
            menor_distancia = distancia_total
            mejor_ruta = [origen] + list(perm)  # Agregar el origen al inicio

    return mejor_ruta

# 📍 Interfaz con Streamlit
st.set_page_config(page_title="Optimizador de Rutas", layout="wide")

st.title("🚚 Optimizador de Rutas de Entrega")
st.write("Seleccione un punto de partida y agregue otros puntos en el mapa.")

# 📌 Configurar sesión para almacenar puntos seleccionados
if "puntos" not in st.session_state:
    st.session_state["puntos"] = []
if "origen" not in st.session_state:
    st.session_state["origen"] = None  # Sin origen por defecto

# 📌 Barra lateral con opciones
st.sidebar.header("📌 Ingresar Puntos Manualmente")

lat_input = st.sidebar.number_input("Latitud", value=-12.046400, format="%.6f")
lon_input = st.sidebar.number_input("Longitud", value=-77.042800, format="%.6f")

if st.sidebar.button("➕ Agregar Punto"):
    st.session_state["puntos"].append((lat_input, lon_input))
    st.sidebar.success(f"📍 Punto agregado: ({lat_input}, {lon_input})")

st.sidebar.subheader("📍 Puntos Seleccionados")
for idx, (lat, lon) in enumerate(st.session_state["puntos"]):
    st.sidebar.write(f"{idx+1}. ({lat}, {lon})")

# 📌 Selección del punto de origen
st.sidebar.subheader("📌 Punto de Origen")
if st.session_state["puntos"]:
    origen_idx = st.sidebar.selectbox("Selecciona el punto de origen:", range(len(st.session_state["puntos"])))
    st.session_state["origen"] = st.session_state["puntos"][origen_idx]

if st.sidebar.button("🗑 Borrar Puntos"):
    st.session_state["puntos"] = []
    st.session_state["origen"] = None
    st.sidebar.warning("⚠️ Se han eliminado todos los puntos.")

# 📌 Crear columnas para los mapas
col1, col2 = st.columns(2)

# 📌 Mapa de selección de puntos
with col1:
    st.subheader("📍 Mapa de Selección")
    mapa_seleccion = folium.Map(location=[-12.0464, -77.0428], zoom_start=12)

    # 📍 Agregar los puntos al mapa
    for idx, (lat, lon) in enumerate(st.session_state["puntos"]):
        color = "red" if (lat, lon) == st.session_state["origen"] else "blue"
        folium.Marker(
            [lat, lon], 
            popup=f"Punto {idx+1}", 
            tooltip=f"Orden: {idx+1}",
            icon=folium.Icon(color=color)
        ).add_to(mapa_seleccion)

    map_data = st_folium(mapa_seleccion, height=500, width=500)

    # 📌 Capturar clics en el mapa
    if map_data and map_data.get("last_clicked") is not None:
        click_lat = map_data["last_clicked"].get("lat", None)
        click_lon = map_data["last_clicked"].get("lng", None)

        if click_lat is not None and click_lon is not None:
            st.session_state["puntos"].append((click_lat, click_lon))
            st.rerun()

# 📌 Mapa con la ruta óptima
with col2:
    st.subheader("📍 Ruta Óptima")

    if st.button("🚀 Calcular Ruta Óptima"):
        if len(st.session_state["puntos"]) < 2:
            st.warning("⚠️ Selecciona al menos 2 puntos para calcular la ruta óptima.")
        elif st.session_state["origen"] is None:
            st.warning("⚠️ Debes seleccionar un punto de origen.")
        else:
            ruta_optima = calcular_ruta_optima(st.session_state["puntos"], st.session_state["origen"])
            if ruta_optima:
                st.success(f"✅ Ruta óptima calculada.")
                
                # Generar mapa con la ruta óptima
                m_resultado = folium.Map(location=st.session_state["origen"], zoom_start=12)

                # 📌 Dibujar los puntos en el mapa con números de orden
                for i, (lat, lon) in enumerate(ruta_optima):
                    color = "red" if (lat, lon) == st.session_state["origen"] else "blue"

                    # 📍 Marcador con popup y color diferente para el origen
                    folium.Marker(
                        [lat, lon],
                        popup=f"Punto {i+1} (Orden {i+1})",
                        icon=folium.Icon(color=color),
                    ).add_to(m_resultado)

                    # 🔢 Etiqueta visual con el número de orden
                    folium.map.Marker(
                        [lat, lon],
                        icon=folium.DivIcon(
                            html=f"""<div style="font-size: 14pt; font-weight: bold; color: red;">{i+1}</div>"""
                        ),
                    ).add_to(m_resultado)

                # 📌 Conectar puntos con líneas para visualizar la ruta
                for i in range(len(ruta_optima) - 1):
                    lat1, lon1 = ruta_optima[i]
                    lat2, lon2 = ruta_optima[i+1]
                    folium.PolyLine([(lat1, lon1), (lat2, lon2)], color="blue", weight=2.5).add_to(m_resultado)

                # 📌 Mostrar el mapa con la ruta óptima
                folium_static(m_resultado)
