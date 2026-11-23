"""Validation helpers for flight schedule rows."""
import datetime
import math
import re

_DATE_RE = re.compile(r"^[0-9]{4}-[0-9]{2}-[0-9]{2} [0-9]{2}:[0-9]{2}$")
_ID_RE = re.compile(r"^[A-Za-z0-9]{2,8}$")
_AIRPORT_RE = re.compile(r"^[A-Z]{3}$")


def load_airports(path: str) -> set[str]:
    airports = set()
    with open(path, "r", encoding="utf-8") as file:
        for line in file:
            code = line.strip()
            if code and not code.startswith("#"):
                airports.add(code)
    return airports


def _parse_datetime(value: str):
    if not _DATE_RE.fullmatch(value):
        return None
    try:
        return datetime.datetime.strptime(value, "%Y-%m-%d %H:%M")
    except ValueError:
        return None


def validate_row(fields: list[str], airports: set[str]) -> str | None:
    fields = [str(value).strip() for value in fields]
    if len(fields) != 6:
        return "WRONG_FIELD_COUNT"
    if any(value == "" for value in fields):
        return "MISSING_FIELD"

    flight_id, origin, destination, departure, arrival, price_text = fields
    if not _ID_RE.fullmatch(flight_id):
        return "INVALID_FLIGHT_ID"
    if not _AIRPORT_RE.fullmatch(origin) or origin not in airports:
        return "INVALID_ORIGIN"
    if not _AIRPORT_RE.fullmatch(destination) or destination not in airports:
        return "INVALID_DESTINATION"
    if origin == destination:
        return "SAME_ORIGIN_DESTINATION"

    dep_dt = _parse_datetime(departure)
    if dep_dt is None:
        return "INVALID_DEPARTURE"
    arr_dt = _parse_datetime(arrival)
    if arr_dt is None:
        return "INVALID_ARRIVAL"
    if arr_dt <= dep_dt:
        return "ARRIVAL_NOT_AFTER_DEPARTURE"

    try:
        price = float(price_text)
    except (TypeError, ValueError):
        return "INVALID_PRICE"
    if not math.isfinite(price):
        return "INVALID_PRICE"
    if price <= 0:
        return "NON_POSITIVE_PRICE"
    return None


def to_record(fields: list[str]) -> dict:
    values = [str(value).strip() for value in fields]
    return {
        "flight_id": values[0],
        "origin": values[1],
        "destination": values[2],
        "departure_datetime": values[3],
        "arrival_datetime": values[4],
        "price": float(values[5]),
    }
