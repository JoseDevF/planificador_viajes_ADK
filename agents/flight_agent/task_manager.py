# agents/flight_agent/task_manager.py
from .agent import execute # Importación relativa de la función execute de agent.py

async def run(payload: dict) -> dict:
    """
    Actúa como un intermediario para invocar la lógica principal del flight_agent.
    Este es el método que el servidor A2A (a través de __main__.py) llamará.

    Args:
        payload (dict): La carga útil de la solicitud, que se pasará a la función execute.

    Returns:
        dict: La respuesta generada por la función execute del agente.
    """
    return await execute(payload)