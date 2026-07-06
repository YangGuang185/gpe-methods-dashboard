from __future__ import annotations

import math
from typing import Any


GROUP_COLORS = {
    "东北沿海": "#4A6FA5",
    "环渤海": "#087E72",
    "长三角": "#3F6B8A",
    "东南沿海": "#36A092",
    "珠三角及粤东粤西": "#D06645",
    "西南沿海（粤西）": "#B64D32",
    "西南沿海（北部湾）": "#786B5F",
    "西南沿海(海南)": "#E08B68",
}

GROUP_SHORT = {
    "东北沿海": "东北沿海",
    "环渤海": "环渤海",
    "长三角": "长三角",
    "东南沿海": "东南沿海",
    "珠三角及粤东粤西": "珠三角",
    "西南沿海（粤西）": "粤西沿海",
    "西南沿海（北部湾）": "北部湾",
    "西南沿海(海南)": "海南沿海",
}

GROUP_LABELS = {
    "东北沿海": [122.15, 39.85],
    "环渤海": [118.6, 38.35],
    "长三角": [121.25, 31.55],
    "东南沿海": [118.35, 26.15],
    "珠三角及粤东粤西": [114.35, 22.65],
    "西南沿海（粤西）": [110.15, 21.05],
    "西南沿海（北部湾）": [108.75, 21.75],
    "西南沿海(海南)": [109.85, 19.35],
}


def cross(origin: tuple[float, float], a: tuple[float, float], b: tuple[float, float]) -> float:
    return (a[0] - origin[0]) * (b[1] - origin[1]) - (a[1] - origin[1]) * (b[0] - origin[0])


def convex_hull(points: list[tuple[float, float]]) -> list[tuple[float, float]]:
    unique = sorted(set(points))
    if len(unique) <= 2:
        return unique

    lower: list[tuple[float, float]] = []
    for point in unique:
        while len(lower) >= 2 and cross(lower[-2], lower[-1], point) <= 0:
            lower.pop()
        lower.append(point)

    upper: list[tuple[float, float]] = []
    for point in reversed(unique):
        while len(upper) >= 2 and cross(upper[-2], upper[-1], point) <= 0:
            upper.pop()
        upper.append(point)

    return lower[:-1] + upper[:-1]


def expand_hull(
    hull: list[tuple[float, float]], center: tuple[float, float], scale: float = 1.38
) -> list[list[float]]:
    cx, cy = center
    ring = []
    for lon, lat in hull:
        ring.append(
            [
                round(cx + (lon - cx) * scale, 4),
                round(cy + (lat - cy) * scale, 4),
            ]
        )
    if ring and ring[0] != ring[-1]:
        ring.append(ring[0][:])
    return ring


def build_port_groups(ports: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for port in ports:
        grouped.setdefault(port["group"], []).append(port)

    groups: list[dict[str, Any]] = []
    for group_name in sorted(grouped):
        members = grouped[group_name]
        coords = [(port["lon"], port["lat"]) for port in members]
        center = (
            sum(lon for lon, _ in coords) / len(coords),
            sum(lat for _, lat in coords) / len(coords),
        )
        hull = convex_hull(coords)
        if len(hull) < 3:
            pad = 0.55
            hull = [
                (center[0] - pad, center[1] - pad),
                (center[0] + pad, center[1] - pad),
                (center[0] + pad, center[1] + pad),
                (center[0] - pad, center[1] + pad),
            ]
        label = GROUP_LABELS.get(group_name, list(center))
        groups.append(
            {
                "id": group_name,
                "name": group_name,
                "shortName": GROUP_SHORT.get(group_name, group_name),
                "color": GROUP_COLORS.get(group_name, "#53666a"),
                "label": [round(label[0], 4), round(label[1], 4)],
                "hull": expand_hull(hull, center),
                "ports": [
                    {
                        "port": port["port"],
                        "city": port["city"],
                        "province": port["province"],
                        "portType": port["portType"],
                        "lat": port["lat"],
                        "lon": port["lon"],
                    }
                    for port in sorted(members, key=lambda item: item["port"])
                ],
            }
        )
    return groups
