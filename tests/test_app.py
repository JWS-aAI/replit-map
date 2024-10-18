import pytest
from app import app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_get_landmarks(client):
    response = client.get('/landmarks?lat=40.7128&lon=-74.0060&radius=10000')
    assert response.status_code == 200
    assert isinstance(response.json, list)

def test_get_landmark_info(client):
    # Assuming a valid pageid for testing
    response = client.get('/landmark/12345')
    assert response.status_code == 200
    assert 'title' in response.json
    assert 'extract' in response.json

def test_search(client):
    response = client.get('/search?q=New York')
    assert response.status_code in [200, 404]  # Can be 404 if location not found
    if response.status_code == 200:
        assert 'lat' in response.json
        assert 'lon' in response.json
