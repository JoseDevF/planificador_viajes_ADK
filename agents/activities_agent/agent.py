# agents/activities_agent/agent.py
import os
import json
from google.adk.agents import Agent
# from google.adk.models.lite_llm import LiteLlm # Corregido para usar LiteLlm
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types # Para construir el mensaje a Gemini
# Importar nuestro esquema compartido
from shared.schemas import TravelRequest, ActivitiesResponse  # Asegúrate que la ruta sea correcta según tu estructura

# --- Configuración del Agente de Actividades ---
# 1. Servicio de Sesión en Memoria
# Para producción, considera alternativas más persistentes si el historial de conversación es largo o crítico.
session_service = InMemorySessionService()

# 2. Identificadores de Usuario y Sesión
# Estos podrían ser dinámicos o específicos del usuario en una aplicación real.
USER_ID = "user_activities_agent"
SESSION_ID = "session_activities_agent"

# 3. Configuración del Modelo LLM (Gemini)
# Asegúrate que tu GOOGLE_API_KEY está configurada en el entorno.
# LiteLlm usará "gemini/gemini-pro" o el modelo que especifiques.
GEMINI_MODEL_NAME = "gemini-2.0-flash" # Puedes cambiarlo a gemini-1.5-flash, etc.

# 4. Instrucción del Sistema para el LLM
# Guía el comportamiento del LLM. [cite: 63]
# Ajustamos el prompt para solicitar JSON y mejorar la robustez.
SYSTEM_INSTRUCTION = (
    "Eres un asistente de planificación de viajes altamente especializado en sugerir actividades turísticas. "
    "Tu tarea es generar una lista de exactamente 2 a 3 actividades basadas en el destino, las fechas y el presupuesto que se te proporcionen. "
    "Para cada actividad, debes incluir obligatoriamente: 'name' (el nombre de la actividad), 'description' (una breve descripción concisa), y 'price_estimate' (una estimación del precio en la moneda local aproximada). "
    "Tu respuesta DEBE ser un único objeto JSON válido que se adhiera estrictamente al esquema proporcionado. "
    "El objeto JSON debe tener una sola clave raíz llamada 'activities'. El valor de esta clave 'activities' DEBE ser una lista de objetos, donde cada objeto representa una actividad. "
    "NO incluyas NINGÚN texto, explicación, comentario, o cualquier carácter ANTES o DESPUÉS del objeto JSON. "
    "NO utilices vallas de bloque de código Markdown. "
    "La respuesta debe ser únicamente el texto del objeto JSON, comenzando estrictamente con un carácter '{' y terminando estrictamente con un carácter '}'. "
    "Todas las claves y los valores de tipo cadena de texto dentro del JSON DEBEN usar comillas dobles. "
    "Si no puedes encontrar actividades adecuadas o la solicitud no es lo suficientemente clara, DEBES responder con el siguiente JSON exacto: {\"activities\": []}."
)

# 5. Creación del Agente ADK
activities_agent = Agent(
    name="activities_agent",
    model=GEMINI_MODEL_NAME,
    description="Sugiere actividades interesantes para el usuario en un destino.",
    instruction=SYSTEM_INSTRUCTION, # Instrucción general para el agente
    output_schema=ActivitiesResponse,
)

# 6. Creación del Runner del Agente
# El Runner maneja la ejecución del agente para una sesión de aplicación concreta.
runner = Runner(
    agent=activities_agent,
    session_service=session_service,
    app_name="activities_app" # Nombre de la aplicación para la sesión
)

async def execute(request: dict) -> dict:
    """
    Ejecuta la lógica principal del agente de actividades.
    Recibe una solicitud, construye un prompt, invoca el LLM y analiza la salida.

    Args:
        request (dict): La solicitud entrante, que se espera que cumpla con TravelRequest.

    Returns:
        dict: Un diccionario con la clave "activities" y una lista de actividades,
              o un texto de fallback si el parseo JSON falla.
    """
    try:
        # Validar con Pydantic (opcional aquí si FastAPI ya lo hace, pero bueno para lógica interna)
        travel_request_data = TravelRequest(**request)
    except Exception as e: # pydantic.ValidationError
        print(f"Error de validación de la solicitud: {e}")
        return {"activities": "Error: Solicitud inválida."}

    # Asegurar que la sesión ADK exista antes de enviar consultas.
    # Esto es importante para que ADK maneje el contexto si fuera necesario.
    session_service.create_session(
        app_name="activities_app",
        user_id=USER_ID,
        session_id=SESSION_ID
    )

    # Construir el prompt específico para el usuario usando los datos de la solicitud. [cite: 67, 68]
    user_prompt = (
        f"Estoy planeando un viaje a {travel_request_data.destination} "
        f"desde {travel_request_data.start_date} hasta {travel_request_data.end_date} "
        f"con un presupuesto aproximado de {travel_request_data.budget} USD. "
        f"Por favor, dame sugerencias de actividades en formato JSON como se te indicó previamente."
    )

    # Crear el mensaje en el formato esperado por el runner de ADK (similar a la API de Gemini)
    # El runner.run_async espera 'message' como un string o un objeto google.generativeai.types.Content
    # Para enviar un mensaje de usuario simple, un string es suficiente.
    # Si necesitaras roles o partes múltiples (ej. imágenes), usarías Content.
    # Aquí, como el system_instruction ya está en el agente, solo pasamos el user_prompt.
    # No obstante, para más control y para ser explícitos con el rol 'user':
    message_content = types.Content(parts=[types.Part(text=user_prompt)], role="user")

    response_text = ""
    try:
        # Invocar el LLM a través del runner de ADK.
        # run_async devuelve un generador asíncrono para el streaming.
        async for event in runner.run_async(
            user_id=USER_ID,
            session_id=SESSION_ID,
            new_message=message_content # Cambiado 'message' por 'new_message'
        ):
            if event.is_final_response():
                # Extraer el texto de la respuesta final. [cite: 73]
                # El contenido puede estar en event.message.parts[0].text o event.content.parts[0].text
                # dependiendo de la versión y configuración. El PDF usa event.content.parts[0].text.
                if event.content and event.content.parts:
                    response_text = event.content.parts[0].text
                break # Salimos del bucle una vez que tenemos la respuesta final
        
        if not response_text:
            return {"activities": "No se recibió respuesta del modelo."}
        
        print(f"Respuesta: {response_text}")

        # Intentar parsear la respuesta como JSON.
        # El prompt pide explícitamente JSON.
        parsed_json = json.loads(response_text)
        if "activities" in parsed_json and isinstance(parsed_json["activities"], list):
            return {"activities": parsed_json["activities"]} # Respuesta estructurada esperada [cite: 74]
        else:
            # Si el JSON no tiene la clave 'activities' o no es una lista. [cite: 75]
            print(f"'activities' key missing or not a list in JSON response: {response_text}")
            # Como fallback, devolvemos el texto crudo si el LLM no siguió el formato JSON.
            # En un caso real, podrías intentar "reparar" el JSON o registrar un error más severo.
            return {"activities": f"Respuesta inesperada del modelo (se esperaba JSON): {response_text}"}

    except json.JSONDecodeError as e:
        # Si el LLM no devuelve un JSON válido. [cite: 75]
        print(f"Fallo al parsear JSON: {e}. Respuesta recibida:\n{response_text}")
        # Devolver el texto crudo como fallback. [cite: 75]
        return {"activities": response_text}
    except Exception as e:
        print(f"Ocurrió un error inesperado durante la ejecución del agente: {e}")
        return {"activities": f"Error interno del servidor: {str(e)}"}