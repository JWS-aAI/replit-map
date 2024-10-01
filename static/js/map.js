let map;
let markers = [];

function initMap() {
    map = L.map('map').setView([0, 0], 2);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
    }).addTo(map);

    map.on('moveend', fetchLandmarks);

    // Try to get user's location
    if ("geolocation" in navigator) {
        navigator.geolocation.getCurrentPosition(function(position) {
            map.setView([position.coords.latitude, position.coords.longitude], 13);
        }, function(error) {
            console.error("Error: " + error.message);
        });
    }
}

function fetchLandmarks() {
    const bounds = map.getBounds();
    const center = bounds.getCenter();
    const radius = Math.max(
        center.distanceTo(bounds.getNorthEast()),
        center.distanceTo(bounds.getSouthWest())
    );

    fetch(`/landmarks?lat=${center.lat}&lon=${center.lng}&radius=${radius}`)
        .then(response => response.json())
        .then(landmarks => {
            clearMarkers();
            landmarks.forEach(addMarker);
        })
        .catch(error => console.error('Error fetching landmarks:', error));
}

function clearMarkers() {
    markers.forEach(marker => map.removeLayer(marker));
    markers = [];
}

function addMarker(landmark) {
    const marker = L.marker([landmark.lat, landmark.lon]).addTo(map);
    marker.on('click', () => fetchLandmarkInfo(landmark.pageid));
    markers.push(marker);
}

function fetchLandmarkInfo(pageid) {
    fetch(`/landmark/${pageid}`)
        .then(response => response.json())
        .then(info => {
            document.getElementById('landmark-title').textContent = info.title;
            document.getElementById('landmark-description').textContent = info.extract;
            document.getElementById('landmark-info').classList.remove('hidden');
        })
        .catch(error => console.error('Error fetching landmark info:', error));
}

document.addEventListener('DOMContentLoaded', initMap);
