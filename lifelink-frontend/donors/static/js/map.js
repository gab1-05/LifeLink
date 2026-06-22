console.log('map.js loading...');

let map, donorLayer, requestLayer, hospitalLayer, userLayer, currentFilter = 'all';
let donorData = [], requestData = [], hospitalData = [];
let myMarker = null, myRadiusCircle = null;
let currentLat = null, currentLng = null;
let fallbackMode = false;

const DEFAULT_CENTER = [19.0760, 72.8777];
const DEFAULT_ZOOM = 11;
const BT_LABEL = {
    A_POSITIVE: 'A+',
    A_NEGATIVE: 'A-',
    B_POSITIVE: 'B+',
    B_NEGATIVE: 'B-',
    AB_POSITIVE: 'AB+',
    AB_NEGATIVE: 'AB-',
    O_POSITIVE: 'O+',
    O_NEGATIVE: 'O-'
};

function getCsrfToken() {
    const match = document.cookie.match(/csrftoken=([^;]+)/);
    return match ? match[1] : '';
}

function showToast(title, message, type) {
    console.log('[' + type + '] ' + title + ': ' + message);
}

function api(url, method, body) {
    method = method || 'GET';

    let parts = url.trim().split('?');
    let base = parts[0];
    let query = parts.length > 1 ? '?' + parts.slice(1).join('?') : '';

    if (!base.startsWith('/api/')) {
        base = '/api/' + base.replace(/^\/+/, '');
    }

    if (!base.endsWith('/') && !query) {
        base += '/';
    }
    if (!base.endsWith('/') && query) {
        base += '/';
    }

    const opts = {
        method: method,
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCsrfToken()
        },
        credentials: 'same-origin'
    };

    if (body) {
        opts.body = JSON.stringify(body);
    }

    return fetch(base + query, opts)
        .then(r => r.json())
        .catch(e => {
            console.error(e);
            return [];
        });
}

function initMap() {
    console.log('initMap called');
    const mapEl = document.getElementById('map');
    if (!mapEl) {
        console.warn('#map element not found');
        return;
    }

    if (typeof L === 'undefined') {
        console.warn('Leaflet not loaded');
        fallbackMode = true;
        return;
    }

    try {
        map = L.map('map').setView(DEFAULT_CENTER, DEFAULT_ZOOM);

        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            maxZoom: 19,
            attribution: '&copy; OpenStreetMap'
        }).addTo(map);

        donorLayer = L.layerGroup().addTo(map);
        requestLayer = L.layerGroup().addTo(map);
        
        if (typeof L.markerClusterGroup !== 'undefined') {
            hospitalLayer = L.markerClusterGroup({ disableClusteringAtZoom: 14 }).addTo(map);
        } else {
            hospitalLayer = L.layerGroup().addTo(map);
        }

        // User layer added last to always appear on top
        userLayer = L.layerGroup().addTo(map);

        // Ensure proper sizing after load
        setTimeout(() => {
            map.invalidateSize();
            // Load hospitals immediately when map is ready
            loadHospitalsInView();
        }, 500);

        locateUser();
        
        map.on('moveend', debounce(loadHospitalsInView, 500));
        map.on('zoomend', debounce(loadHospitalsInView, 500));
    } catch (e) {
        console.error('Map init error:', e);
        fallbackMode = true;
    }
}

function debounce(fn, wait) {
    let t;
    return (...args) => {
        clearTimeout(t);
        t = setTimeout(() => fn(...args), wait);
    };
}

