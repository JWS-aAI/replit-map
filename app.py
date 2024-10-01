import os
from flask import Flask, render_template, jsonify, request
import requests
from urllib.parse import urlparse
import logging

logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__)

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

    # Query Wikipedia API for nearby landmarks
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
    
    return jsonify(landmarks)

@app.route('/landmark/<int:pageid>')
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

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
