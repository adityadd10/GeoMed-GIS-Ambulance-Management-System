"""
Route Optimizer Service

Features
--------
1. Snap start/end points to nearest drivable road (OSRM Nearest)
2. Try OSRM routing first
3. Fall back to OpenRouteService if available
4. Validate routes for campus-scale trips
5. Fall back to Haversine distance if routing fails
"""

import logging
import math
from typing import Dict, List, Optional

import requests

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def calculate_route(
    start_coords: List[float],
    end_coords: List[float],
    api_key: Optional[str] = None
) -> Dict:
    """
    Parameters
    ----------
    start_coords : [lon, lat]
    end_coords   : [lon, lat]
    """

    snapped_start = _snap_to_road_osrm(start_coords) or start_coords
    snapped_end = _snap_to_road_osrm(end_coords) or end_coords

    crow_distance = _haversine_km(snapped_start, snapped_end)

    # ------------------------------------------------------------------
    # Try OSRM first
    # ------------------------------------------------------------------

    try:
        logger.info("Attempting OSRM routing...")

        osrm_route = _try_osrm(snapped_start, snapped_end)

        if _route_is_reasonable(osrm_route, crow_distance):
            return {
                **osrm_route,
                "snapped_start": snapped_start,
                "snapped_end": snapped_end,
            }

        logger.warning("OSRM route rejected. Trying OpenRouteService.")

    except Exception as e:
        logger.warning(f"OSRM failed: {e}")

    # ------------------------------------------------------------------
    # Try ORS
    # ------------------------------------------------------------------

    if api_key:

        try:
            logger.info("Attempting OpenRouteService routing...")

            ors_route = _try_openrouteservice(
                snapped_start,
                snapped_end,
                api_key
            )

            if _route_is_reasonable(ors_route, crow_distance):
                return {
                    **ors_route,
                    "snapped_start": snapped_start,
                    "snapped_end": snapped_end,
                }

            logger.warning("ORS route rejected.")

        except Exception as e:
            logger.warning(f"ORS failed: {e}")

    # ------------------------------------------------------------------
    # Final fallback
    # ------------------------------------------------------------------

    logger.info("Using Haversine fallback.")

    fallback = _calculate_haversine(snapped_start, snapped_end)

    return {
        **fallback,
        "snapped_start": snapped_start,
        "snapped_end": snapped_end,
    }


def _snap_to_road_osrm(coords: List[float]) -> Optional[List[float]]:
    """
    Snap [lon, lat] to nearest routable road.
    """

    try:

        url = (
            f"https://router.project-osrm.org/"
            f"nearest/v1/driving/{coords[0]},{coords[1]}"
        )

        response = requests.get(
            url,
            params={"number": 1},
            timeout=5,
        )

        if response.status_code != 200:
            return None

        data = response.json()

        if (
            data.get("code") == "Ok"
            and data.get("waypoints")
        ):
            lon, lat = data["waypoints"][0]["location"]
            return [lon, lat]

    except Exception as e:
        logger.warning(f"Snap-to-road failed: {e}")

    return None


def _route_is_reasonable(
    route: Dict,
    crow_distance_km: float,
) -> bool:
    """
    Reject routes that are obviously wrong for campus routing.
    """

    if not route:
        return False

    geometry = route.get("geometry")

    if not geometry or len(geometry) < 2:
        return False

    distance = route.get("distance", 0)

    if crow_distance_km <= 3:

        max_allowed = max(
            crow_distance_km * 4,
            crow_distance_km + 3,
        )

        if distance > max_allowed:
            return False

    return True


def _try_osrm(
    start_coords: List[float],
    end_coords: List[float],
) -> Dict:

    url = (
        "https://router.project-osrm.org/"
        f"route/v1/driving/"
        f"{start_coords[0]},{start_coords[1]};"
        f"{end_coords[0]},{end_coords[1]}"
    )

    params = {
        "overview": "full",
        "geometries": "geojson",
    }

    response = requests.get(
        url,
        params=params,
        timeout=10,
    )

    if response.status_code != 200:
        raise Exception(
            f"OSRM API error ({response.status_code})"
        )

    data = response.json()

    if (
        data.get("code") != "Ok"
        or not data.get("routes")
    ):
        raise Exception("No OSRM route returned")

    route = data["routes"][0]

    geometry = [
        [lat, lon]
        for lon, lat in route["geometry"]["coordinates"]
    ]

    return {
        "distance": route["distance"] / 1000,
        "duration": route["duration"] / 60,
        "geometry": geometry,
        "source": "OSRM",
    }


def _try_openrouteservice(
    start_coords: List[float],
    end_coords: List[float],
    api_key: str,
) -> Dict:

    url = (
        "https://api.openrouteservice.org/"
        "v2/directions/driving-car"
    )

    headers = {
        "Authorization": api_key,
        "Content-Type": "application/json",
    }

    body = {
        "coordinates": [
            start_coords,
            end_coords,
        ]
    }

    response = requests.post(
        url,
        json=body,
        headers=headers,
        timeout=10,
    )

    if response.status_code != 200:
        raise Exception(
            f"ORS API error ({response.status_code})"
        )

    data = response.json()

    route = data["routes"][0]

    geometry = [
        [lat, lon]
        for lon, lat in route["geometry"]["coordinates"]
    ]

    return {
        "distance": route["summary"]["distance"] / 1000,
        "duration": route["summary"]["duration"] / 60,
        "geometry": geometry,
        "source": "OpenRouteService",
    }


def _calculate_haversine(
    start_coords: List[float],
    end_coords: List[float],
) -> Dict:

    distance = _haversine_km(
        start_coords,
        end_coords,
    )

    average_speed = 30  # km/h

    duration = (distance / average_speed) * 60

    return {
        "distance": distance,
        "duration": duration,
        "geometry": [
            [start_coords[1], start_coords[0]],
            [end_coords[1], end_coords[0]],
        ],
        "source": "Haversine",
    }


def _haversine_km(
    start_coords: List[float],
    end_coords: List[float],
) -> float:

    lon1, lat1 = start_coords
    lon2, lat2 = end_coords

    R = 6371

    lat1 = math.radians(lat1)
    lat2 = math.radians(lat2)

    dlat = lat2 - lat1
    dlon = math.radians(lon2 - lon1)

    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(lat1)
        * math.cos(lat2)
        * math.sin(dlon / 2) ** 2
    )

    c = 2 * math.atan2(
        math.sqrt(a),
        math.sqrt(1 - a),
    )

    return R * c