async function loadHospitalsInView() {
    if (!map || fallbackMode) return;
    const bounds = map.getBounds();
    const south = bounds.getSouth();
    const west = bounds.getWest();
    const north = bounds.getNorth();
    const east = bounds.getEast();
    
    console.log(`[HospitalLoader] Fetching hospitals in bounds: S=${south.toFixed(4)} W=${west.toFixed(4)} N=${north.toFixed(4)} E=${east.toFixed(4)}`);
    
    try {
        const url = `/api/hospitals-in-view/?south=${south}&west=${west}&north=${north}&east=${east}`;
        const response = await fetch(url, { credentials: 'same-origin' });
        hospitalData = await response.json();
        console.log(`[HospitalLoader] Got ${Array.isArray(hospitalData) ? hospitalData.length : 'ERROR'} hospitals`, hospitalData);
        if (Array.isArray(hospitalData)) {
            renderHospitals();
        }
    } catch (e) {
        console.error('[HospitalLoader] Failed to load viewport hospitals', e);
    }
}

function renderHospitals() {
    if (!map || !hospitalLayer) return;
    hospitalLayer.clearLayers();
    hospitalData.forEach(h => {
        if (!h.latitude || !h.longitude) return;
        const popupHtml = `
            <div class="marker-popup hospital-popup">
                <strong>🏥 ${h.name || 'Hospital'}</strong><br>
                ${h.address ? `<span>📍 ${h.address}</span><br>` : ''}
                <div class="popup-buttons">
                    <button class="popup-btn popup-btn-primary" onclick="requestBloodAtHospital('${(h.name||'').replace(/'/g, "\\'")}', '${(h.address||'').replace(/'/g, "\\'")}', ${h.latitude}, ${h.longitude})">Request Blood Here</button>
                </div>
            </div>
        `;
        L.marker([parseFloat(h.latitude), parseFloat(h.longitude)], {
            icon: L.divIcon({html:'<div style="width:30px;height:30px;border-radius:10px;background:#2979FF;color:#fff;display:flex;align-items:center;justify-content:center;">🏥</div>',iconSize:[30,30],iconAnchor:[15,15]})
        }).bindPopup(popupHtml).addTo(hospitalLayer);
    });
}

function requestBloodAtHospital(name, address, lat, lng) {
    window.location.href = `/dashboard/?request_modal=1&hosp_name=${encodeURIComponent(name)}&hosp_addr=${encodeURIComponent(address)}&lat=${lat}&lng=${lng}`;
}

function toggleLayer(layerName, element) {
    let targetLayer;
    if (layerName === 'donor') targetLayer = donorLayer;
    else if (layerName === 'request') targetLayer = requestLayer;
    else if (layerName === 'hospital') targetLayer = hospitalLayer;

    if (!targetLayer || !map) return;
    
    const isDonorVisible = map.hasLayer(donorLayer);
    const isRequestVisible = map.hasLayer(requestLayer);
    const isHospitalVisible = map.hasLayer(hospitalLayer);
    
    // Check if only the target layer is currently visible
    const onlyTargetVisible = map.hasLayer(targetLayer) && 
        ((targetLayer === donorLayer) ? (!isRequestVisible && !isHospitalVisible) : 
         (targetLayer === requestLayer) ? (!isDonorVisible && !isHospitalVisible) : 
         (!isDonorVisible && !isRequestVisible));
         
    // Reset all interactive legend items to 0.5 opacity
    document.querySelectorAll('.map-legend .legend-item').forEach(el => {
        if (el.getAttribute('onclick')) el.style.opacity = '0.5';
    });

    if (onlyTargetVisible) {
        // Restore all layers if clicked again
        map.addLayer(donorLayer);
        map.addLayer(requestLayer);
        map.addLayer(hospitalLayer);
        document.querySelectorAll('.map-legend .legend-item').forEach(el => {
            if (el.getAttribute('onclick')) el.style.opacity = '1';
        });
    } else {
        // Show only the target layer
        if (map.hasLayer(donorLayer)) map.removeLayer(donorLayer);
        if (map.hasLayer(requestLayer)) map.removeLayer(requestLayer);
        if (map.hasLayer(hospitalLayer)) map.removeLayer(hospitalLayer);
        
        map.addLayer(targetLayer);
        
        // Highlight just the associated legend items
        document.querySelectorAll(`.map-legend .legend-item[onclick*='${layerName}']`).forEach(el => {
            el.style.opacity = '1';
        });
    }
}

