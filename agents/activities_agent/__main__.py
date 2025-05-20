# agents/activities_agent/__main__.py
import uvicorn
from dotenv import load_dotenv # Importar load_dotenv
import os
from common.a2a_server import create_app # Desde nuestra utilidad común
from .task_manager import run as agent_run_function # La función 'run' de nuestro task_manager

load_dotenv() # Cargar variables desde .env al entorno

# ---- Inicio: Líneas de depuración ----
loaded_api_key = os.getenv("GOOGLE_API_KEY")
if loaded_api_key:
    print(f"DEBUG: GOOGLE_API_KEY cargada en __main__.py: ...{loaded_api_key[-4:]}") # Muestra solo los últimos 4 caracteres
else:
    print("DEBUG: GOOGLE_API_KEY NO encontrada en el entorno después de load_dotenv()")
# ---- Fin: Líneas de depuración ----

# Para que create_app funcione, necesita un objeto que tenga un método 'execute'.
# Creamos un objeto simple sobre la marcha que cumple con este contrato. [cite: 83]
# El PDF usa type("Agent", (), {"execute": agent_run_function}) lo que es una forma
# de crear una clase anónima y luego instanciarla.
# Una forma más explícita podría ser:
class AgentExecutor:
    async def execute(self, payload: dict) -> dict:
        return await agent_run_function(payload)

agent_executor_instance = AgentExecutor()

# Crear la aplicación FastAPI usando nuestra utilidad y el ejecutor del agente
app = create_app(agent_executor=agent_executor_instance)

if __name__ == "__main__":
    # Iniciar el servidor FastAPI con Uvicorn. [cite: 81]
    # El puerto 8003 se usa para el activities_agent según el documento.
    uvicorn.run(app, host="0.0.0.0", port=8003)