"""CSV input processing and duplicate-flight detection."""
import csv
import os
from validator import validate_row, to_record


def parse_files(paths: list[str], airports: set[str]) -> tuple[list[dict], list[str]]:
    records = []
    errors = []
    seen = set()

    for path in paths:
        filename = os.path.basename(path)
        with open(path, "r", encoding="utf-8-sig", newline="") as file:
            reader = csv.reader(file)
            for line_number, fields in enumerate(reader, start=1):
                # Header is always the first physical line.
                if line_number == 1:
                    continue
                raw_line = ",".join(fields)
                if not raw_line.strip() or raw_line.lstrip().startswith("#"):
                    continue
                fields = [field.strip() for field in fields]
                error = validate_row(fields, airports)
                if error is None:
                    record = to_record(fields)
                    key = (record["flight_id"], record["departure_datetime"])
                    if key in seen:
                        error = "DUPLICATE_FLIGHT"
                    else:
                        seen.add(key)
                        records.append(record)
                if error:
                    errors.append(f"{filename}:{line_number}: {error} | {raw_line}")
    return records, errors