function locateUser() {
    if (!navigator.geolocation) {
        console.warn('Geolocation not available, loading data without user position');
        loadData();
        return;
    }

    navigator.geolocation.getCurrentPosition(
        pos => {
            currentLat = pos.coords.latitude;
            currentLng = pos.coords.longitude;
            if (map) {
                map.setView([currentLat, currentLng], 11);
                renderUserLocation();
            }
            loadData();
        },
        err => {
            console.log('Location denied or error', err);
            loadData();
        },
        {
            enableHighAccuracy: true,
            timeout: 10000,
            maximumAge: 60000
        }
    );
}

function renderUserLocation() {
    if (!map || currentLat == null || currentLng == null) return;

    if (myMarker) {
        userLayer.removeLayer(myMarker);
    }
    if (myRadiusCircle) {
        userLayer.removeLayer(myRadiusCircle);
    }

    myMarker = L.marker([currentLat, currentLng], {
        icon: L.divIcon({
            html: '<div class="user-location-marker" style="width:50px;height:50px;border-radius:50%;background:linear-gradient(135deg, #4A90E2 0%, #357ABD 100%);color:#fff;display:flex;align-items:center;justify-content:center;font-weight:800;font-size:24px;border:4px solid white;box-shadow:0 0 0 3px #4A90E2, 0 0 20px rgba(74, 144, 226, 0.6), inset 0 0 10px rgba(255, 255, 255, 0.3);position:relative;animation:pulse-ring 2s infinite;">' +
                '<span style="position:absolute;width:14px;height:14px;background:white;border-radius:50%;top:50%;left:50%;transform:translate(-50%, -50%);box-shadow:0 0 8px rgba(255, 255, 255, 0.8);"></span>' +
                '<span style="position:absolute;width:6px;height:6px;background:#357ABD;border-radius:50%;top:50%;left:50%;transform:translate(-50%, -50%);"></span>' +
                '</div>',
            iconSize: [50, 50],
            iconAnchor: [25, 25],
            popupAnchor: [0, -25],
            className: 'user-location-icon',
            zIndexOffset: 1000
        })
    })
    .bindPopup('<div class="user-location-popup"><strong>📍 Your Location</strong><br><span style="font-size:12px;color:#666;">Lat: ' + currentLat.toFixed(4) + '<br>Lng: ' + currentLng.toFixed(4) + '</span></div>', {
        maxWidth: 250,
        className: 'user-location-popup-container'
    })
    .addTo(userLayer);

    // Add a pulsing circle around user location
    myRadiusCircle = L.circle([currentLat, currentLng], {
        color: '#4A90E2',
        fillColor: '#4A90E2',
        fillOpacity: 0.08,
        weight: 2.5,
        radius: 150,
        dashArray: '8, 4',
        className: 'user-radius-circle'
    }).addTo(userLayer);
}

function loadData() {
    console.log('loadData called');
    const radius = document.getElementById('radius-filter')?.value || 50;
    const btFilter = document.getElementById('bt-filter')?.value || '';

    let q = '';

    if (currentLat != null && currentLng != null && currentFilter !== 'all') {
        q = '?lat=' + currentLat + '&lng=' + currentLng + '&radius=' + radius;
    }

    if (btFilter) {
        q += (q ? '&' : '?') + 'bloodType=' + btFilter;
    }

    Promise.allSettled([
        (currentFilter === 'all' || currentFilter === 'donors') ? api('users/donors' + q) : Promise.resolve([]),
        (currentFilter === 'all' || currentFilter === 'requests') ? api('requests' + q) : Promise.resolve([])
    ]).then(results => {
        donorData = results[0].status === 'fulfilled' ? results[0].value : [];
        requestData = results[1].status === 'fulfilled' ? results[1].value : [];

        if (map && !fallbackMode) {
            renderLeafletData();
        }
    });

    if (currentFilter === 'all' || currentFilter === 'hospitals') {
        loadHospitalsInView();
    }
}

