import sys

try:
    import pysqlite3
    sys.modules["sqlite3"] = pysqlite3
except Exception:
    pass

import json
import requests
import streamlit as st
from openai import OpenAI


# Part A: Weather function location in form City, State, Country
# default units is Fahrenheit
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


# Part B: Define the tool
weather_tool = [
    {
        "type": "function",
        "function": {
            "name": "get_current_weather",
            "description": "Get the current weather for a given location name.",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "City, State, Country (e.g., Syracuse, NY, US)",
                    }
                },
                "required": ["location"],
            },
        },
    }
]


# UI
st.title("Lab 05 — The 'What to Wear' Bot")

openai_api_key = st.secrets["OPENAI_API_KEY"]
weather_api_key = st.secrets["OPENWEATHER_API_KEY"]

client = OpenAI(api_key=openai_api_key)

city = st.text_input("Enter a city (example: Syracuse, NY, US)", "")

if st.button("Get What to Wear Advice"):
    # Step 6: Not a chatbot, user inputs a city, bot outputs advice
    user_location = city.strip()

    # First call: give tool to OpenAI with tool_choice='auto'
    # (7a)
    messages = [
        {
            "role": "system",
            "content": (
                "You are a 'What to Wear' assistant. "
                "If you need weather to answer, use the get_current_weather tool."
            ),
        },
        {
            "role": "user",
            "content": (
                f"City: {user_location}\n"
                "Tell me what clothes to wear today and suggest outdoor activities "
                "that fit the weather."
            ),
        },
    ]

    try:
        first_resp = client.chat.completions.create(
            model="gpt-5-mini",
            messages=messages,
            tools=weather_tool,
            tool_choice="auto",
        )

        msg = first_resp.choices[0].message

        # If model requests the tool, run it then make a second call (8)
        tool_calls = getattr(msg, "tool_calls", None)

        if tool_calls:
            # only defined one tool, so handle the first request
            tool_call = tool_calls[0]
            args = {}
            try:
                args = json.loads(tool_call.function.arguments or "{}")
            except Exception:
                args = {}

            # Step 7b: Default to Syracuse, NY if no location provided
            requested_location = (args.get("location") or "").strip()
            if not requested_location:
                requested_location = "Syracuse, NY"

            weather = get_current_weather(requested_location, weather_api_key)

            # Second call: Provide weather info as part of the prompt (8a)
            messages_2 = [
                {
                    "role": "system",
                    "content": (
                        "You are a 'What to Wear' assistant. "
                        "Use the provided weather information to answer."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        f"Weather info: {weather}\n\n"
                        "Based on this weather, suggest what clothes to wear today "
                        "and suggest outdoor activities that are appropriate."
                    ),
                },
            ]

            second_resp = client.chat.completions.create(
                model="gpt-5-mini",
                messages=messages_2,
            )

            final_answer = second_resp.choices[0].message.content or ""
            st.subheader("Recommendation")
            st.write(final_answer)

        else:
            # If tool wasn't invoked, just show the model's response
            # tool_choice='auto' only calls weather when needed
            st.subheader("Recommendation")
            st.write(msg.content or "")

    except Exception as e:
        st.error(str(e))
