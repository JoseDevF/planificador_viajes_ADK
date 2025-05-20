# agents/host_agent/agent.py
from google.adk.agents import Agent
# No necesitamos LiteLlm aquí si seguimos el patrón de pasar el nombre del modelo como string
# from google.adk.models.lite_llm import LiteLlm 
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types # Para construir el mensaje al LLM si es necesario
from shared.schemas import TravelRequest # Para validación si este agente procesara el request directamente

# --- Configuración del Host Agent (como Agente LLM) ---
session_service = InMemorySessionService()
USER_ID = "user_host_agent"
SESSION_ID = "session_host_agent"
GEMINI_MODEL_NAME = "gemini-2.0-flash" # Modelo para el host_agent si realiza tareas LLM

# Instrucción del sistema para el LLM del host_agent.
# Describe su rol como orquestador y para una posible tarea de resumen.
# Como indica el PDF[cite: 98], el LLM no se usa para llamar subagentes en esta implementación,
# pero se define su rol para futuras ampliaciones.
SYSTEM_INSTRUCTION = (
    "Eres el agente anfitrión (host_agent) y tu principal responsabilidad es coordinar la planificación de un viaje. "
    "Recibes una solicitud de viaje y, aunque la orquestación de llamadas a subagentes se maneja externamente (en task_manager.py), "
    "tu rol con LLM podría ser, si se te solicita, resumir o presentar de forma unificada los resultados "
    "obtenidos de los agentes especializados en vuelos, alojamiento y actividades. "
    "Por ahora, si se te llama directamente con una solicitud de viaje, puedes ofrecer un resumen general de la tarea de planificación."
)

# Creación del Agente ADK para el host_agent.
# No especificamos output_schema aquí a menos que su función 'execute'
# deba devolver una estructura JSON específica y compleja generada por el LLM.
# Para la función de orquestación del task_manager, esto no es directamente relevante.
host_llm_agent = Agent( # Renombrado para diferenciar del concepto general de "host_agent"
    name="host_llm_agent", # Nombre del agente LLM interno del host
    model=GEMINI_MODEL_NAME,
    description="Agente LLM coordinador para la planificación de viajes. Puede resumir información.",
    instruction=SYSTEM_INSTRUCTION
)

# Runner para el host_llm_agent (si se usa su capacidad LLM)
host_llm_runner = Runner(
    agent=host_llm_agent,
    session_service=session_service,
    app_name="host_llm_app"
)

async def execute_llm_task(request: dict) -> dict:
    """
    Ejecuta una tarea LLM para el host_agent, como generar un resumen.
    Esta función se llamaría si el host_agent necesitara usar su LLM
    para algo más que la orquestación directa hecha por task_manager.py.
    Por ejemplo, si quisiéramos que el LLM del host_agent generara un texto introductorio
    o un resumen final basado en los datos de la solicitud.

    Args:
        request (dict): La solicitud entrante.

    Returns:
        dict: Un diccionario con un resumen o mensaje.
    """
    try:
        TravelRequest(**request) # Validar que la solicitud sea la esperada
    except Exception as e:
        print(f"Error de validación en host_agent.execute_llm_task: {e}")
        return {"summary": "La solicitud de viaje no es válida."}

    session_service.create_session(
        app_name="host_llm_app", user_id=USER_ID, session_id=SESSION_ID
    )

    # Prompt para una tarea de resumen/confirmación por el LLM del host
    prompt_text = (
        f"He recibido una solicitud para planificar un viaje a {request.get('destination')} "
        f"desde {request.get('start_date')} hasta {request.get('end_date')} "
        f"con un presupuesto de {request.get('budget')} USD desde {request.get('origin', 'un origen no especificado')}. "
        f"Confirma la recepción de esta tarea de planificación."
    )
    message = types.Content(parts=[types.Part(text=prompt_text)], role="user")
    summary_text = "No se pudo generar un resumen."

    async for event in host_llm_runner.run_async(
        user_id=USER_ID, session_id=SESSION_ID, new_message=message
    ):
        if event.is_final_response():
            if event.content and event.content.parts:
                summary_text = event.content.parts[0].text
            break
    
    return {"summary": summary_text, "details_received": request}

# NOTA: La función que realmente se conectará al endpoint /run del host_agent
# y que orquestará las llamadas a otros agentes será la función 'run'
# en 'task_manager.py'. Esta 'execute_llm_task' es para el caso de que el
# propio host_agent necesite realizar una tarea de LLM independiente.