function renderLeafletData() {
    if (!map) return;

    donorLayer.clearLayers();
    requestLayer.clearLayers();

    donorData.forEach(d => {
        if (!d.latitude || !d.longitude) return;

        const lat = parseFloat(d.latitude);
        const lng = parseFloat(d.longitude);
        if (Number.isNaN(lat) || Number.isNaN(lng)) return;

        L.marker([lat, lng], {
            icon: L.divIcon({
                html: '<div style="width:30px;height:30px;border-radius:50%;background:#DC143C;color:#fff;display:flex;align-items:center;justify-content:center;font-weight:700;">'
                    + (BT_LABEL[d.bloodType] || '?')
                    + '</div>',
                iconSize: [30, 30],
                iconAnchor: [15, 15]
            })
        })
        .bindPopup(createDonorPopup(d), { maxWidth: 300, maxHeight: 400 })
        .addTo(donorLayer);
    });

    requestData.forEach(r => {
        if (!r.latitude || !r.longitude) return;

        const lat = parseFloat(r.latitude);
        const lng = parseFloat(r.longitude);
        if (Number.isNaN(lat) || Number.isNaN(lng)) return;

        const c = (r.urgency === 'CRITICAL'
            ? '#FF3358'
            : r.urgency === 'URGENT'
                ? '#FFB700'
                : '#00E676');

        L.marker([lat, lng], {
            icon: L.divIcon({
                html: '<div style="width:35px;height:35px;border-radius:10px;background:' + c + ';color:#000;display:flex;align-items:center;justify-content:center;font-weight:800;">🆘</div>',
                iconSize: [35, 35],
                iconAnchor: [17, 17]
            })
        })
        .bindPopup(createRequestPopup(r), { maxWidth: 300, maxHeight: 400 })
        .addTo(requestLayer);
    });

}

function setFilter(f, btn) {
    currentFilter = f;
    document.querySelectorAll('.map-controls button.filter-btn').forEach(b => {
        b.classList.remove('active');
    });
    if (btn) {
        btn.classList.add('active');
    }
    loadData();
}

// Simple helpers
function applyBloodFilter() {
    loadData();
}

function reloadData() {
    loadData();
}

function centerOnMe() {
    if (map && currentLat != null && currentLng != null) {
        // Smooth pan and zoom to user location
        map.flyTo([currentLat, currentLng], 14, {
            duration: 1.5,
            easeLinearity: 0.25
        });
        
        // Ensure user marker is rendered and visible
        renderUserLocation();
        
        // Show toast notification
        showToast('📍 Centered', 'Your location is now centered', 'info');
    }
}

function openChatWith(userId, name) {
    window.location = '/messages/?to=' + userId + '&name=' + encodeURIComponent(name);
}

function respondToRequest(id) {
    api('requests/' + id + '/respond', 'PATCH')
        .then(r => {
            if (r.message) {
                showToast('Response!', r.message, 'success');
                loadData();
            }
        });
}

function openInGoogleMaps(lat, lng, name) {
    const url = 'https://www.google.com/maps?q=' + lat + ',' + lng + '&z=15';
    window.open(url, '_blank');
}

