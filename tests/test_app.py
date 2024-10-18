import pytest
from flask import Flask
import sys
sys.path.insert(0, '')  # Ensure the current directory is in PYTHONPATH
from app import app as flask_app

@pytest.fixture
def client():
    flask_app.config['TESTING'] = True
    with flask_app.test_client() as client:
        yield client

def test_get_landmarks(client):
    response = client.get('/landmarks?lat=51.5074&lon=-0.1278&radius=10000')
    assert response.status_code == 200
    assert isinstance(response.json, list)

def test_get_landmark_info(client):
    response = client.get('/landmark/21721040')  # Example PageID
    assert response.status_code == 200
    assert 'title' in response.json
    assert 'extract' in response.json

def test_search(client):
    response = client.get('/search?q=Eiffel Tower')
    assert response.status_code in [200, 404, 400]
    if response.status_code == 200:
        assert 'lat' in response.json
        assert 'lon' in response.json

def test_search_no_query(client):
    response = client.get('/search?q=')
    assert response.status_code == 400

