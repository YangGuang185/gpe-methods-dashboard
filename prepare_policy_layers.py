from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from prepare_map_layers import MAP_BOUNDS, DATA_DIR, CITIES_GEOJSON


POLICY_BATCHES = [
    {
        "batch_label": "2019年",
        "policy_year": 2019,
        "innovation_zone": ["北京", "上海", "天津", "深圳", "杭州", "合肥", "浙江德清县"],
        "application_zone": ["上海（浦东新区）", "深圳", "济南—青岛"],
    },
    {
        "batch_label": "2020年",
        "policy_year": 2020,
        "innovation_zone": ["重庆", "成都", "西安", "济南"],
        "application_zone": [],
    },
    {
        "batch_label": "2021年",
        "policy_year": 2021,
        "innovation_zone": ["广州", "武汉", "苏州", "长沙"],
        "application_zone": ["北京", "天津（滨海新区）", "杭州", "广州", "成都"],
    },
    {
        "batch_label": "2022年",
        "policy_year": 2022,
        "innovation_zone": [],
        "application_zone": ["南京", "武汉", "长沙"],
    },
    {
        "batch_label": "2021年12月",
        "policy_year": 2021,
        "innovation_zone": ["郑州", "沈阳", "哈尔滨"],
        "application_zone": [],
    },
]

SMART_PORT_META = {
    "天津港": 2019,
    "上海港": 2019,
    "深圳港": 2019,
    "青岛港": 2019,
    "广州港": 2020,
    "苏州港（太仓港区等）": 2021,
}


def norm_city(value: str) -> str:
    s = str(value).strip().replace(" ", "")
    if s in {"北京", "上海", "天津", "重庆"}:
        return s + "市"
    if s.endswith(("市", "县", "区", "盟")):
        return s
    return s + "市"


def parse_policy_area(raw: str) -> list[str]:
    s = str(raw).strip().replace(" ", "")
    if not s or s == "-":
        return []
    if "—" in s or ("-" in s and "青岛" in s):
        parts = s.replace("—", "-").split("-")
        out = []
        for part in parts:
            part = part.strip()
            if not part or part.startswith(("（", "(")):
                continue
            out.append(norm_city(part))
        return out
    if "（" in s:
        s = s.split("（", 1)[0]
    if s.startswith("浙江") and s.endswith("县"):
        return ["德清县"]
    return [norm_city(s)]


def city_coord_lookup() -> dict[str, list[float]]:
    raw = json.loads(CITIES_GEOJSON.read_text(encoding="utf-8"))
    lookup: dict[str, list[float]] = {}
    for feature in raw["features"]:
        props = feature.get("properties") or {}
        name = str(props.get("name") or "")
        centroid = props.get("centroid") or props.get("center")
        if not name or not isinstance(centroid, list) or len(centroid) != 2:
            continue
        lon, lat = float(centroid[0]), float(centroid[1])
        lookup[name] = [round(lon, 4), round(lat, 4)]
        if name.endswith("市"):
            lookup[name[:-1]] = lookup[name]
    lookup.setdefault("德清县", [119.967, 30.542])
    return lookup


def in_bounds(lon: float, lat: float, bounds: dict[str, float]) -> bool:
    return bounds["minLon"] <= lon <= bounds["maxLon"] and bounds["minLat"] <= lat <= bounds["maxLat"]


def build_policy_registry() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for batch in POLICY_BATCHES:
        for zone_type, areas in [
            ("innovation", batch["innovation_zone"]),
            ("application", batch["application_zone"]),
        ]:
            for raw in areas:
                for city in parse_policy_area(raw):
                    rows.append(
                        {
                            "city": city,
                            "cityLabel": city.replace("市", "").replace("县", ""),
                            "zoneType": zone_type,
                            "zoneLabel": "AI 创新发展试验区"
                            if zone_type == "innovation"
                            else "AI 创新应用先导区",
                            "policyYear": int(batch["policy_year"]),
                            "batchLabel": batch["batch_label"],
                        }
                    )
    return rows


def dedupe_policy_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    merged: dict[tuple[str, str], dict[str, Any]] = {}
    for row in rows:
        key = (row["city"], row["zoneType"])
        if key not in merged or row["policyYear"] < merged[key]["policyYear"]:
            merged[key] = row
    return list(merged.values())


def load_policy_layers(ports: list[dict[str, Any]]) -> dict[str, Any]:
    coords = city_coord_lookup()
    registry = dedupe_policy_rows(build_policy_registry())
    innovation: list[dict[str, Any]] = []
    application: list[dict[str, Any]] = []

    for row in registry:
        city = row["city"]
        point = coords.get(city) or coords.get(city.replace("市", ""))
        if not point:
            continue
        lon, lat = point
        if not in_bounds(lon, lat, MAP_BOUNDS):
            continue
        payload = {
            **row,
            "lon": lon,
            "lat": lat,
        }
        if row["zoneType"] == "innovation":
            innovation.append(payload)
        else:
            application.append(payload)

    smart_ports = []
    port_by_name = {port["port"]: port for port in ports}
    for port_name, policy_year in SMART_PORT_META.items():
        port = port_by_name.get(port_name)
        if not port:
            continue
        smart_ports.append(
            {
                "port": port_name,
                "city": port["city"],
                "group": port["group"],
                "portType": port["portType"],
                "policyYear": policy_year,
                "lon": port["lon"],
                "lat": port["lat"],
            }
        )

    return {
        "innovationZones": sorted(innovation, key=lambda item: (item["policyYear"], item["city"])),
        "applicationZones": sorted(application, key=lambda item: (item["policyYear"], item["city"])),
        "smartPorts": smart_ports,
    }


def port_city_labels(ports: list[dict[str, Any]]) -> list[dict[str, Any]]:
    labels: list[dict[str, Any]] = []
    seen: set[str] = set()
    for port in ports:
        city = port["city"]
        if city in seen:
            continue
        seen.add(city)
        labels.append(
            {
                "city": city,
                "lon": round(port["lon"] + 0.12, 4),
                "lat": round(port["lat"] + 0.10, 4),
            }
        )
    return labels
