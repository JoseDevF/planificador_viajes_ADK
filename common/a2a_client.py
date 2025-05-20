# common/a2a_client.py
import httpx
import asyncio

async def call_agent(url: str, payload: dict) -> dict:
    """
    Realiza una llamada asíncrona a otro agente a través de su endpoint /run.

    Args:
        url (str): La URL del endpoint /run del agente a llamar.
        payload (dict): El diccionario de datos (basado en TravelRequest) a enviar.

    Returns:
        dict: La respuesta JSON del agente.

    Raises:
        httpx.HTTPStatusError: Si la respuesta del agente no es exitosa (código de estado >= 400).
    """
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, json=payload, timeout=60.0)
            response.raise_for_status()  # Lanza una excepción para respuestas 4xx/5xx
            return response.json()
        except httpx.HTTPStatusError as e:
            # Podrías añadir un logging más robusto aquí
            print(f"Error al llamar al agente en {url}: {e}")
            # Devuelve un error estructurado si lo prefieres, o relanza la excepción
            # Para este ejemplo, devolvemos un diccionario con el error.
            return {"error": str(e), "details": e.response.text if e.response else "No response"}
        except httpx.RequestError as e:
            # Para otros errores de red (ej. no se puede conectar)
            print(f"Error de solicitud al agente en {url}: {e}")
            return {"error": f"Request error to {url}: {e}"}