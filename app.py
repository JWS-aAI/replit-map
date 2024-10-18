from flask import Flask, render_template, jsonify, request, Response
import requests
from urllib.parse import quote_plus
import logging
from flask_caching import Cache
import time

logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s"
)

app = Flask(__name__)

# Configure caching
cache = Cache(app, config={"CACHE_TYPE": "SimpleCache"})


@app.route("/")
def index() -> str:
    return render_template("index.html")


@app.route("/landmarks")
def get_landmarks() -> Response:
    # Get coordinates from query parameters
    lat: float = float(request.args.get("lat"))
    lon: float = float(request.args.get("lon"))
    radius: int = int(
        float(request.args.get("radius", 10000))
    )  # Default radius: 10km, converted to integer
    filters: list[str] = request.args.get("filters", "").split(",")

    # Create a cache key that includes lat, lon, and radius
    cache_key: str = f"landmarks_{lat}_{lon}_{radius}"

    # Check if we have cached data for this key
    cached_data: tuple[float, list[dict[str, str]]] | None = cache.get(cache_key)
    if cached_data:
        timestamp, landmarks = cached_data
        # Check if the cached data is less than 5 minutes old
        if time.time() - timestamp < 300:
            return jsonify(landmarks)

    # If no cached data or it's expired, fetch new data
    url: str = f"https://en.wikipedia.org/w/api.php?action=query&list=geosearch&gsradius={radius}&gscoord={lat}|{lon}&gslimit=50&format=json"
    logging.debug(f"Wikipedia API request URL: {url}")

    response = requests.get(url)
    data: dict = response.json()

    logging.debug(f"Wikipedia API response: {data}")

    landmarks: list[dict[str, str]] = []
    if "query" in data and "geosearch" in data["query"]:
        for place in data["query"]["geosearch"]:
            landmark_type: str = classify_landmark(place["title"])
            if not filters or landmark_type in filters:
                landmarks.append(
                    {
                        "pageid": str(place["pageid"]),
                        "title": place["title"],
                        "lat": str(place["lat"]),
                        "lon": str(place["lon"]),
                        "type": landmark_type,
                    }
                )
    else:
        logging.error(f"Unexpected API response format: {data}")

    # Cache the new data with the current timestamp
    cache.set(cache_key, (time.time(), landmarks))

    return jsonify(landmarks)


@app.route("/landmark/<int:pageid>")
@cache.memoize(timeout=3600)  # Cache for 1 hour
def get_landmark_info(pageid: int) -> Response:
    # Query Wikipedia API for landmark details
    url: str = f"https://en.wikipedia.org/w/api.php?action=query&pageids={pageid}&prop=extracts&exintro&format=json&explaintext"
    response = requests.get(url)
    data: dict = response.json()

    page: dict = data["query"]["pages"][str(pageid)]
    extract: str = page.get("extract", "No information available.")

    return jsonify(
        {
            "title": page["title"],
            "extract": extract[:200] + "..." if len(extract) > 200 else extract,
        }
    )


@app.route("/search")
def search() -> Response:
    query: str = request.args.get("q", "")
    logging.info(f"Received search query: {query}")

    if not query:
        logging.warning("No search query provided")
        return jsonify({"error": "No search query provided"}), 400

    # Use Nominatim API for geocoding
    encoded_query: str = quote_plus(query)
    url: str = f"https://nominatim.openstreetmap.org/search?q={encoded_query}&format=json&limit=1"
    headers: dict[str, str] = {"User-Agent": "LocalLandmarksApp/1.0"}

    try:
        logging.info(f"Sending request to Nominatim API: {url}")
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data: list[dict[str, str]] = response.json()

        logging.info(f"Received response from Nominatim API: {data}")

        if data:
            result: dict[str, str] = data[0]
            logging.info(f"Search result: {result}")
            return jsonify(
                {
                    "lat": float(result["lat"]),
                    "lon": float(result["lon"]),
                    "display_name": result["display_name"],
                }
            )
        else:
            logging.warning(f"Location not found for query: {query}")
            return jsonify({"error": "Location not found"}), 404
    except requests.RequestException as e:
        logging.error(f"Error during geocoding request: {str(e)}")
        return jsonify({"error": "An error occurred during the search"}), 500


def classify_landmark(title: str) -> str:
    # This is a simple classification based on keywords
    # In a real-world scenario, you might want to use a more sophisticated method
    title = title.lower()
    if any(
        word in title
        for word in ["museum", "castle", "monument", "memorial", "church", "cathedral"]
    ):
        return "historical"
    elif any(word in title for word in ["park", "mountain", "lake", "river", "forest"]):
        return "natural"
    else:
        return "cultural"


@app.route("/route")
def get_route():
    start_lat = float(request.args.get("start_lat"))
    start_lon = float(request.args.get("start_lon"))
    end_lat = float(request.args.get("end_lat"))
    end_lon = float(request.args.get("end_lon"))

    osrm_url = f"http://router.project-osrm.org/route/v1/driving/{start_lat},{start_lon};{end_lat},{end_lon}?overview=full&geometries=geojson"
    logging.info(f"OSRM route API request: {osrm_url}")

    try:
        response = requests.get(osrm_url)
        response.raise_for_status()
        route_data = response.json()
        route_geometry = route_data["routes"][0]["geometry"]
        return jsonify({"geometry": route_geometry})
    except requests.RequestException as e:
        logging.error(f"Error fetching route: {e}")
        return jsonify({"error": "An error occurred while fetching the route"}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001)
