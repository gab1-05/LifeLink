console.log('map.js loading...');
let map, donorLayer, requestLayer, hospitalLayer, currentFilter = 'all';
let donorData = [], requestData = [], hospitalData = [];
let currentLat = null, currentLng = null, myMarker = null, myRadiusCircle = null;
let fallbackMode = false;

const DEFAULT_CENTER = [19.0760, 72.8777];
const DEFAULT_ZOOM = 11;
const BT_LABEL = {A_POSITIVE:'A+',A_NEGATIVE:'A-',B_POSITIVE:'B+',B_NEGATIVE:'B-',AB_POSITIVE:'AB+',AB_NEGATIVE:'AB-',O_POSITIVE:'O+',O_NEGATIVE:'O-'};

function getCsrfToken(){const match=document.cookie.match(/csrftoken=([^;]+)/);return match?match[1]:'';}
function showToast(title, message, type){console.log('['+type+'] '+title+': '+message);}
function api(url, method, body) {
    method = method || 'GET';
    let parts = url.trim().split('?');
    let base = parts[0];
    let query = parts.length > 1 ? '?' + parts.slice(1).join('?') : '';
    if (!base.startsWith('/api/')) base = '/api/' + base.replace(/^\\/+/, '');
    if (!base.endsWith('/') && !query) base += '/';
    if (!base.endsWith('/') && query) base += '/';
    let opts = {method:method,headers:{'Content-Type':'application/json','X-CSRFToken':getCsrfToken()},credentials:'same-origin'};
    if (body) opts.body = JSON.stringify(body);
    return fetch(base + query, opts).then(r => r.json()).catch(e => {console.error(e);return [];});
}

function initMap() {
    console.log('initMap called');
    const mapEl = document.getElementById('map');
    if (!mapEl) return;
    if (typeof L === 'undefined') {
        console.warn('Leaflet not loaded');
        fallbackMode = true;
        return;
    }
    try {
        map = L.map('map').setView(DEFAULT_CENTER, DEFAULT_ZOOM);
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',{maxZoom:19,attribution:'&copy; OpenStreetMap'}).addTo(map);
        donorLayer = L.layerGroup().addTo(map);
        requestLayer = L.layerGroup().addTo(map);
        hospitalLayer = L.layerGroup().addTo(map);
        setTimeout(() => map.invalidateSize(), 300);
        locateUser();
    } catch (e) {
        console.error('Map init error:', e);
        fallbackMode = true;
    }
}

function locateUser() {
    if (!navigator.geolocation) {loadData(); return;}
    navigator.geolocation.getCurrentPosition(
        pos => {currentLat = pos.coords.latitude; currentLng = pos.coords.longitude; if (map) map.setView([currentLat, currentLng], 11); loadData();},
        () => {console.log('Location denied'); loadData();},
        {enableHighAccuracy: true, timeout: 10000, maximumAge: 60000}
    );
}

function loadData() {
    console.log('loadData called');
    const radius = document.getElementById('radius-filter')?.value || 50;
    const btFilter = document.getElementById('bt-filter')?.value || '';
    let q = '';
    if (currentLat && currentLng && currentFilter !== 'all') q = '?lat=' + currentLat + '&lng=' + currentLng + '&radius=' + radius;
    if (btFilter) q += (q ? '&' : '?') + 'bloodType=' + btFilter;
    Promise.allSettled([
        (currentFilter === 'all' || currentFilter === 'donors') ? api('users/donors' + q) : Promise.resolve([]),
        (currentFilter === 'all' || currentFilter === 'requests') ? api('requests' + q) : Promise.resolve([]),
        (currentFilter === 'all' || currentFilter === 'hospitals') ? api('hospitals') : Promise.resolve([])
    ]).then(r => {
        donorData = r[0].status === 'fulfilled' ? r[0].value : [];
        requestData = r[1].status === 'fulfilled' ? r[1].value : [];
        hospitalData = r[2].status === 'fulfilled' ? r[2].value : [];
        if (map && !fallbackMode) renderLeafletData();
    });
}

function renderLeafletData() {
    if (!map) return;
    donorLayer.clearLayers();
    requestLayer.clearLayers();
    hospitalLayer.clearLayers();
    donorData.forEach(d => {
        if (!d.latitude || !d.longitude) return;
        L.marker([parseFloat(d.latitude), parseFloat(d.longitude)], {icon: L.divIcon({html:'<div style="width:30px;height:30px;border-radius:50%;background:#DC143C;color:#fff;display:flex;align-items:center;justify-content:center;font-weight:700;">' + (BT_LABEL[d.bloodType] || '?') + '</div>',iconSize:[30,30],iconAnchor:[15,15]})})
            .bindPopup('<strong>' + (d.fullName || 'Donor') + '</strong><br>' + (BT_LABEL[d.bloodType] || '-')).addTo(donorLayer);
    });
    requestData.forEach(r => {
        if (!r.latitude || !r.longitude) return;
        const c = (r.urgency === 'CRITICAL' ? '#FF3358' : r.urgency === 'URGENT' ? '#FFB700' : '#00E676');
        L.marker([parseFloat(r.latitude), parseFloat(r.longitude)], {icon: L.divIcon({html:'<div style="width:35px;height:35px;border-radius:10px;background:' + c + ';color:#000;display:flex;align-items:center;justify-content:center;font-weight:800;">🆘</div>',iconSize:[35,35],iconAnchor:[17,17]})})
            .bindPopup('<strong>' + (r.patientName || 'Request') + '</strong><br>' + (BT_LABEL[r.bloodType] || '-')).addTo(requestLayer);
    });
    hospitalData.forEach(h => {
        if (!h.latitude || !h.longitude) return;
        L.marker([parseFloat(h.latitude), parseFloat(h.longitude)], {icon: L.divIcon({html:'<div style="width:30px;height:30px;border-radius:10px;background:#2979FF;color:#fff;display:flex;align-items:center;justify-content:center;">🏥</div>',iconSize:[30,30],iconAnchor:[15,15]})})
            .bindPopup('<strong>' + (h.hospitalName || 'Hospital') + '</strong><br>' + (h.address || '-')).addTo(hospitalLayer);
    });
}

function setFilter(f, btn) {
    currentFilter = f;
    document.querySelectorAll('.map-controls button.filter-btn').forEach(b => b.classList.remove('active'));
    if (btn) btn.classList.add('active');
    loadData();
}

function applyBloodFilter() {loadData();}
function reloadData() {loadData();}
function centerOnMe() {if (map && currentLat != null && currentLng != null) map.setView([currentLat, currentLng], 12);}
function openChatWith(userId, name) {window.location = '/messages/?to=' + userId + '&name=' + encodeURIComponent(name);}
function respondToRequest(id) {api('requests/' + id + '/respond', 'PATCH').then(r => {if (r.message) {showToast('Response!', r.message, 'success'); loadData();}})}

console.log('map.js loaded');
window.addEventListener('load', initMap);
setInterval(() => loadData(), 30000);
    if (btn) btn.classList.add('active');
    loadData();
}

function applyBloodFilter() {loadData();}
function reloadData() {loadData();}
function centerOnMe() {if (map && currentLat != null && currentLng != null) map.setView([currentLat, currentLng], 12);}
function openChatWith(userId, name) {window.location = '/messages/?to=' + userId + '&name=' + encodeURIComponent(name);}
function respondToRequest(id) {api('requests/' + id + '/respond', 'PATCH').then(r => {if (r.message) {showToast('Response!', r.message, 'success'); loadData();}})}

window.addEventListener('load', initMap);
setInterval(() => loadData(), 30000);

console.log('map.js loaded completely');