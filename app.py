import os
from flask import Flask, render_template, jsonify, request
import requests
from urllib.parse import urlparse

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/landmarks')
def get_landmarks():
    # Get coordinates from query parameters
    lat = float(request.args.get('lat'))
    lon = float(request.args.get('lon'))
    radius = float(request.args.get('radius', 10000))  # Default radius: 10km

    # Query Wikipedia API for nearby landmarks
    url = f"https://en.wikipedia.org/w/api.php?action=query&list=geosearch&gsradius={radius}&gscoord={lat}|{lon}&gslimit=50&format=json"
    response = requests.get(url)
    data = response.json()

    landmarks = []
    for place in data['query']['geosearch']:
        landmarks.append({
            'pageid': place['pageid'],
            'title': place['title'],
            'lat': place['lat'],
            'lon': place['lon'],
        })

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

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
