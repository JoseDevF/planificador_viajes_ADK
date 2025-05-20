# agents/host_agent/task_manager.py
import asyncio # Para ejecutar llamadas a agentes de forma concurrente
from common.a2a_client import call_agent # Nuestra utilidad para llamar a otros agentes

# URLs de los endpoints /run de los agentes especializados.
# Asegúrate de que los puertos coincidan con cómo estás ejecutando cada agente.
FLIGHT_AGENT_URL = "http://localhost:8001/run"
STAY_AGENT_URL = "http://localhost:8002/run"
ACTIVITIES_AGENT_URL = "http://localhost:8003/run"

async def run(payload: dict) -> dict:
    """
    Orquesta las llamadas a los agentes de vuelos, alojamiento y actividades.

    Recibe el payload de la solicitud de viaje, lo envía a cada agente especializado
    concurrentemente, y luego agrega sus respuestas.

    Args:
        payload (dict): El payload de la solicitud de viaje (TravelRequest).

    Returns:
        dict: Un diccionario consolidado con las respuestas de todos los agentes.
              Incluye manejo básico de errores si algún agente falla.
    """
    print(f"Host Agent - Task Manager: Recibido payload: {payload}")

    # Realizar llamadas concurrentes a los agentes especializados usando asyncio.gather.
    # call_agent ya es una función async.
    results = await asyncio.gather(
        call_agent(FLIGHT_AGENT_URL, payload),
        call_agent(STAY_AGENT_URL, payload),
        call_agent(ACTIVITIES_AGENT_URL, payload),
        return_exceptions=True  # Importante para que una excepción no detenga todo.
    )

    # Desempaquetar resultados o manejar excepciones.
    # results será una lista: [flight_result, stay_result, activities_result]
    
    flight_response, stay_response, activities_response = results

    # Procesar cada respuesta, verificando si fue una excepción.
    # El PDF sugiere devolver un string si no hay respuesta,
    # pero es mejor devolver la estructura esperada (lista vacía) y una clave de error.

    if isinstance(flight_response, Exception):
        print(f"Error al llamar a Flight Agent: {flight_response}")
        flights_data = {"flights": [], "error": str(flight_response)}
    elif flight_response.get("error"): # Si call_agent devolvió un error estructurado
        print(f"Error desde Flight Agent: {flight_response.get('error')}")
        flights_data = {"flights": [], "error": flight_response.get('error')}
    else:
        flights_data = flight_response.get("flights", []) # Extraer la lista de vuelos

    if isinstance(stay_response, Exception):
        print(f"Error al llamar a Stay Agent: {stay_response}")
        stays_data = {"stays": [], "error": str(stay_response)}
    elif stay_response.get("error"):
        print(f"Error desde Stay Agent: {stay_response.get('error')}")
        stays_data = {"stays": [], "error": stay_response.get('error')}
    else:
        stays_data = stay_response.get("stays", [])

    if isinstance(activities_response, Exception):
        print(f"Error al llamar a Activities Agent: {activities_response}")
        activities_data = {"activities": [], "error": str(activities_response)}
    elif activities_response.get("error"):
        print(f"Error desde Activities Agent: {activities_response.get('error')}")
        activities_data = {"activities": [], "error": activities_response.get('error')}
    else:
        activities_data = activities_response.get("activities", [])

    # Construir la respuesta final consolidada.
    # El PDF [cite: 105] simplemente asigna el resultado o un string.
    # Nosotros devolveremos la estructura de datos o el mensaje de error bajo su respectiva clave.
    final_response = {
        "flights": flights_data if not isinstance(flights_data, dict) or "error" not in flights_data else flights_data,
        "stays": stays_data if not isinstance(stays_data, dict) or "error" not in stays_data else stays_data,
        "activities": activities_data if not isinstance(activities_data, dict) or "error" not in activities_data else activities_data
    }
    
    # Si la sub-respuesta ya es un dict con error y datos, la usamos directamente.
    # Si es solo la lista de datos (ej. flights_data = [...]), la envolvemos.
    # El objetivo es que el frontend pueda buscar response['flights']['flights'] o response['flights']['error']
    
    # Simplificación: La UI espera directamente la lista o el texto del error bajo la clave principal
    # Si la sub-respuesta es un dict (porque tuvo un error), se pasa tal cual.
    # Si es una lista (éxito), se pasa la lista. La UI manejará el tipo.

    final_simplified_response = {
        "flights": flight_response.get("flights", "No se pudieron obtener vuelos." if not isinstance(flight_response, dict) or "error" in flight_response else flight_response),
        "stay": stay_response.get("stays", "No se pudieron obtener opciones de alojamiento." if not isinstance(stay_response, dict) or "error" in stay_response else stay_response), # PDF usa 'stay' singular para la UI
        "activities": activities_response.get("activities", "No se pudieron obtener actividades." if not isinstance(activities_response, dict) or "error" in activities_response else activities_response)
    }
    
    # El PDF en la página 11, para la UI, accede a data["flights"], data["stay"], data["activities"].
    # Y si hubo un error en el call_agent, `call_agent` devuelve un dict con `{"error": ...}`.
    # La lógica del PDF para el `task_manager` del host (pág 9) es:
    # "flights": flights.get("flights", "No flights returned."),
    # "stay": stay.get("stays", "No stay options returned."),
    # "activities": activities.get("activities", "No activities found.")
    # Esto implica que si `flights` es un dict de error, `flights.get("flights", ...)` fallaría o no daría lo esperado.
    # Vamos a ajustar para que coincida mejor con esa expectativa del PDF.

    def get_data_or_error_message(response_dict, data_key, error_message):
        if isinstance(response_dict, dict):
            if "error" in response_dict:
                # Devuelve el mensaje de error específico del subagente si está disponible.
                return response_dict.get("details", str(response_dict["error"])) 
            return response_dict.get(data_key, error_message) # Devuelve los datos si existen.
        return error_message # Si no es un dict (ej. Exception), devuelve mensaje de error genérico.

    final_response_aligned_with_pdf = {
        "flights": get_data_or_error_message(flight_response, "flights", "No se retornaron vuelos o hubo un error."),
        "stay": get_data_or_error_message(stay_response, "stays", "No se retornaron opciones de estadía o hubo un error."), # La UI usa 'stay'
        "activities": get_data_or_error_message(activities_response, "activities", "No se encontraron actividades o hubo un error.")
    }
    
    print(f"Host Agent - Task Manager: Respuesta final: {final_response_aligned_with_pdf}")
    return final_response_aligned_with_pdf