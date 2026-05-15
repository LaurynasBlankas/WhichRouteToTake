from google import genai
from google.genai import types
from dotenv import load_dotenv
import requests
import json
import os

load_dotenv()
gemini_api = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
openroute_api = os.getenv("OPEN_ROUTE_KEY")

start = json.loads(os.getenv("STARTPOINT"))
end = json.loads(os.getenv("ENDPOINT"))

via_gelezinio = [54.67289742078834, 25.239826325151537]
via_olandu = [54.692477785393024, 25.305084347042996]


def get_route(via_point):
    start_str = f"{start[0]},{start[1]}"
    via_str = f"{via_point[0]},{via_point[1]}"
    end_str = f"{end[0]},{end[1]}"

    url = f"https://api.tomtom.com/routing/1/calculateRoute/{start_str}:{via_str}:{end_str}/json"

    params = {
        "key": os.getenv("TOMTOM_API_KEY"),
        "traffic": "true",
        "travelMode": "car",
        "routeType": "fastest"
    }

    response = requests.get(url, params=params)
    data = response.json()
    summary = data["routes"][0]["summary"]

    return {
        "duration_min": round(summary["travelTimeInSeconds"] / 60, 1),
        "distance_km": round(summary["lengthInMeters"] / 1000, 2)
    }


print("Fetching routes...\n")
route_gelezinio = get_route(via_gelezinio)
route_olandu = get_route(via_olandu)

prompt = f"""
I need to drive from {start} to {end}.
I have two route options:

Route 1 - via Geležinio Vilko g:
- Duration: {route_gelezinio['duration_min']} minutes
- Distance: {route_gelezinio['distance_km']} km

Route 2 - via Olandų g:
- Duration: {route_olandu['duration_min']} minutes
- Distance: {route_olandu['distance_km']} km

Which route do you recommend and why? Be concise.
"""

response = gemini_api.models.generate_content(
    model="gemini-2.5-flash",
    contents=prompt
)

print(f"Geležinio Vilko g: {route_gelezinio['duration_min']} min, {route_gelezinio['distance_km']} km")
print(f"Olandų g:          {route_olandu['duration_min']} min, {route_olandu['distance_km']} km")
print(f"\nGemini says:\n{response.text}")