function createDonorPopup(donor) {
    const btLabel = BT_LABEL[donor.bloodType] || 'Unknown';
    const googleMapsBtn = '<button class="popup-btn popup-btn-map" onclick="openInGoogleMaps(' + donor.latitude + ', ' + donor.longitude + ', \'' + (donor.fullName || 'Donor').replace(/'/g, "\\'") + '\')">📍 Google Maps</button>';
    const messageBtn = '<button class="popup-btn popup-btn-message" onclick="openChatWith(' + donor.id + ', \'' + (donor.fullName || 'Donor').replace(/'/g, "\\'") + '\')">💬 Message</button>';
    const donateBtn = '<button class="popup-btn popup-btn-donate" onclick="initiateDonation(' + donor.id + ', \'' + (donor.fullName || 'Donor').replace(/'/g, "\\'") + '\')">🤝 Donate Blood</button>';
    
    return '<div class="marker-popup">' +
        '<strong>' + (donor.fullName || 'Donor') + '</strong><br>' +
        '<span class="blood-type">🩸 Blood Type: ' + btLabel + '</span><br>' +
        (donor.phone ? '<span>📱 ' + donor.phone + '</span><br>' : '') +
        (donor.address ? '<span>📍 ' + donor.address + '</span><br>' : '') +
        (donor.lastDonated ? '<span>📅 Last Donated: ' + donor.lastDonated + '</span><br>' : '') +
        '<div class="popup-buttons">' +
        googleMapsBtn + messageBtn + donateBtn +
        '</div></div>';
}

function initiateDonation(donorId, donorName) {
    showToast('Donation Request', 'Opening donation interface with ' + donorName, 'info');
    openChatWith(donorId, donorName);
}



function createRequestPopup(request) {
    const btLabel = BT_LABEL[request.bloodType] || 'Unknown';
    const requesterId = request.patient && request.patient.id ? request.patient.id : null;
    const requesterName = request.patient && request.patient.fullName ? request.patient.fullName : 'Requester';
    const urgencyIcon = request.urgency === 'CRITICAL' ? '!' : request.urgency === 'URGENT' ? 'Urgent' : 'Open';
    const safeName = requesterName.replace(/'/g, "\\'");
    const googleMapsBtn = '<button class="popup-btn popup-btn-map" onclick="openInGoogleMaps(' + request.latitude + ', ' + request.longitude + ', \'' + safeName + '\')">Google Maps</button>';
    const respondBtn = '<button class="popup-btn popup-btn-respond" onclick="respondToRequest(' + request.id + ')">Respond</button>';
    const messageBtn = requesterId ? '<button class="popup-btn popup-btn-message" onclick="openChatWith(' + requesterId + ', \'' + safeName + '\')">Contact</button>' : '';

    return '<div class="marker-popup request-popup">' +
        '<strong>' + urgencyIcon + ' ' + requesterName + '</strong><br>' +
        '<span class="urgency-' + String(request.urgency || '').toLowerCase() + '">Status: ' + (request.urgency || 'OPEN') + '</span><br>' +
        '<span class="blood-type">Blood Type: ' + btLabel + '</span><br>' +
        '<span>Requested: ' + (request.unitsNeeded || '1') + ' units</span><br>' +
        (request.hospitalName ? '<span>Hospital: ' + request.hospitalName + '</span><br>' : '') +
        '<div class="popup-buttons">' + googleMapsBtn + respondBtn + messageBtn + '</div></div>';
}

function createHospitalPopup(hospital) {
    const hospitalName = hospital.name || hospital.hospitalName || 'Hospital';
    const safeName = hospitalName.replace(/'/g, "\\'");
    const googleMapsBtn = '<button class="popup-btn popup-btn-map" onclick="openInGoogleMaps(' + hospital.latitude + ', ' + hospital.longitude + ', \'' + safeName + '\')">Google Maps</button>';
    const messageBtn = '<button class="popup-btn popup-btn-message" onclick="openChatWith(' + hospital.id + ', \'' + safeName + '\')">Message Hospital</button>';

    return '<div class="marker-popup hospital-popup">' +
        '<strong>' + hospitalName + '</strong><br>' +
        (hospital.address ? '<span>' + hospital.address + '</span><br>' : '') +
        (hospital.phone ? '<span>' + hospital.phone + '</span><br>' : '') +
        '<div class="popup-buttons">' + googleMapsBtn + messageBtn + '</div></div>';
}

// Only one set of listeners
window.addEventListener('load', initMap);
setInterval(loadData, 30000);

console.log('map.js loaded completely');
