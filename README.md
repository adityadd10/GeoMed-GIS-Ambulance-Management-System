# Ambulance Service - IITB Hospital

A comprehensive ambulance service management system for IITB hospital with real-time routing, trip tracking, data analytics, and visualization.

## Features

- 🚑 **Real-time Route Tracking**: Animated ambulance routing from hospital to pickup location and back
- 📊 **Analytics Dashboard**: Isochrone zones and route frequency heat maps
- 📝 **Trip Management**: Form-based trip recording with auto date/time and odometer tracking
- 📈 **Data Export**: CSV export of all ambulance trip data
- 🗺️ **Dual Map Display**: Separate maps for route visualization and analytics
- 💾 **Database Storage**: SQLite database for persistent trip data

## Technology Stack

- **Backend**: Python, Flask, SQLAlchemy
- **Frontend**: HTML5, CSS3, JavaScript, Bootstrap 5
- **Maps**: Leaflet.js, OpenStreetMap
- **Routing**: 3-Tier Fallback System (ORS → OSRM → Haversine)
- **Database**: SQLite

## Routing System

This application uses a **robust 3-tier routing fallback system** to ensure routing always works:

### Tier 1: OpenRouteService (ORS) - Primary
- **Most accurate** road-based routing
- Requires API key (free tier available)
- Used when `ORS_API_KEY` is configured
- Best for production use

### Tier 2: OSRM - Secondary
- **Free public service**, no API key needed
- Automatically used when ORS key is not available or ORS fails
- Good road-based routing as fallback
- Default routing service

### Tier 3: Haversine - Tertiary
- **Straight-line distance** calculation
- Used only when both ORS and OSRM fail
- Always available as last resort
- Assumes 30 km/h average speed

**How it works**: The system automatically tries each service in order. If one fails, it seamlessly falls back to the next, ensuring your application always has working route calculations.

## Prerequisites

- Python 3.8 or higher
- OpenRouteService API key (free tier available)

## Installation

1. **Clone or navigate to the project directory**
   ```bash
   cd Ambulance
   ```

2. **Install Python dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Get OpenRouteService API Key (Optional)**
   - Visit [OpenRouteService](https://openrouteservice.org/dev/#/signup)
   - Sign up for a free account
   - Copy your API key
   - **Note**: If you skip this step, the app will use OSRM (free public service)

4. **Configure API Key (Optional)**
   - Create a `.env` file or edit `config.py`
   - Add your API key:
     ```python
     ORS_API_KEY = 'your_actual_api_key_here'
     ```
   - Without an API key, routing will automatically use OSRM

## Running the Application

1. **Start the Flask server**
   ```bash
   python app.py
   ```

2. **Open your browser**
   - Navigate to: `http://localhost:5000`

3. **Using the Application**
   - Fill in the trip details form
   - Select a pickup location from the dropdown
   - Click "Submit Trip" to record and visualize the route
   - View the animated ambulance route on the first map
   - View analytics (isochrones and route frequency) on the second map
   - Click "Export CSV" to download all trip data

## Project Structure

```
Ambulance/
├── app.py                 # Main Flask application
├── models.py              # Database models
├── config.py              # Configuration settings
├── route_optimizer.py     # 3-tier routing service
├── requirements.txt       # Python dependencies
├── ambulance.db          # SQLite database (auto-generated)
├── templates/
│   └── index.html        # Main HTML page
└── static/
    ├── css/
    │   └── style.css     # Custom styles
    └── js/
        ├── main.js       # Main application logic
        └── analytics.js  # Analytics & visualization
```

## Features Explained

### Route Visualization
- Shows ambulance route from IITB Hospital to pickup location and back
- Animated ambulance marker follows the route
- Displays trip summary with distance, duration, and odometer readings

### Analytics Map
- **Isochrone Zones**: Shows areas reachable within 3, 5, and 7 minutes from hospital
- **Route Frequency**: Color-coded routes based on usage frequency
  - Red: High frequency routes
  - Orange: Medium frequency routes
  - Yellow: Low frequency routes

### Data Management
- Automatic odometer tracking
- Trip history stored in SQLite database
- CSV export for data analysis
- Automatic calculation of trip metrics

## API Endpoints

- `GET /` - Main application page
- `GET /api/get-current-odometer` - Get current odometer reading
- `GET /api/get-locations` - Get all campus locations
- `POST /api/submit-trip` - Submit new ambulance trip
- `GET /api/export-csv` - Export trip data to CSV
- `GET /api/get-isochrones` - Get isochrone zones
- `GET /api/get-route-frequency` - Get route frequency data

## Troubleshooting

### Routing Issues
If you see routing errors or unexpected routes:
1. **Check which routing service is being used** (check browser console logs)
2. **ORS Issues**: 
   - Verify your API key is correct in `config.py` or `.env`
   - Check your API key quota at OpenRouteService dashboard
   - System will automatically fall back to OSRM if ORS fails
3. **OSRM Issues**: 
   - Check your internet connection
   - System will fall back to Haversine (straight-line) if OSRM is unavailable
4. **Haversine Mode**: If you see straight lines instead of roads, both ORS and OSRM are unavailable

### Database Issues
If database errors occur:
1. Delete `ambulance.db` file
2. Restart the application (database will be recreated)

### Map Not Loading
1. Check your internet connection (maps require online access)
2. Clear browser cache
3. Try a different browser

## Campus Locations

The application includes the following IITB campus locations:
- Hostels 1-15
- Main Gate
- Academic Area
- Library
- Student Activity Center (SAC)
- Convocation Hall
- Sports Complex

## License

This project is created for academic purposes at IIT Bombay.

## Support

For issues or questions, please contact the development team.
