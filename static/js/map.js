let map;
let markers = [];

function initMap() {
    // Initialize the map with a default view
    map = L.map('map').setView([0, 0], 2);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
    }).addTo(map);

    // Try to get user's location
    if ("geolocation" in navigator) {
        navigator.geolocation.getCurrentPosition(
            function(position) {
                // Success callback
                const userLat = position.coords.latitude;
                const userLon = position.coords.longitude;
                map.setView([userLat, userLon], 13);
                console.log("User location detected:", userLat, userLon);
                fetchLandmarks();
            },
            function(error) {
                // Error callback
                console.error("Geolocation error:", error.message);
                // If geolocation fails, we'll keep the default view and fetch landmarks
                fetchLandmarks();
            },
            {
                enableHighAccuracy: true,
                timeout: 5000,
                maximumAge: 0
            }
        );
    } else {
        console.log("Geolocation is not supported by this browser.");
        // If geolocation is not supported, we'll keep the default view and fetch landmarks
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
    document.getElementById('search-input').addEventListener('keyup', function(event) {
        if (event.key === 'Enter') {
            performSearch();
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
    marker.bindPopup(`<b>${landmark.title}</b><br>${landmark.type}`);
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
            document.getElementById('landmark-title').textContent = info.title;
            document.getElementById('landmark-description').textContent = info.extract;
            document.getElementById('landmark-info').classList.remove('hidden');
        })
        .catch(error => console.error('Error fetching landmark info:', error));
}

function performSearch() {
    const searchQuery = document.getElementById('search-input').value.trim();
    if (searchQuery) {
        console.log('Performing search for:', searchQuery);
        fetch(`/search?q=${encodeURIComponent(searchQuery)}`)
            .then(response => response.json())
            .then(result => {
                console.log('Search result:', result);
                if (result.lat && result.lon) {
                    map.setView([result.lat, result.lon], 13);
                    clearMarkers(); // Clear existing markers before fetching new ones
                    fetchLandmarks(); // Fetch landmarks for the new location
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

document.addEventListener('DOMContentLoaded', initMap);
