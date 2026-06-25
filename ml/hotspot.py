"""
GeoMed Spatial Hotspot Detector
"""
import config

def detect_hotspots():
    """
    Returns current incident hotspots.
    Uses predefined campus locations combined with historical density.
    """
    locations = config.Config.CAMPUS_LOCATIONS
    
    # In a real scenario, this would run DBSCAN or KDE on the Trips table.
    # For now, we return statically weighted hotspots based on common campus areas.
    
    hotspots = [
        {
            "name": "LHC / Academic Area",
            "lat": locations['Lecture Hall Complex (LHC)'][0],
            "lon": locations['Lecture Hall Complex (LHC)'][1],
            "intensity": 0.8,
            "radius_meters": 300
        },
        {
            "name": "Hostel 12/13/14 Complex",
            "lat": locations['Hostel 12 (Crown of the Campus)'][0],
            "lon": locations['Hostel 12 (Crown of the Campus)'][1],
            "intensity": 0.6,
            "radius_meters": 200
        },
        {
            "name": "Main Gate",
            "lat": locations['Main Gate'][0],
            "lon": locations['Main Gate'][1],
            "intensity": 0.4,
            "radius_meters": 150
        }
    ]
    
    return hotspots
