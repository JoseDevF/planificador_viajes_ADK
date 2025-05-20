# agents/stay_agent/task_manager.py
from .agent import execute

async def run(payload: dict) -> dict:
    """
    Actúa como un intermediario para invocar la lógica principal del stay_agent.
    """
    return await execute(payload)