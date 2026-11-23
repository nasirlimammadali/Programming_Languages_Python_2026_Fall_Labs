"""Flight database query functions."""
import datetime
import math

_RECORD_KEYS = {
    "flight_id", "origin", "destination", "departure_datetime",
    "arrival_datetime", "price"
}
_ALLOWED = _RECORD_KEYS | {"min_price", "sort_by", "order", "limit"}
_DT_FORMAT = "%Y-%m-%d %H:%M"


def _valid_datetime(value):
    if not isinstance(value, str):
        return False
    try:
        parsed = datetime.datetime.strptime(value, _DT_FORMAT)
        return parsed.strftime(_DT_FORMAT) == value
    except ValueError:
        return False


def _is_number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def _valid_query(q):
    if not isinstance(q, dict) or not set(q).issubset(_ALLOWED):
        return False
    for key in ("flight_id", "origin", "destination"):
        if key in q and not isinstance(q[key], str):
            return False
    for key in ("departure_datetime", "arrival_datetime"):
        if key in q and not _valid_datetime(q[key]):
            return False
    for key in ("price", "min_price"):
        if key in q and not _is_number(q[key]):
            return False
    if "sort_by" in q and q["sort_by"] not in _RECORD_KEYS:
        return False
    if "order" in q and (q["sort_by"] is None or q["order"] not in ("asc", "desc")):
        return False
    if "limit" in q and (isinstance(q["limit"], bool) or not isinstance(q["limit"], int) or q["limit"] < 0):
        return False
    return True


def run_query(db: list[dict], query: dict) -> dict:
    if not _valid_query(query):
        return {"query": query, "error": "INVALID_QUERY", "matches": []}

    matches = []
    for flight in db:
        if "flight_id" in query and flight["flight_id"] != query["flight_id"]:
            continue
        if "origin" in query and flight["origin"] != query["origin"]:
            continue
        if "destination" in query and flight["destination"] != query["destination"]:
            continue
        if "departure_datetime" in query and flight["departure_datetime"] < query["departure_datetime"]:
            continue
        if "arrival_datetime" in query and flight["arrival_datetime"] > query["arrival_datetime"]:
            continue
        if "price" in query and flight["price"] > query["price"]:
            continue
        if "min_price" in query and flight["price"] < query["min_price"]:
            continue
        matches.append(flight)

    if "sort_by" in query:
        matches = sorted(matches, key=lambda item: item[query["sort_by"]], reverse=query.get("order", "asc") == "desc")
    if "limit" in query:
        matches = matches[:query["limit"]]
    return {"query": query, "matches": matches}


def run_queries(db: list[dict], queries: dict | list) -> list[dict]:
    if isinstance(queries, dict):
        queries = [queries]
    if not isinstance(queries, list):
        return []
    return [run_query(db, q) for q in queries]
