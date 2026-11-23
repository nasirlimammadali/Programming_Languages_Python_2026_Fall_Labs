"""Command-line entry point for the flight schedule parser."""
import argparse
import datetime
import json
import logging
import os
import sys

from validator import load_airports
from csv_loader import parse_files
from query import run_queries

STUDENT_ID = "251ADB068"
FIRST_NAME = "Mammadali"
LAST_NAME = "Nasirli"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate flight CSV files and query a flight database")
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("-i", metavar="FILE", help="parse one CSV file")
    source.add_argument("-d", metavar="FOLDER", help="parse CSV files in a folder")
    source.add_argument("-j", metavar="FILE", help="load an existing JSON database")
    parser.add_argument("-a", metavar="FILE", help="airport list (required with -i and -d)")
    parser.add_argument("-o", metavar="FILE", help="database output path (default: db.json)")
    parser.add_argument("-q", metavar="FILE", help="JSON query file")
    parser.add_argument("-r", metavar="FOLDER", help="response output folder (default: current folder)")
    args = parser.parse_args(argv)

    if (args.i or args.d) and not args.a:
        parser.error("-a is required with -i or -d")
    if args.j and args.o:
        parser.error("-o cannot be used with -j")

    handler = None
    logger = logging.getLogger("flight_parser")
    logger.setLevel(logging.INFO)
    try:
        if args.i or args.d:
            if args.i:
                paths = [args.i]
            else:
                if not os.path.isdir(args.d):
                    raise OSError(f"folder does not exist: {args.d}")
                paths = [os.path.join(args.d, name) for name in sorted(os.listdir(args.d))
                         if name.endswith(".csv") and os.path.isfile(os.path.join(args.d, name))]
                if not paths:
                    raise OSError("folder contains no .csv files")

            airports = load_airports(args.a)
            records, errors = parse_files(paths, airports)
            db_path = args.o or "db.json"
            with open(db_path, "w", encoding="utf-8") as file:
                json.dump(records, file, indent=2)

            log_path = os.path.join(os.path.dirname(os.path.abspath(db_path)), "errors.log")
            handler = logging.FileHandler(log_path, mode="w", encoding="utf-8")
            handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s", datefmt="%Y-%m-%d %H:%M:%S"))
            logger.addHandler(handler)
            for error in errors:
                logger.warning(error)
            db = records
        else:
            with open(args.j, "r", encoding="utf-8") as file:
                db = json.load(file)
            if not isinstance(db, list) or any(not isinstance(item, dict) for item in db):
                raise ValueError("database must be a JSON array of objects")

        if args.q:
            with open(args.q, "r", encoding="utf-8") as file:
                queries = json.load(file)
            if not isinstance(queries, (dict, list)) or (isinstance(queries, list) and any(not isinstance(q, dict) for q in queries)):
                raise ValueError("query file must contain an object or an array of objects")
            response = run_queries(db, queries)
            folder = args.r or "."
            if not os.path.isdir(folder):
                raise OSError(f"response folder does not exist: {folder}")
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M")
            filename = f"response_{STUDENT_ID}_{FIRST_NAME}_{LAST_NAME}_{timestamp}.json"
            with open(os.path.join(folder, filename), "w", encoding="utf-8") as file:
                json.dump(response, file, indent=2)
        return 0
    except (OSError, json.JSONDecodeError, ValueError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1
    finally:
        if handler is not None:
            logger.removeHandler(handler)
            handler.close()


if __name__ == "__main__":
    sys.exit(main())
