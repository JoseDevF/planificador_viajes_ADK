# shared/schemas.py
from pydantic import BaseModel, Field
from typing import List, Optional

class TravelRequest(BaseModel):
    """
    Define la estructura para una solicitud de viaje.
    """
    destination: str
    start_date: str
    end_date: str
    budget: float
    origin: str = Field(description="El origen del vuelo.") # 'origin' es importante para vuelos

class Activity(BaseModel):
    """
    Define la estructura para una única actividad turística.
    """
    name: str = Field(description="El nombre de la actividad turística.")
    description: str = Field(description="Una breve descripción de la actividad.")
    price_estimate: str = Field(description="Estimación del precio de la actividad en la moneda local aproximada.")

class ActivitiesResponse(BaseModel):
    """
    Define la estructura para la respuesta del agente de actividades,
    conteniendo una lista de actividades.
    """
    activities: List[Activity] = Field(description="Una lista de actividades turísticas sugeridas.")

# --- INICIO: Nuevos modelos para la respuesta de vuelos ---
class FlightOption(BaseModel):
    """
    Define la estructura para una opción de vuelo.
    """
    airline: str = Field(description="Nombre de la aerolínea.")
    price: str = Field(description="Precio estimado del vuelo, incluyendo moneda (ej. '$1,450 USD').") # El ejemplo del PDF usa string con '$'
    departure_time: str = Field(description="Fecha y hora de salida (ej. '04:30 PM on April 13, 2025').")
    flight_details: str = Field(description="Detalles adicionales del vuelo como paradas, servicios, etc.")

class FlightsResponse(BaseModel):
    """
    Define la estructura para la respuesta del agente de vuelos,
    conteniendo una lista de opciones de vuelo.
    """
    flights: List[FlightOption] = Field(description="Una lista de opciones de vuelo sugeridas.")
# --- FIN: Nuevos modelos para la respuesta de vuelos ---

# --- INICIO: Nuevos modelos para la respuesta de alojamiento ---
class StayOption(BaseModel):
    """
    Define la estructura para una opción de alojamiento.
    """
    hotel_name: str = Field(description="Nombre del hotel o alojamiento.")
    price_per_night: str = Field(description="Precio estimado por noche, incluyendo moneda (ej. 'INR 1800 per night').")
    location: str = Field(description="Ubicación o área general del hotel.")
    details: str = Field(description="Breve descripción o detalles relevantes del hotel.")

class StaysResponse(BaseModel):
    """
    Define la estructura para la respuesta del agente de alojamiento.
    """
    stays: List[StayOption] = Field(description="Una lista de opciones de alojamiento sugeridas.") # El PDF usa "stays" para la clave en la UI, así que lo usaré aquí también.
# --- FIN: Nuevos modelos para la respuesta de alojamiento ---