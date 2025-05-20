# agents/flight_agent/__main__.py
import uvicorn
from dotenv import load_dotenv # Para cargar variables de entorno desde .env
import os # Opcional, para depuración de variables de entorno

from common.a2a_server import create_app # Utilidad para crear la app FastAPI
from .task_manager import run as flight_agent_run_function # Función 'run' del task_manager

# Cargar variables de entorno del archivo .env ubicado en la raíz del proyecto.
# Es importante que esto se ejecute antes de que cualquier parte del código intente acceder a ellas.
load_dotenv()

# Opcional: Depuración para verificar si la clave API se cargó.
# GOOGLE_API_KEY_LOADED = os.getenv("GOOGLE_API_KEY")
# if GOOGLE_API_KEY_LOADED:
#     print(f"DEBUG flight_agent __main__.py: GOOGLE_API_KEY cargada (últimos 4 chars): ...{GOOGLE_API_KEY_LOADED[-4:]}")
# else:
#     print("DEBUG flight_agent __main__.py: GOOGLE_API_KEY NO ENCONTRADA en el entorno.")

# Clase contenedora simple para cumplir con la interfaz que espera 'create_app'.
# 'create_app' espera un objeto con un método asíncrono 'execute'.
class AgentExecutor:
    async def execute(self, payload: dict) -> dict:
        """Ejecuta la función principal del agente de vuelos."""
        return await flight_agent_run_function(payload)

# Crear una instancia del ejecutor.
agent_executor_instance = AgentExecutor()

# Crear la aplicación FastAPI usando la utilidad compartida.
app = create_app(agent_executor=agent_executor_instance)

# Punto de entrada para ejecutar el servidor Uvicorn.
if __name__ == "__main__":
    print("Iniciando servidor para Flight Agent en el puerto 8001...")
    # El puerto 8001 se usa para el flight_agent según la estructura del proyecto del PDF. [cite: 104]
    uvicorn.run(app, host="0.0.0.0", port=8001)