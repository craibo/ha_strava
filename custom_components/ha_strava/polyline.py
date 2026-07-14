"""Google encoded polyline algorithm decoder (precision 5).

Reference: https://developers.google.com/maps/documentation/utilities/polylinealgorithm
"""

from __future__ import annotations


def decode_polyline(polyline_str: str, precision: int = 5) -> list[tuple[float, float]]:
    """Decode a Google encoded polyline string into a list of (lat, lon) tuples."""
    if not polyline_str:
        return []

    index = 0
    lat = 0
    lon = 0
    coordinates: list[tuple[float, float]] = []
    factor = 10**precision
    length = len(polyline_str)

    while index < length:
        for is_lat in (True, False):
            shift = 0
            result = 0
            while True:
                byte = ord(polyline_str[index]) - 63
                index += 1
                result |= (byte & 0x1F) << shift
                shift += 5
                if byte < 0x20:
                    break
            delta = ~(result >> 1) if (result & 1) else (result >> 1)
            if is_lat:
                lat += delta
            else:
                lon += delta

        coordinates.append((lat / factor, lon / factor))

    return coordinates
