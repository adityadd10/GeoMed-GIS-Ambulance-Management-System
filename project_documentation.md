# Ambulance Service Project - Complete Documentation

## File-by-File Breakdown

### 1. `app.py` - Main Flask Application

**Libraries Used:**
- `flask`: Web framework (Flask, render_template, request, jsonify, send_file)
- `flask_cors`: Handling Cross-Origin Resource Sharing
- `models`: Database models (db, AmbulanceTrip)
- `config`: Configuration settings
- `route_optimizer`: Custom routing logic
- `requests`: Making HTTP requests
- `json`: JSON parsing
- `datetime`: Date and time handling
- `csv`: CSV file generation
- `io`: In-memory file handling

**Functions & Routes:**

#### `__init__` (App Setup)
**Lines 12-21:**
- Initializes Flask application
- Configures SQLAlchemy database URI and tracking settings from `config.py`
- Initializes CORS and Database
- Creates database tables within the app context

#### `index()`
**Lines 23-25:**
- **Route:** `/`
- Renders the main `index.html` template

#### `get_current_odometer()`
**Lines 27-35:**
- **Route:** `/api/get-current-odometer` (GET)
- Queries the last trip from the database
- Returns the end reading of the last trip, or the initial odometer value if no trips exist

#### `get_locations()`
**Lines 37-47:**
- **Route:** `/api/get-locations` (GET)
- Iterates through `config.CAMPUS_LOCATIONS`
- Returns a list of all campus locations with their coordinates

#### `get_route()`
**Lines 49-79:**
- **Route:** `/api/get-route` (POST)
- Receives pickup coordinates from the request
- Calculates two routes:
    1. Hospital -> Pickup Location
    2. Pickup Location -> Hospital
- Combines distance, duration, and geometry of both routes
- Returns the combined route data for visualization

#### `calculate_route(start_coords, end_coords)`
**Lines 81-92:**
- Helper function to calculate route between two points
- Calls `route_optimizer.calculate_route` using the 3-tier fallback system

#### `submit_trip()`
**Lines 94-156:**
- **Route:** `/api/submit-trip` (POST)
- Receives trip data (patient name, driver, purpose, etc.)
- Calculates the route again to ensure accuracy
- Computes departure and arrival times
- Updates odometer reading
- Creates a new `AmbulanceTrip` record in the database
- Commits the transaction and returns the saved trip details

#### `export_csv()`
**Lines 157-191:**
- **Route:** `/api/export-csv` (GET)
- Queries all trips from the database
- Creates an in-memory CSV file using `io.StringIO`
- Writes headers and trip data rows
- Returns the CSV file as a downloadable attachment

#### `get_isochrones()`
**Lines 193-209:**
- **Route:** `/api/get-isochrones` (GET)
- Calculates reachable zones (3, 5, 7 minutes) from the hospital
- Calls `calculate_isochrone` for each time range
- Returns polygon geometries for visualization

#### `calculate_isochrone(coords, seconds)`
**Lines 211-235:**
- Helper function to fetch isochrone data from OpenRouteService API
- Converts response coordinates from [lon, lat] to [lat, lon]

#### `get_route_frequency()`
**Lines 237-272:**
- **Route:** `/api/get-route-frequency` (GET)
- Analyzes all past trips to find frequently used route segments
- Breaks down routes into small segments and counts their usage
- Returns normalized frequency data for heatmap visualization

---

### 2. `config.py` - Configuration Settings

**Libraries Used:**
- `os`: Environment variable access

**Variables:**

**Lines 3-5:** Database Configuration
- `SQLALCHEMY_DATABASE_URI`: Path to SQLite database
- `SQLALCHEMY_TRACK_MODIFICATIONS`: Disabled for performance

**Lines 7-8:** API Configuration
- `ORS_API_KEY`: OpenRouteService API key (with default fallback)

**Lines 10-12:** Routing Settings
- `ROUTING_TIMEOUT`: Timeout for API calls (10s)
- `HAVERSINE_SPEED_KMH`: Average speed for fallback calculations (30 km/h)

**Lines 14-15:** Hospital Location
- `HOSPITAL_COORDS`: Fixed coordinates for IITB Hospital

**Lines 17-37:** Campus Locations
- `CAMPUS_LOCATIONS`: Dictionary of hostel and landmark coordinates

**Lines 39-40:** Odometer
- `INITIAL_ODOMETER`: Starting reading for the ambulance (0)

---

### 3. `models.py` - Database Models

**Libraries Used:**
- `flask_sqlalchemy`: Database ORM
- `datetime`: Time handling

