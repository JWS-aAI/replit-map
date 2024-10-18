import os
from flask import Flask, render_template, jsonify, request
from flask_socketio import SocketIO, emit
# from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
import logging
from flask_caching import Cache
import time

import requests
from urllib.parse import quote_plus

from app.langchain import call_agent

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

# Load environment variables
load_dotenv()

# Initialize Flask-SocketIO
app = Flask(__name__)
socketio = SocketIO(app)

# Initialize OpenAI LLM
# llm = ChatOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Configure caching
cache = Cache(app, config={'CACHE_TYPE': 'SimpleCache'})

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/landmarks')
def get_landmarks():
    # Get coordinates from query parameters
    lat = float(request.args.get('lat'))
    lon = float(request.args.get('lon'))
    radius = int(float(request.args.get('radius', 10000)))  # Default radius: 10km, converted to integer
    filters = request.args.get('filters', '').split(',')

    # Create a cache key that includes lat, lon, and radius
    cache_key = f"landmarks_{lat}_{lon}_{radius}"

    # Check if we have cached data for this key
    cached_data = cache.get(cache_key)
    if cached_data:
        timestamp, landmarks = cached_data
        # Check if the cached data is less than 5 minutes old
        if time.time() - timestamp < 300:
            return jsonify(landmarks)

    # If no cached data or it's expired, fetch new data
    url = f"https://en.wikipedia.org/w/api.php?action=query&list=geosearch&gsradius={radius}&gscoord={lat}|{lon}&gslimit=50&format=json"
    logging.debug(f'Wikipedia API request URL: {url}')
    
    response = requests.get(url)
    data = response.json()
    
    logging.debug(f'Wikipedia API response: {data}')
    
    landmarks = []
    if 'query' in data and 'geosearch' in data['query']:
        for place in data['query']['geosearch']:
            landmark_type = classify_landmark(place['title'])
            if not filters or landmark_type in filters:
                landmarks.append({
                    'pageid': place['pageid'],
                    'title': place['title'],
                    'lat': place['lat'],
                    'lon': place['lon'],
                    'type': landmark_type
                })
    else:
        logging.error(f'Unexpected API response format: {data}')
    
    # Cache the new data with the current timestamp
    cache.set(cache_key, (time.time(), landmarks))
    
    return jsonify(landmarks)

@app.route('/landmark/<int:pageid>')
@cache.memoize(timeout=3600)  # Cache for 1 hour
def get_landmark_info(pageid):
    # Query Wikipedia API for landmark details
    url = f"https://en.wikipedia.org/w/api.php?action=query&pageids={pageid}&prop=extracts&exintro&format=json&explaintext"
    response = requests.get(url)
    data = response.json()

    page = data['query']['pages'][str(pageid)]
    extract = page.get('extract', 'No information available.')

    return jsonify({
        'title': page['title'],
        'extract': extract[:200] + '...' if len(extract) > 200 else extract
    })

@app.route('/search')
# Removed @cache.memoize decorator to ensure fresh results for each search
def search():
    query = request.args.get('q', '')
    logging.info(f"Received search query: {query}")
    
    if not query:
        logging.warning("No search query provided")
        return jsonify({'error': 'No search query provided'}), 400

    # Use Nominatim API for geocoding
    encoded_query = quote_plus(query)
    url = f"https://nominatim.openstreetmap.org/search?q={encoded_query}&format=json&limit=1"
    headers = {'User-Agent': 'LocalLandmarksApp/1.0'}
    
    try:
        logging.info(f"Sending request to Nominatim API: {url}")
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        
        logging.info(f"Received response from Nominatim API: {data}")
        
        if data:
            result = data[0]
            logging.info(f"Search result: {result}")
            return jsonify({
                'lat': float(result['lat']),
                'lon': float(result['lon']),
                'display_name': result['display_name']
            })
        else:
            logging.warning(f"Location not found for query: {query}")
            return jsonify({'error': 'Location not found'}), 404
    except requests.RequestException as e:
        logging.error(f"Error during geocoding request: {str(e)}")
        return jsonify({'error': 'An error occurred during the search'}), 500

def classify_landmark(title):
    # This is a simple classification based on keywords
    # In a real-world scenario, you might want to use a more sophisticated method
    title = title.lower()
    if any(word in title for word in ['museum', 'castle', 'monument', 'memorial', 'church', 'cathedral']):
        return 'historical'
    elif any(word in title for word in ['park', 'mountain', 'lake', 'river', 'forest']):
        return 'natural'
    else:
        return 'cultural'

# New SocketIO event for chatbot
@socketio.on('send_message')
def handle_send_message(data):
    print("test")

    user_message = data.get('message')
    # Process the message with LangChain
    response = call_agent(user_message)
    # response = llm(user_message).content  # Extract the text content from AIMessage
    emit('receive_message', {'message': response})

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000)