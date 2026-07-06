from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any


DATA_DIR = Path(__file__).resolve().parent / "data"
PROVINCES_GEOJSON = DATA_DIR / "china_provinces.json"
CITIES_GEOJSON = DATA_DIR / "china_cities.json"

MAP_BOUNDS = {
    "minLon": 107.8,
    "maxLon": 122.8,
    "minLat": 18.0,
    "maxLat": 41.8,
}

PROVINCE_FILLS = [
    "#F6F2EA",
    "#F3EEE4",
    "#F8F4EC",
    "#F1ECE3",
    "#F5F0E8",
    "#F2EDE4",
    "#F7F3EB",
    "#EFEBE2",
]

COASTAL_PROVINCES = {
    "辽宁省",
    "河北省",
    "天津市",
    "山东省",
    "江苏省",
    "上海市",
    "浙江省",
    "福建省",
    "广东省",
    "广西壮族自治区",
    "海南省",
}


def ring_bbox(ring: list[list[float]]) -> tuple[float, float, float, float]:
    lons = [point[0] for point in ring]
    lats = [point[1] for point in ring]
    return min(lons), min(lats), max(lons), max(lats)


def intersects_bounds(
    ring: list[list[float]], bounds: dict[str, float]
) -> bool:
    min_lon, min_lat, max_lon, max_lat = ring_bbox(ring)
    if max_lon < bounds["minLon"] or min_lon > bounds["maxLon"]:
        return False
    if max_lat < bounds["minLat"] or min_lat > bounds["maxLat"]:
        return False
    return True


def perpendicular_distance(
    point: list[float], start: list[float], end: list[float]
) -> float:
    if start == end:
        dx = point[0] - start[0]
        dy = point[1] - start[1]
        return math.hypot(dx, dy)
    numerator = abs(
        (end[0] - start[0]) * (start[1] - point[1])
        - (start[0] - point[0]) * (end[1] - start[1])
    )
    denominator = math.hypot(end[0] - start[0], end[1] - start[1])
    return numerator / denominator


def simplify_ring(
    ring: list[list[float]], tolerance: float
) -> list[list[float]]:
    if len(ring) <= 2:
        return ring
    start, end = ring[0], ring[-1]
    max_distance = 0.0
    index = 0
    for i in range(1, len(ring) - 1):
        distance = perpendicular_distance(ring[i], start, end)
        if distance > max_distance:
            index = i
            max_distance = distance
    if max_distance > tolerance:
        left = simplify_ring(ring[: index + 1], tolerance)
        right = simplify_ring(ring[index:], tolerance)
        return left[:-1] + right
    return [start, end]


def geometry_rings(geometry: dict[str, Any]) -> list[list[list[float]]]:
    geom_type = geometry["type"]
    coordinates = geometry["coordinates"]
    if geom_type == "Polygon":
        return [coordinates[0]]
    if geom_type == "MultiPolygon":
        return [polygon[0] for polygon in coordinates]
    return []


def round_ring(ring: list[list[float]]) -> list[list[float]]:
    return [[round(lon, 4), round(lat, 4)] for lon, lat in ring]


def feature_layers(
    features: list[dict[str, Any]],
    bounds: dict[str, float],
    tolerance: float,
    *,
    level: str | None = None,
    name_filter: set[str] | None = None,
) -> list[dict[str, Any]]:
    layers: list[dict[str, Any]] = []
    for feature in features:
        props = feature.get("properties") or {}
        if level is not None and props.get("level") not in {level, None}:
            if props.get("level") != level:
                continue
        name = str(props.get("name") or "")
        if name_filter is not None and name not in name_filter:
            continue
        rings = []
        for ring in geometry_rings(feature["geometry"]):
            if not intersects_bounds(ring, bounds):
                continue
            simplified = round_ring(simplify_ring(ring, tolerance))
            if len(simplified) >= 3:
                rings.append(simplified)
        if not rings:
            continue
        centroid = props.get("centroid") or props.get("center") or []
        label = None
        if isinstance(centroid, list) and len(centroid) == 2:
            lon, lat = centroid
            if (
                bounds["minLon"] <= lon <= bounds["maxLon"]
                and bounds["minLat"] <= lat <= bounds["maxLat"]
            ):
                label = [round(float(lon), 4), round(float(lat), 4)]
        layers.append({"name": name, "rings": rings, "label": label})
    return layers


def load_map_layers() -> dict[str, Any]:
    if not PROVINCES_GEOJSON.exists() or not CITIES_GEOJSON.exists():
        raise FileNotFoundError(
            "Missing map GeoJSON in web/gpe-dashboard/data/. "
            "Download china_provinces.json and china_cities.json first."
        )

    provinces_raw = json.loads(PROVINCES_GEOJSON.read_text(encoding="utf-8"))
    cities_raw = json.loads(CITIES_GEOJSON.read_text(encoding="utf-8"))

    provinces = feature_layers(
        provinces_raw["features"],
        MAP_BOUNDS,
        tolerance=0.01,
        name_filter=COASTAL_PROVINCES,
    )
    for index, province in enumerate(provinces):
        province["fill"] = PROVINCE_FILLS[index % len(PROVINCE_FILLS)]

    prefectures = feature_layers(
        cities_raw["features"],
        MAP_BOUNDS,
        tolerance=0.004,
        level="city",
    )

    districts = feature_layers(
        cities_raw["features"],
        MAP_BOUNDS,
        tolerance=0.0025,
        level="district",
    )

    return {
        "source": "Alibaba DataV / areas_v3 administrative boundaries",
        "bounds": MAP_BOUNDS,
        "provinces": provinces,
        "prefectures": prefectures,
        "districts": districts,
    }
