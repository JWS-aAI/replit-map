import pytest
from app import app

@pytest.fixture
def client():
    with app.test_client() as client:
        yield client

def test_landmarks_route(client):
    response = client.get('/landmarks?lat=0&lon=0&radius=10000')
    assert response.status_code == 200
    assert isinstance(response.json, list)

def test_search_route(client):
    response = client.get('/search?q=Eiffel Tower')
    assert response.status_code == 200
    assert 'lat' in response.json
    assert 'lon' in response.json

def test_route_to_landmark(client):
    # Assuming the route endpoint is /route and it returns a JSON response
    response = client.get('/route?start_lat=48.858844&start_lon=2.294351&end_lat=48.858844&end_lon=2.294351')
    assert response.status_code == 200
    # Check if the response contains a valid route (this is a placeholder check)
    assert 'geometry' in response.json
