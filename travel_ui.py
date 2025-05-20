# travel_ui.py
import streamlit as st
import requests # Para hacer la solicitud HTTP al host_agent
import json # Para manejar/mostrar JSON si es necesario, aunque aquí usamos markdown
from datetime import date # Para valores por defecto en date_input

# Configuración de la página de Streamlit
st.set_page_config(page_title="Planificador de Viajes ADK", page_icon="✈️", layout="wide")

# Título de la aplicación
st.title("✈️ Planificador de Viajes Potenciado por ADK")
st.markdown("Ingresa los detalles de tu viaje y nuestros agentes inteligentes te ayudarán a planificarlo.")

# --- Formulario de Entrada del Usuario ---
with st.form("travel_form"):
    st.header("Ingresa los Detalles de tu Viaje")
    
    col1, col2 = st.columns(2)
    
    with col1:
        origin = st.text_input("📍 Origen del Vuelo", placeholder="Ej: Ciudad de México")
        destination = st.text_input("🎯 Destino", placeholder="Ej: París")
    
    with col2:
        today = date.today()
        # Usamos start_date_input para referirnos al valor seleccionado
        start_date_input = st.date_input("🗓️ Fecha de Inicio", 
                                         value=today, 
                                         min_value=today, 
                                         key="start_date_picker") # Añadir una clave única es buena práctica
        
        # El valor por defecto de end_date_input ahora es start_date_input
        # y su min_value también es start_date_input.
        end_date_input = st.date_input("🗓️ Fecha de Fin", 
                                       value=start_date_input, # CORRECCIÓN: valor por defecto basado en start_date_input
                                       min_value=start_date_input, # min_value es el start_date_input
                                       key="end_date_picker") # Añadir una clave única
        
    budget = st.number_input("💰 Presupuesto Total del Viaje (USD)", min_value=100, step=50, value=1000)
    
    # El botón de envío está correctamente aquí dentro del formulario
    submit_button = st.form_submit_button(label="🚀 Planificar Mi Viaje")

# --- Lógica de Procesamiento y Visualización de Resultados ---
if submit_button:
    # Validar que todos los campos necesarios estén llenos
    # Usamos los nombres de variable de los widgets: start_date_input y end_date_input
    if not all([origin, destination, start_date_input, end_date_input, budget]):
        st.warning("⚠️ Por favor, completa todos los detalles del viaje.")
    # La restricción min_value en end_date_input ya previene que end_date_input < start_date_input.
    # Pero una comprobación explícita para start_date_input > end_date_input es redundante pero inofensiva.
    # En la práctica, con min_value bien puesto, este 'elif' no debería activarse si la lógica es correcta.
    elif start_date_input > end_date_input: 
         st.warning("⚠️ La fecha de fin no puede ser anterior a la fecha de inicio. (Este error no debería ocurrir con la lógica actual).")
    else:
        with st.spinner("🌍 Contactando a nuestros agentes especializados... ¡Esto puede tardar un momento!"):
            # Construir el payload para el host_agent
            payload = {
                "origin": origin,
                "destination": destination,
                "start_date": str(start_date_input), # Usar el valor del widget
                "end_date": str(end_date_input),   # Usar el valor del widget
                "budget": budget
            }
            
            # URL del host_agent
            host_agent_url = "http://localhost:8000/run"
            
            try:
                # Enviar la solicitud POST al host_agent
                response = requests.post(host_agent_url, json=payload, timeout=180) # Timeout generoso
                response.raise_for_status() # Lanza una excepción para respuestas HTTP 4xx/5xx
                
                data = response.json()
                
                st.success("🎉 ¡Hemos recibido tu plan de viaje!")
                
                # Mostrar los resultados
                # El PDF usa data["flights"], data["stay"], data["activities"] [cite: 118]
                # Nuestro host_agent.task_manager está diseñado para devolver strings (listas como string, o mensajes de error)
                # bajo estas claves. Streamlit st.markdown puede manejar bien esto.

                st.subheader("✈️ Vuelos Sugeridos")
                if isinstance(data.get("flights"), list) and data.get("flights"):
                    for flight in data["flights"]:
                        st.markdown(f"- **Aerolínea:** {flight.get('airline', 'N/D')}")
                        st.markdown(f"  - **Precio:** {flight.get('price', 'N/D')}")
                        st.markdown(f"  - **Salida:** {flight.get('departure_time', 'N/D')}")
                        st.markdown(f"  - **Detalles:** {flight.get('flight_details', 'N/D')}")
                elif isinstance(data.get("flights"), str): # Si es un mensaje de error o "no encontrado"
                     st.info(data.get("flights"))
                else:
                    st.info("No se encontraron opciones de vuelo o hubo un error al consultarlas.")

                st.subheader("🏨 Opciones de Alojamiento")
                if isinstance(data.get("stay"), list) and data.get("stay"): # El PDF usa 'stay' para la clave en la UI
                    for stay_option in data["stay"]:
                        st.markdown(f"- **Hotel:** {stay_option.get('hotel_name', 'N/D')}")
                        st.markdown(f"  - **Precio/Noche:** {stay_option.get('price_per_night', 'N/D')}")
                        st.markdown(f"  - **Ubicación:** {stay_option.get('location', 'N/D')}")
                        st.markdown(f"  - **Detalles:** {stay_option.get('details', 'N/D')}")
                elif isinstance(data.get("stay"), str):
                     st.info(data.get("stay"))
                else:
                    st.info("No se encontraron opciones de alojamiento o hubo un error al consultarlas.")
                
                st.subheader("🏞️ Actividades Recomendadas")
                if isinstance(data.get("activities"), list) and data.get("activities"):
                    for activity in data["activities"]:
                        st.markdown(f"- **Actividad:** {activity.get('name', 'N/D')}")
                        st.markdown(f"  - **Descripción:** {activity.get('description', 'N/D')}")
                        st.markdown(f"  - **Precio Estimado:** {activity.get('price_estimate', 'N/D')}")
                elif isinstance(data.get("activities"), str):
                     st.info(data.get("activities"))
                else:
                    st.info("No se encontraron actividades o hubo un error al consultarlas.")

            except requests.exceptions.HTTPError as http_err:
                st.error(f"😕 Error HTTP al contactar al planificador: {http_err}")
                st.error(f"Detalles: {response.text if 'response' in locals() else 'No hay respuesta detallada.'}")
            except requests.exceptions.ConnectionError as conn_err:
                st.error(f"🔌 Error de conexión: No se pudo conectar al servidor del planificador en {host_agent_url}. ¿Está el host_agent en ejecución?")
            except requests.exceptions.Timeout as timeout_err:
                st.error(f"⏱️ Error: La solicitud al planificador tardó demasiado en responder (timeout).")
            except json.JSONDecodeError:
                st.error("😕 Error: La respuesta del planificador no estaba en formato JSON válido.")
            except Exception as e:
                st.error(f" Ocurrió un error inesperado: {e}")