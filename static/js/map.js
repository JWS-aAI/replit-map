let map;
let markers = [];
let routeLayer;
let userLat, userLon;
let selectedLandmark = null;

function initMap() {
    // Initialize the map
    map = L.map('map').setView([0, 0], 2);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
    }).addTo(map);

    // Try to get user's location
    if ("geolocation" in navigator) {
        navigator.geolocation.getCurrentPosition(
            function (position) {
                userLat = position.coords.latitude;
                userLon = position.coords.longitude;
                map.setView([userLat, userLon], 13);
                fetchLandmarks();
            },
            function (error) {
                console.error("Geolocation error:", error.message);
                fetchLandmarks();
            },
            {
                enableHighAccuracy: true,
                timeout: 5000,
                maximumAge: 0
            }
        );
    } else {
        fetchLandmarks();
    }

    map.on('moveend', fetchLandmarks);

    // Add event listeners to checkboxes
    document.querySelectorAll('.landmark-filter').forEach(checkbox => {
        checkbox.addEventListener('change', fetchLandmarks);
    });

    // Add event listener for search button
    document.getElementById('search-button').addEventListener('click', performSearch);

    // Add event listener for search input (Enter key)
    document.getElementById('search-input').addEventListener('keyup', function (event) {
        if (event.key === 'Enter') {
            performSearch();
        }
    });

    document.getElementById('calculate-route-button').addEventListener('click', () => {
        if (selectedLandmark && userLat && userLon) {
            calculateRoute(userLat, userLon, selectedLandmark.lat, selectedLandmark.lon);
        }
    });
}

function fetchLandmarks() {
    const bounds = map.getBounds();
    const center = bounds.getCenter();
    const radius = Math.max(
        center.distanceTo(bounds.getNorthEast()),
        center.distanceTo(bounds.getSouthWest())
    );

    // Get selected filters
    const selectedFilters = Array.from(document.querySelectorAll('.landmark-filter:checked')).map(cb => cb.value);

    fetch(`/landmarks?lat=${center.lat}&lon=${center.lng}&radius=${radius}&filters=${selectedFilters.join(',')}`)
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
    marker.bindPopup(`<b>${landmark.title}</b><br>${landmark.type}`);
    marker.on('click', () => {
        fetchLandmarkInfo(landmark.pageid);
        selectedLandmark = landmark;  // Store the clicked landmark for route calculation
        showRouteButton(landmark);
    });
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

function performSearch() {
    const searchQuery = document.getElementById('search-input').value.trim();
    if (searchQuery) {
        fetch(`/search?q=${encodeURIComponent(searchQuery)}`)
            .then(response => response.json())
            .then(result => {
                if (result.lat && result.lon) {
                    map.setView([result.lat, result.lon], 13);
                    clearMarkers();
                    fetchLandmarks();
                } else {
                    alert('Location not found. Please try a different search term.');
                }
            })
            .catch(error => {
                console.error('Error performing search:', error);
                alert('An error occurred while searching. Please try again.');
            });
    }
}

function showRouteButton(landmark) {
    document.getElementById('route-container').classList.remove('hidden');
    document.getElementById('landmark-name').textContent = landmark.title;
}

function calculateRoute(startLat, startLon, endLat, endLon) {
    fetch(`/route?start_lat=${startLat}&start_lon=${startLon}&end_lat=${endLat}&end_lon=${endLon}`)
        .then(response => response.json())
        .then(data => {
            if (routeLayer) {
                map.removeLayer(routeLayer);  // Remove the previous route if any
            }
            routeLayer = L.geoJSON(data.geometry).addTo(map);
            const bounds = routeLayer.getBounds();
            map.fitBounds(bounds);
        })
        .catch(error => console.error('Error calculating route:', error));
}

document.addEventListener('DOMContentLoaded', initMap);
