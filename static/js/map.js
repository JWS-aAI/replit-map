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
            console.log('Landmarks received:', landmarks);
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
    marker.on('click', () => {
        console.log('Marker clicked:', landmark);
        fetchLandmarkInfo(landmark.pageid);
    });
    markers.push(marker);
}

function fetchLandmarkInfo(pageid) {
    console.log('Fetching landmark info for pageid:', pageid);
    fetch(`/landmark/${pageid}`)
        .then(response => response.json())
        .then(info => {
            console.log('Landmark info received:', info);
            const infoElement = document.getElementById('landmark-info');
            const titleElement = document.getElementById('landmark-title');
            const descriptionElement = document.getElementById('landmark-description');
            
            if (infoElement && titleElement && descriptionElement) {
                titleElement.textContent = info.title;
                descriptionElement.textContent = info.extract;
                infoElement.classList.remove('hidden');
                // Ensure the info is in view
                infoElement.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
            } else {
                console.error('One or more DOM elements not found');
            }
        })
        .catch(error => console.error('Error fetching landmark info:', error));
}

document.addEventListener('DOMContentLoaded', initMap);

// Add click event listener to the map container
document.addEventListener('DOMContentLoaded', () => {
    initMap();
    
    const mapContainer = document.getElementById('map');
    mapContainer.addEventListener('click', (event) => {
        console.log('Map container clicked', event);
    });
});
