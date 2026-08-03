"""LangChain tool factory for the weather assistant."""

import requests
from langchain_core.tools import tool

_TEMP_UNITS = {"celsius", "fahrenheit", "kelvin"}


def _to_kelvin(value: float, unit: str) -> float:
    if unit == "celsius":
        return value + 273.15
    if unit == "fahrenheit":
        return (value - 32) * 5 / 9 + 273.15
    return value


def _from_kelvin(value: float, unit: str) -> float:
    if unit == "celsius":
        return value - 273.15
    if unit == "fahrenheit":
        return (value - 273.15) * 9 / 5 + 32
    return value


def convert_temperature(value: float, from_unit: str, to_unit: str) -> str:
    """Convert a temperature value between celsius, fahrenheit and kelvin."""
    from_unit, to_unit = from_unit.strip().lower(), to_unit.strip().lower()
    if from_unit not in _TEMP_UNITS or to_unit not in _TEMP_UNITS:
        return f"Error: units must be one of {sorted(_TEMP_UNITS)}."
    result = _from_kelvin(_to_kelvin(value, from_unit), to_unit)
    return f"{value} {from_unit} = {round(result, 2)} {to_unit}"


def make_tools(weather_api_key: str, weather_base_url: str):
    """Return [get_current_weather, convert_temperature] bound to the given weather API config."""

    @tool
    def get_current_weather(city: str) -> str:
        """Fetch current weather conditions (temperature, description, humidity, wind) for a city."""
        try:
            response = requests.get(
                f"{weather_base_url}/weather",
                params={"q": city, "appid": weather_api_key, "units": "metric", "lang": "fr"},
                timeout=10,
            )
            if response.status_code == 404:
                return f"Error: city '{city}' not found."
            response.raise_for_status()
            data = response.json()
            return (
                f"Météo à {data['name']} : {data['weather'][0]['description']}, "
                f"{round(data['main']['temp'])}°C (ressenti {round(data['main']['feels_like'])}°C), "
                f"humidité {data['main']['humidity']}%, vent {round(data['wind']['speed'])} m/s."
            )
        except requests.RequestException as e:
            return f"Error: weather service unavailable ({e})."

    @tool
    def convert_temperature_tool(value: float, from_unit: str, to_unit: str) -> str:
        """Convert a temperature value between celsius, fahrenheit and kelvin."""
        return convert_temperature(value, from_unit, to_unit)

    return [get_current_weather, convert_temperature_tool]
