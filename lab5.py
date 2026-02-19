import sys

try:
    import pysqlite3
    sys.modules["sqlite3"] = pysqlite3
except Exception:
    pass

import requests
import streamlit as st


# location in form City, State, Country (Syracuse, NY, US)
# default units is degrees Fahrenheit
def get_current_weather(location, api_key, units="imperial"):
    url = (
        f"https://api.openweathermap.org/data/2.5/weather"
        f"?q={location}&appid={api_key}&units={units}"
    )

    response = requests.get(url, timeout=20)

    if response.status_code == 401:
        raise Exception("Authentication failed: Invalid API key (401 Unauthorized)")
    if response.status_code == 404:
        error_message = response.json().get("message")
        raise Exception(f"404 error: {error_message}")

    data = response.json()

    temp = data["main"]["temp"]
    feels_like = data["main"]["feels_like"]
    temp_min = data["main"]["temp_min"]
    temp_max = data["main"]["temp_max"]
    humidity = data["main"]["humidity"]

    # weather description 
    description = data["weather"][0]["description"]

    return {
        "location": location,
        "temperature": round(temp, 2),
        "feels_like": round(feels_like, 2),
        "temp_min": round(temp_min, 2),
        "temp_max": round(temp_max, 2),
        "humidity": round(humidity, 2),
        "description": description,
    }


st.title("Lab 05 — The 'What to Wear' Bot (Part A)")

# API key from secrets.toml 
api_key = st.secrets["OPENWEATHER_API_KEY"]

st.subheader("Part A: Test the weather function")

col1, col2 = st.columns(2)

with col1:
    if st.button("Test: Syracuse, NY, US"):
        try:
            st.write(get_current_weather("Syracuse, NY, US", api_key))
        except Exception as e:
            st.error(str(e))

with col2:
    if st.button("Test: Lima, Peru"):
        try:
            st.write(get_current_weather("Lima, Peru", api_key))
        except Exception as e:
            st.error(str(e))