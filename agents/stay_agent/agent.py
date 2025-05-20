# agents/stay_agent/agent.py
import json
from google.adk.agents import Agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types # Usado para construir el mensaje al LLM
from shared.schemas import TravelRequest, StaysResponse # Importamos nuestros modelos Pydantic

# --- Configuración del Agente de Alojamiento ---
session_service = InMemorySessionService()
USER_ID = "user_stay_agent"
SESSION_ID = "session_stay_agent"
GEMINI_MODEL_NAME = "gemini-2.0-flash"

# Instrucción del sistema para el LLM, enfocada en alojamiento y formato JSON.
SYSTEM_INSTRUCTION = (
    "Eres un asistente de planificación de viajes especializado en encontrar y sugerir opciones de alojamiento (hoteles). "
    "Dado un destino, fechas de viaje y un presupuesto general de viaje, tu tarea es proponer 2-3 opciones de alojamiento que se ajusten a un rango de precio razonable derivado del presupuesto general. "
    "Para cada opción de alojamiento, debes proporcionar: 'hotel_name' (nombre del hotel), "
    "'price_per_night' (precio estimado por noche, incluyendo la moneda, ej. 'Approx 150 USD per night' o 'INR 1800 por noche'), "
    "'location' (ubicación o área general del hotel), y "
    "'details' (descripción breve de los detalles del hotel, como tipo, servicios principales o puntos de interés cercanos). "
    "Interpreta el presupuesto de viaje para estimar un rango adecuado para el costo por noche del hotel. "
    "Tu respuesta DEBE ser un único objeto JSON válido que se adhiera estrictamente al esquema proporcionado. "
    "El objeto JSON debe tener una sola clave raíz llamada 'stays'. El valor de esta clave 'stays' DEBE ser una lista de objetos, donde cada objeto representa una opción de alojamiento. "
    "NO incluyas NINGÚN texto, explicación, comentario, o cualquier carácter ANTES o DESPUÉS del objeto JSON. "
    "NO utilices vallas de bloque de código Markdown. "
    "La respuesta debe ser únicamente el texto del objeto JSON, comenzando estrictamente con un carácter '{' y terminando estrictamente con un carácter '}'. "
    "Todas las claves y los valores de tipo cadena de texto dentro del JSON DEBEN usar comillas dobles. "
    "Si no puedes encontrar opciones de alojamiento adecuadas o la solicitud no es clara, DEBES responder con el siguiente JSON exacto: {\"stays\": []}."
)

# Creación del Agente ADK
stay_agent = Agent(
    name="stay_agent",
    model=GEMINI_MODEL_NAME, # Pasamos el nombre del modelo como string
    description="Recomienda opciones de alojamiento (hoteles) basadas en el destino, fechas y presupuesto del usuario.",
    instruction=SYSTEM_INSTRUCTION,
    output_schema=StaysResponse # Especificamos el modelo Pydantic para la salida
)

# Creación del Runner del Agente
runner = Runner(
    agent=stay_agent,
    session_service=session_service,
    app_name="stay_app"
)

async def execute(request: dict) -> dict:
    """
    Ejecuta la lógica principal del agente de alojamiento.
    """
    try:
        travel_request_data = TravelRequest(**request)
    except Exception as e: # pydantic.ValidationError
        print(f"Error de validación de la solicitud para stay_agent: {e}")
        return {"stays": [], "error": f"Solicitud inválida: {e}"}

    session_service.create_session(
        app_name="stay_app", user_id=USER_ID, session_id=SESSION_ID
    )

    user_prompt = (
        f"Estoy buscando alojamiento en {travel_request_data.destination} "
        f"para las fechas del {travel_request_data.start_date} al {travel_request_data.end_date}. "
        f"Mi presupuesto general para el viaje es de {travel_request_data.budget} USD. "
        f"Por favor, considera este presupuesto para sugerir hoteles con un precio por noche adecuado y proporciona las opciones en el formato JSON especificado."
    )
    
    message_content = types.Content(parts=[types.Part(text=user_prompt)], role="user")
    response_text = ""

    try:
        print(f"DEBUG: stay_agent usando Agent con output_schema={stay_agent.output_schema}")
        async for event in runner.run_async(
            user_id=USER_ID, session_id=SESSION_ID, new_message=message_content
        ):
            if event.is_final_response():
                if event.content and event.content.parts:
                    response_text = event.content.parts[0].text
                break
        
        if not response_text:
            print("ADVERTENCIA: stay_agent no recibió respuesta de texto del modelo.")
            return {"stays": []}

        print(f"DEBUG: stay_agent - Respuesta de texto crudo del LLM: '{response_text}'")

        parsed_json_data = json.loads(response_text)
        validated_response = StaysResponse(**parsed_json_data)
        return validated_response.model_dump()

    except json.JSONDecodeError as e:
        print(f"FALLO AL PARSEAR JSON en stay_agent: {e}. Respuesta recibida:\n{response_text}")
        return {"stays": [], "error": f"Respuesta inválida del modelo (no es JSON válido): {response_text}"}
    except Exception as e: # Captura errores de validación Pydantic y otros.
        print(f"OCURRIÓ UN ERROR INESPERADO en stay_agent: {type(e).__name__} - {e}. Respuesta recibida:\n{response_text}")
        return {"stays": [], "error": f"Error procesando la respuesta: {e}. Texto original: {response_text}"}