# agents/flight_agent/agent.py
import json
from google.adk.agents import Agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types # Usado para construir el mensaje al LLM
from shared.schemas import TravelRequest, FlightsResponse # Importamos nuestros modelos Pydantic

# --- Configuración del Agente de Vuelos ---
session_service = InMemorySessionService() # Servicio de sesión en memoria
USER_ID = "user_flight_agent" # Identificador de usuario para la sesión
SESSION_ID = "session_flight_agent" # Identificador de sesión
GEMINI_MODEL_NAME = "gemini-2.0-flash" # Nombre del modelo Gemini a utilizar

# Instrucción del sistema para el LLM, enfocada en vuelos y formato JSON.
# Esta instrucción es crucial para guiar al LLM.
SYSTEM_INSTRUCTION = (
    "Eres un asistente de planificación de viajes especializado en encontrar y sugerir opciones de vuelo. "
    "Dado un origen, destino, fechas de viaje y un presupuesto, tu tarea es proponer 2-3 opciones de vuelo adecuadas. "
    "Para cada opción de vuelo, debes proporcionar: 'airline' (nombre de la aerolínea), "
    "'price' (precio estimado del vuelo, incluyendo la moneda, ej. '$1500 USD'), "
    "'departure_time' (fecha y hora de salida formateada, ej. '04:30 PM on April 13, 2025'), y "
    "'flight_details' (descripción breve de los detalles del vuelo como si es directo, número de paradas, servicios principales). "
    "Asegúrate de que las opciones de vuelo se ajusten razonablemente al presupuesto del usuario si es posible, mencionando si se excede. "
    "Tu respuesta DEBE ser un único objeto JSON válido que se adhiera estrictamente al esquema proporcionado. "
    "El objeto JSON debe tener una sola clave raíz llamada 'flights'. El valor de esta clave 'flights' DEBE ser una lista de objetos, donde cada objeto representa una opción de vuelo. "
    "NO incluyas NINGÚN texto, explicación, comentario, o cualquier carácter ANTES o DESPUÉS del objeto JSON. "
    "NO utilices vallas de bloque de código Markdown. "
    "La respuesta debe ser únicamente el texto del objeto JSON, comenzando estrictamente con un carácter '{' y terminando estrictamente con un carácter '}'. "
    "Todas las claves y los valores de tipo cadena de texto dentro del JSON DEBEN usar comillas dobles. "
    "Si no puedes encontrar opciones de vuelo adecuadas o la solicitud no es clara, DEBES responder con el siguiente JSON exacto: {\"flights\": []}."
)

# Creación del Agente ADK, pasando el nombre del modelo y el output_schema.
# Esto permite al ADK optimizar la interacción con el LLM para obtener JSON estructurado.
flight_agent = Agent(
    name="flight_agent",
    model=GEMINI_MODEL_NAME, # Pasamos el nombre del modelo como string
    description="Recomienda opciones de vuelo basadas en las preferencias del usuario y un presupuesto.",
    instruction=SYSTEM_INSTRUCTION,
    output_schema=FlightsResponse # Especificamos el modelo Pydantic para la salida
)

# Creación del Runner del Agente.
# El Runner gestiona la ejecución del agente para una sesión de aplicación concreta.
runner = Runner(
    agent=flight_agent,
    session_service=session_service,
    app_name="flight_app" # Nombre de la aplicación para la sesión
)

async def execute(request: dict) -> dict:
    """
    Ejecuta la lógica principal del agente de vuelos.
    Recibe una solicitud, construye un prompt, invoca el LLM a través del Runner,
    y analiza la salida JSON en el formato esperado.

    Args:
        request (dict): La solicitud entrante, que se espera que cumpla con TravelRequest.

    Returns:
        dict: Un diccionario que cumple con FlightsResponse, o un diccionario de error.
    """
    try:
        # Validar la solicitud entrante con el modelo Pydantic TravelRequest.
        travel_request_data = TravelRequest(**request)
    except Exception as e: # Captura pydantic.ValidationError
        print(f"Error de validación de la solicitud para flight_agent: {e}")
        # Devuelve un error con la estructura esperada si es posible, o un mensaje genérico.
        return {"flights": [], "error": f"Solicitud inválida: {e}"}

    # Crear (o asegurar la existencia de) una sesión ADK.
    session_service.create_session(
        app_name="flight_app", user_id=USER_ID, session_id=SESSION_ID
    )

    # Construir el prompt específico para el usuario.
    # Es importante incluir todos los detalles relevantes de travel_request_data.
    user_prompt = (
        f"Necesito opciones de vuelo desde {travel_request_data.origin} hacia {travel_request_data.destination}, "
        f"viajando desde el {travel_request_data.start_date} hasta el {travel_request_data.end_date}. "
        f"Mi presupuesto aproximado es de {travel_request_data.budget} USD. "
        f"Por favor, proporciona las opciones en el formato JSON especificado en mis instrucciones."
    )
    
    # Crear el objeto Content para el mensaje del usuario.
    message_content = types.Content(parts=[types.Part(text=user_prompt)], role="user")
    response_text = "" # Inicializar para almacenar el texto de la respuesta del LLM.

    try:
        # Invocar el LLM a través del runner de ADK.
        # Se espera que devuelva un generador asíncrono para el streaming de eventos.
        print(f"DEBUG: flight_agent usando Agent con output_schema={flight_agent.output_schema}")
        async for event in runner.run_async(
            user_id=USER_ID, session_id=SESSION_ID, new_message=message_content
        ):
            if event.is_final_response(): # Procesar solo la respuesta final del stream.
                if event.content and event.content.parts:
                    response_text = event.content.parts[0].text # Extraer el texto de la respuesta.
                break # Salir del bucle una vez obtenida la respuesta final.
        
        if not response_text:
            print("ADVERTENCIA: flight_agent no recibió respuesta de texto del modelo.")
            return {"flights": []} # Devolver una lista vacía si no hay respuesta.

        print(f"DEBUG: flight_agent - Respuesta de texto crudo del LLM: '{response_text}'")

        # Parsear la respuesta de texto como JSON.
        # Se espera que sea JSON crudo gracias a output_schema y el prompt.
        parsed_json_data = json.loads(response_text)
        
        # Validar la estructura del JSON parseado con el modelo Pydantic FlightsResponse.
        # Esto asegura que la respuesta del LLM cumple con el contrato esperado.
        validated_response = FlightsResponse(**parsed_json_data)
        
        # Devolver la respuesta validada como un diccionario.
        return validated_response.model_dump() # Para Pydantic v2+
        # return validated_response.dict() # Para Pydantic v1

    except json.JSONDecodeError as e:
        print(f"FALLO AL PARSEAR JSON en flight_agent: {e}. Respuesta recibida:\n{response_text}")
        return {"flights": [], "error": f"Respuesta inválida del modelo (no es JSON válido): {response_text}"}
    except Exception as e: # Captura errores de validación Pydantic y otros errores inesperados.
        print(f"OCURRIÓ UN ERROR INESPERADO en flight_agent: {type(e).__name__} - {e}. Respuesta recibida:\n{response_text}")
        return {"flights": [], "error": f"Error procesando la respuesta: {e}. Texto original: {response_text}"}