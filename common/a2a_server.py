# common/a2a_server.py
from fastapi import FastAPI
import uvicorn # Aunque uvicorn se usa en __main__.py, importarlo aquí no causa problema
                # y es a veces útil para tipado o stubs si se expande la función.

def create_app(agent_executor: object) -> FastAPI:
    """
    Crea una aplicación FastAPI con un endpoint /run estándar que delega
    la ejecución al método 'execute' del objeto agente_executor proporcionado.

    Args:
        agent_executor (object): Un objeto que debe tener un método asíncrono
                                 `execute(payload: dict) -> dict`.

    Returns:
        FastAPI: Una instancia de la aplicación FastAPI configurada.
    """
    app = FastAPI()

    @app.post("/run")
    async def run_agent_logic(payload: dict) -> dict:
        """
        Endpoint que recibe la carga útil y la pasa al método execute del agente.
        """
        # Aquí asumimos que el objeto 'agent' (o 'agent_executor')
        # tiene un método 'execute' que toma el payload.
        return await agent_executor.execute(payload)

    # Opcionalmente, puedes añadir el endpoint .well-known/agent.json aquí
    # si todos tus agentes van a tener uno y quieres centralizar su servicio,
    # aunque el PDF lo muestra como un archivo estático por agente.
    # Por ahora, seguiremos la estructura del PDF con archivos agent.json estáticos.

    return app