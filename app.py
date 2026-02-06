from flask import Flask, render_template, request
import requests

app = Flask(__name__)

# ===== CONFIG =====
GROK_API_KEY = "YOUR_GROK_API_KEY"
GROK_API_URL = "https://api.x.ai/v1/completions"

GOOGLE_MAPS_API_KEY = "YOUR_GOOGLE_MAPS_API_KEY"
# ==================

def call_grok(prompt):
    headers = {
        "Authorization": f"Bearer {GROK_API_KEY}",
        "Content-Type": "application/json"
    }
    body = {
        "model": "grok-4",
        "prompt": prompt,
        "max_tokens": 60
    }
    try:
        resp = requests.post(GROK_API_URL, headers=headers, json=body)
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"]
    except Exception as e:
        return f"Error fetching Grok commentary: {e}"

def get_coordinates(place):
    """Use Google Maps Geocoding API"""
    try:
        if "India" not in place:
            place = place + ", India"
        url = "https://maps.googleapis.com/maps/api/geocode/json"
        params = {"address": place, "key": GOOGLE_MAPS_API_KEY}
        response = requests.get(url, params=params)
        data = response.json()
        if data["status"] != "OK":
            return None
        loc = data["results"][0]["geometry"]["location"]
        return loc["lat"], loc["lng"]
    except Exception as e:
        print("Error in get_coordinates:", e)
        return None

def get_distance_duration(src, dest):
    """Google Directions API"""
    url = "https://maps.googleapis.com/maps/api/directions/json"
    params = {
        "origin": src,
        "destination": dest,
        "key": GOOGLE_MAPS_API_KEY
    }
    resp = requests.get(url, params=params).json()
    if resp['status'] != 'OK':
        return None, None
    leg = resp['routes'][0]['legs'][0]
    return leg['distance']['text'], leg['duration']['text']

@app.route("/", methods=["GET", "POST"])
def index():
    error = None
    if request.method == "POST":
        src_name = request.form.get("src")
        dest_name = request.form.get("dest")

        src_coords = get_coordinates(src_name)
        dest_coords = get_coordinates(dest_name)

        if not src_coords or not dest_coords:
            error = "One or both locations not found! Please include city + country."
            return render_template("index.html", error=error)

        distance, duration = get_distance_duration(src_name, dest_name)
        prompt = f"Provide a road safety analysis and traffic tips when traveling from {src_name} to {dest_name} in Bangalore."
        commentary = call_grok(prompt)

        return render_template(
            "map.html",
            src_name=src_name,
            dest_name=dest_name,
            src_coords=src_coords,
            dest_coords=dest_coords,
            distance=distance,
            duration=duration,
            commentary=commentary,
            google_api_key=GOOGLE_MAPS_API_KEY
        )

    return render_template("index.html", error=error)

if __name__ == "__main__":
    app.run(debug=True)
