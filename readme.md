# Proyecto Planificador de Viajes Multiagente con ADK

## Descripción General
Este proyecto implementa un sistema de planificación de viajes multiagente utilizando Python, el Google Agent Development Kit (ADK), FastAPI para los servicios de los agentes, y un LLM de Google (Gemini) para la generación de contenido. El sistema cuenta con agentes especializados para vuelos, alojamiento y actividades, orquestados por un agente anfitrión. La interfaz de usuario está construida con Streamlit.

Este proyecto se basa en la guía "Kit de Desarrollo de Agentes (ADK): Una guía con proyecto de demostración" de DataCamp[cite: 1, 2], adaptado para usar Gemini como el LLM principal.

## Requisitos Previos
* Python 3.9 o superior.
* `pip` (manejador de paquetes de Python).
* Una clave API de Google válida con acceso a los modelos Gemini (Generative Language API habilitada en tu proyecto de Google Cloud).

## Configuración del Proyecto

1.  **Clonar el Repositorio (Si es un repositorio Git):**
    Si has clonado este proyecto desde un repositorio, navega a su directorio:
    ```bash
    # git clone https://github.com/JoseDevF/planificador_viajes_ADK
    # cd planificador_viajes_adk
    ```
    Si tienes los archivos localmente, simplemente navega al directorio raíz del proyecto.

2.  **Crear un Entorno Virtual (Recomendado):**
    Es una buena práctica trabajar dentro de un entorno virtual para aislar las dependencias del proyecto.
    ```bash
    python -m venv venv
    ```
    Activa el entorno virtual:
    * En macOS y Linux:
        ```bash
        source venv/bin/activate
        ```
    * En Windows:
        ```bash
        venv\Scripts\activate
        ```

3.  **Instalar Dependencias:**
    Asegúrate de tener un archivo `requirements.txt` en la raíz de tu proyecto.

    Luego, instala las dependencias usando pip:
    ```bash
    pip install -r requirements.txt
    ```

4.  **Configurar Variables de Entorno:**
    Crea un archivo llamado `.env` en el directorio raíz del proyecto. Este archivo almacenará tu clave API de Google. Añade la siguiente línea, reemplazando `"TU_CLAVE_API_DE_GOOGLE_AQUI"` con tu clave real:
    ```env
    GOOGLE_API_KEY="TU_CLAVE_API_DE_GOOGLE_AQUI"
    ```
    Esta clave es necesaria para que los agentes puedan hacer llamadas al LLM Gemini.

## Estructura del Proyecto (Simplificada)

.
├── agents/
│   ├── activities_agent/
│   │   ├── .well-known/agent.json
│   │   ├── init.py
│   │   ├── main.py
│   │   ├── agent.py
│   │   └── task_manager.py
│   ├── flight_agent/
│   │   └── ... (estructura similar)
│   ├── host_agent/
│   │   └── ... (estructura similar)
│   └── stay_agent/
│       └── ... (estructura similar)
├── common/
│   ├── init.py
│   ├── a2a_client.py
│   └── a2a_server.py
├── shared/
│   ├── init.py
│   └── schemas.py
├── .env
├── requirements.txt
├── travel_ui.py
└── README.md

## Ejecución de los Agentes y la Interfaz

Para que el sistema completo funcione, necesitas ejecutar los cuatro servidores de los agentes (activities, flight, stay, host) y luego la aplicación Streamlit. Cada servidor de agente debe ejecutarse en su propia terminal o como un proceso en segundo plano.

**Asegúrate de estar en el directorio raíz del proyecto y de que tu entorno virtual (`venv`) esté activado para cada terminal.**

1.  **Iniciar el `activities_agent` (Puerto 8003):**
    Abre una terminal y ejecuta:
    ```bash
    python -m agents.activities_agent.__main__
    ```
    Alternativamente, para desarrollo con recarga automática:
    ```bash
    uvicorn agents.activities_agent.__main__:app --host 0.0.0.0 --port 8003 --reload
    ```

2.  **Iniciar el `flight_agent` (Puerto 8001):**
    Abre una segunda terminal y ejecuta:
    ```bash
    python -m agents.flight_agent.__main__
    ```
    O para desarrollo con recarga automática:
    ```bash
    uvicorn agents.flight_agent.__main__:app --host 0.0.0.0 --port 8001 --reload
    ```

3.  **Iniciar el `stay_agent` (Puerto 8002):**
    Abre una tercera terminal y ejecuta:
    ```bash
    python -m agents.stay_agent.__main__
    ```
    O para desarrollo con recarga automática:
    ```bash
    uvicorn agents.stay_agent.__main__:app --host 0.0.0.0 --port 8002 --reload
    ```

4.  **Iniciar el `host_agent` (Puerto 8000):**
    Abre una cuarta terminal y ejecuta:
    ```bash
    python -m agents.host_agent.__main__
    ```
    O para desarrollo con recarga automática:
    ```bash
    uvicorn agents.host_agent.__main__:app --host 0.0.0.0 --port 8000 --reload
    ```
    *Nota del PDF*: En sistemas tipo Unix (Linux, macOS), podrías ejecutar estos servidores en segundo plano añadiendo `&` al final de cada comando `uvicorn`[cite: 118], por ejemplo: `uvicorn agents.host_agent.__main__:app --port 8000 &`. Sin embargo, para depuración es mejor ver la salida de cada uno en su propia terminal.

5.  **Ejecutar la Interfaz de Usuario Streamlit:**
    Una vez que los cuatro agentes estén en ejecución y escuchando en sus respectivos puertos, abre una quinta terminal y ejecuta:
    ```bash
    streamlit run travel_ui.py
    ```
    Streamlit debería abrir automáticamente la aplicación en tu navegador web (usualmente en `http://localhost:8501`). Si no lo hace, copia la URL local que te proporciona la consola de Streamlit y pégala en tu navegador.

## Cómo Funciona
La interfaz de usuario (`travel_ui.py`) recopila los detalles del viaje del usuario y los envía al `host_agent` (en `http://localhost:8000/run`). El `host_agent` a su vez llama a los agentes especializados:
* `flight_agent` (`http://localhost:8001/run`) para opciones de vuelo.
* `stay_agent` (`http://localhost:8002/run`) para opciones de alojamiento.
* `activities_agent` (`http://localhost:8003/run`) para sugerencias de actividades.

Finalmente, el `host_agent` consolida estas respuestas y las devuelve a la interfaz de usuario Streamlit para su visualización.

---