**Classes:**

#### `AmbulanceTrip`
**Lines 6-27:**
- Defines the schema for `ambulance_trips` table
- Fields: `id`, `date`, `time`, `km_reading_start`, `km_reading_end`, `pickup_location`, `patient_name`, `driver_name`, `purpose`, `notes`, `distance_km`, `duration_minutes`, `departure_time`, `arrival_time`, `route_geometry`, `created_at`

#### `to_dict(self)`
**Lines 28-48:**
- Converts the database object to a Python dictionary
- Formats dates and times for JSON serialization

---

### 4. `route_optimizer.py` - Routing Logic

**Libraries Used:**
- `requests`: HTTP requests
- `math`: Mathematical calculations (Haversine)
- `logging`: Error logging
- `typing`: Type hinting

**Functions:**

#### `calculate_route(...)`
**Lines 19-48:**
- Main entry point for routing
- Implements **3-Tier Fallback System**:
    1. Tries **OpenRouteService** (Best accuracy)
    2. If fails, tries **OSRM** (Free, good accuracy)
    3. If fails, uses **Haversine** (Straight line, always works)

#### `_try_openrouteservice(...)`
**Lines 51-97:**
- Calls OpenRouteService API
- Returns distance, duration, and precise geometry

#### `_try_osrm(...)`
**Lines 99-145:**
- Calls OSRM public API
- Returns distance, duration, and geometry

#### `_calculate_haversine(...)`
**Lines 147-191:**
- Calculates straight-line distance using Haversine formula
- Estimates duration based on 30 km/h average speed
- Returns a simple straight-line geometry

---

### 5. `static/js/main.js` - Frontend Logic

**Functions:**

#### `initializeMaps()`
**Lines 18-54:**
- Initializes Leaflet maps for Route and Analysis views
- Adds tile layers (OpenStreetMap)
- Places hospital markers on both maps
- Loads initial analytics data

#### `loadCurrentOdometer()`
**Lines 57-66:**
- Fetches current odometer reading from API
- Updates the input field

#### `loadLocations()`
**Lines 69-88:**
- Fetches campus locations from API
- Populates the "From Location" dropdown menu

#### `handleFormSubmit(e)`
**Lines 116-169:**
- Handles trip form submission
- Collects form data
- Sends data to `/api/submit-trip`
- On success: displays route, updates summary, and refreshes analytics

#### `displayRoute(data, locationData)`
**Lines 172-202:**
- Clears previous route
- Adds pickup marker
- Draws the polyline for the full route (Hospital -> Pickup -> Hospital)
- Fits map bounds to show the entire route
- Starts ambulance animation

#### `animateAmbulance(coords)`
**Lines 225-257:**
- Creates an ambulance marker
- Moves the marker along the route points every 200ms
- Returns ambulance to hospital after trip completion

#### `loadIsochrones()`
**Lines 282-310:**
- Fetches isochrone data
- Draws 3, 5, and 7-minute reachability polygons on the analysis map

#### `loadRouteFrequency()`
**Lines 313-342:**
- Fetches route usage frequency
- Draws color-coded segments (Red/Orange/Yellow) based on usage intensity

---

### 6. `static/js/analytics.js` - Analytics Logic

**Functions:**

#### `displayIsochrones(isochroneData)`
**Lines 7-25:**
- Renders isochrone polygons with specific colors for each time range

#### `displayRouteFrequency(segments)`
**Lines 28-58:**
- Renders route segments with varying colors and weights based on frequency

#### `calculateStatistics(trips)`
**Lines 61-90:**
- Computes total/average distance and duration
- Identifies the most common pickup location

#### `analyzePeakHours(trips)`
**Lines 101-115:**
- Calculates hourly distribution of trips to find peak usage times

---

### 7. `templates/index.html` - Frontend Structure

**Structure:**

**Lines 1-23:** Head
- Includes Bootstrap, Leaflet CSS, Google Fonts, Font Awesome, and Custom CSS

**Lines 27-39:** Header
- Title and "Export CSV" button

**Lines 42-205:** Main Content Grid
- **Left Column (Lines 45-144):**
    - Trip Details Form (Date, Time, Location, Patient Info)
    - Trip Summary Card (Hidden by default, shows after trip)
- **Right Column (Lines 147-203):**
    - Route Map (Top)
    - Analysis Map (Bottom)

**Lines 208-213:** Loading Overlay
- Spinner shown during trip processing

**Lines 216-223:** Scripts
- Includes Bootstrap JS, Leaflet JS, and custom `main.js`/`analytics.js`
