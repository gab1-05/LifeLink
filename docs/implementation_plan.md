# Nearby Hospitals Map Integration

You requested a feature to automatically fetch and display nearby hospitals on a map using the OpenStreetMap Overpass API, based on the user's geolocation.

## Open Questions & Clarifications
- **React vs. Vanilla JS:** Your request mentions using React Leaflet and React Hooks. However, this application is built using **Django Templates and Vanilla JavaScript**, not React. To maintain compatibility and avoid introducing an entirely new frontend framework, I will implement this feature using our existing Vanilla JS and Leaflet setup. It will accomplish the exact same behavior (geolocation, Overpass API, markers, distance calculation).
- **Map Modal Automation:** To fulfill "see the map automatically instead of putting it manually", I will make the map modal open automatically when you click on the "Hospital Name" input field.

## Proposed Changes

### 1. Django Backend (`donors/views.py` & `donors/urls.py`)
#### [MODIFY] donors/views.py
- Create a new REST API endpoint `api_nearby_hospitals`.
- This view will accept `lat` and `lng` query parameters.
- It will make a request to the **Overpass API** for nodes tagged `amenity=hospital` within a 5000m (5km) radius.
- It will parse the response and return a JSON list of hospitals (name, address, latitude, longitude).

#### [MODIFY] donors/urls.py
- Add routing for `path("api/nearby-hospitals/", views.api_nearby_hospitals, name="api_nearby_hospitals")`.

### 2. Frontend (`donors/templates/base.html`)
#### [MODIFY] base.html
- **Geolocation:** Enhance `openHospitalMap()` to automatically request `navigator.geolocation` if the location isn't already known.
- **Overpass Integration:** Update the fetch call to hit `/api/nearby-hospitals/?lat=...&lng=...` instead of the local database.
- **Markers & Distance:** Calculate the straight-line distance from the user to each hospital and display it in the marker popup alongside the name and address.
- **Auto-Open:** Add an `onfocus` event to the `req-hospital` input so the map modal opens automatically when the user clicks the input field.

## Verification Plan
### Manual Verification
- Focus the "Hospital Name" input field in the Request Blood modal. The map should open automatically.
- The browser should prompt for location permission (if not already granted).
- Once granted, the map centers on the user and fetches real hospitals within 5km via the Overpass API.
- Clicking a hospital marker displays Name, Address, and Distance, and selecting it auto-fills the form.
