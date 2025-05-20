# agents/stay_agent/__main__.py
import uvicorn
from dotenv import load_dotenv
import os

from common.a2a_server import create_app
from .task_manager import run as stay_agent_run_function

load_dotenv()

# Opcional: Depuración para la clave API
# GOOGLE_API_KEY_LOADED = os.getenv("GOOGLE_API_KEY")
# if GOOGLE_API_KEY_LOADED:
#     print(f"DEBUG stay_agent __main__.py: GOOGLE_API_KEY cargada (últimos 4 chars): ...{GOOGLE_API_KEY_LOADED[-4:]}")
# else:
#     print("DEBUG stay_agent __main__.py: GOOGLE_API_KEY NO ENCONTRADA.")

class AgentExecutor:
    async def execute(self, payload: dict) -> dict:
        return await stay_agent_run_function(payload)

agent_executor_instance = AgentExecutor()
app = create_app(agent_executor=agent_executor_instance)

if __name__ == "__main__":
    print("Iniciando servidor para Stay Agent en el puerto 8002...")
    # El puerto 8002 se usa para el stay_agent. [cite: 105]
    uvicorn.run(app, host="0.0.0.0", port=8002)