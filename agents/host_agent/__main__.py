# agents/host_agent/__main__.py
import uvicorn
from dotenv import load_dotenv
import os

from common.a2a_server import create_app
# La función 'run' que queremos usar es la del task_manager,
# que orquesta las llamadas a otros agentes.
from .task_manager import run as host_agent_orchestration_run

load_dotenv()
# Opcional: Depuración para la clave API (aunque el host_agent.task_manager no la usa directamente,
# es bueno para consistencia si el agent.py del host sí la usara).
# GOOGLE_API_KEY_LOADED = os.getenv("GOOGLE_API_KEY")
# if GOOGLE_API_KEY_LOADED:
#     print(f"DEBUG host_agent __main__.py: GOOGLE_API_KEY cargada (últimos 4 chars): ...{GOOGLE_API_KEY_LOADED[-4:]}")
# else:
#     print("DEBUG host_agent __main__.py: GOOGLE_API_KEY NO ENCONTRADA.")

class AgentExecutor:
    async def execute(self, payload: dict) -> dict:
        # Esta función 'execute' será llamada por el a2a_server.
        # Debe llamar a la lógica de orquestación de nuestro task_manager.
        return await host_agent_orchestration_run(payload)

agent_executor_instance = AgentExecutor()
app = create_app(agent_executor=agent_executor_instance)

if __name__ == "__main__":
    print("Iniciando servidor para Host Agent en el puerto 8000...")
    # El puerto 8000 se usa para el host_agent según el PDF. [cite: 110]
    uvicorn.run(app, host="0.0.0.0", port=8000)