#!/usr/bin/env python3
"""Initialize a supervisor-research case without overwriting existing work."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import re
import sys
import unicodedata
from pathlib import Path

from case_utils import COVERAGE_AREA_ORDER


def write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def slugify(value: str, fallback: str) -> str:
    normalized = unicodedata.normalize("NFKC", value).strip()
    text = (
        unicodedata.normalize("NFKD", normalized)
        .encode("ascii", "ignore")
        .decode("ascii")
        .strip()
        .lower()
    )
    text = re.sub(r"[\s/\\]+", "-", text)
    text = re.sub(r"[^a-z0-9\-]+", "-", text)
    text = re.sub(r"-+", "-", text).strip("-_ ")
    if text:
        return text
    digest = hashlib.sha1(normalized.encode("utf-8")).hexdigest()[:8]
    return f"{fallback}-{digest}"


def split_schools(raw: str) -> list[str]:
    if not raw.strip():
        return []
    # Commas are legal in official institution names. Use only explicit list
    # separators that cannot silently split a school name.
    return [item.strip() for item in re.split(r"[;；\n]+", raw) if item.strip()]


def normalize_scope_name(value: str) -> str:
    return re.sub(r"\s+", " ", unicodedata.normalize("NFKC", value).strip()).casefold()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Initialize a PhD-supervisor research case")
    parser.add_argument("--workspace", required=True, help="User workspace in which outputs will be created")
    parser.add_argument("--location", required=True, help="Country or region")
    parser.add_argument("--schools", default="", help="Semicolon-separated school names; omit for QS top-300 scope")
    parser.add_argument(
        "--topic",
        default="thoracic oncology, especially lung cancer",
        help="Research topic",
    )
    parser.add_argument("--as-of", default=dt.date.today().isoformat(), help="Verification date, YYYY-MM-DD")
    parser.add_argument("--intake", default="", help="Optional target intake")
    parser.add_argument("--output-dir", default="", help="Optional explicit case directory")
    parser.add_argument("--resume", action="store_true", help="Return an existing initialized case without changing it")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        as_of_date = dt.date.fromisoformat(args.as_of)
    except ValueError:
        print("--as-of must use YYYY-MM-DD", file=sys.stderr)
        return 2
    if as_of_date > dt.date.today():
        print("--as-of cannot be later than the current system date", file=sys.stderr)
        return 2
    as_of = as_of_date.isoformat()

    workspace = Path(args.workspace).expanduser().resolve()
    if not workspace.exists() or not workspace.is_dir():
        print(f"Workspace does not exist or is not a directory: {workspace}", file=sys.stderr)
        return 2

    schools_input = split_schools(args.schools)
    normalized_schools = [normalize_scope_name(name) for name in schools_input]
    if len(normalized_schools) != len(set(normalized_schools)):
        print("--schools contains duplicate institution names", file=sys.stderr)
        return 2
    if args.output_dir:
        case_dir = Path(args.output_dir).expanduser().resolve()
    else:
        scope_suffix = ""
        if schools_input:
            scope_material = "\x1f".join(sorted(normalized_schools))
            scope_hash = hashlib.sha1(scope_material.encode("utf-8")).hexdigest()[:8]
            scope_suffix = f"-schools-{scope_hash}"
        dirname = (
            f"{slugify(args.location, 'region')}{scope_suffix}"
            f"-lung-cancer-phd-supervisors-{as_of}"
        )
        case_dir = (workspace / "outputs" / dirname).resolve()

    try:
        case_dir.relative_to(workspace)
    except ValueError:
        print(
            f"Output directory must remain inside the supplied workspace: {case_dir}",
            file=sys.stderr,
        )
        return 2

    data_dir = case_dir / "data"
    sentinel = data_dir / "case.json"
    if sentinel.exists():
        if args.resume:
            existing = json.loads(sentinel.read_text(encoding="utf-8"))
            expected_scope = "named_schools" if schools_input else "qs_top_300"
            mismatches = []
            for field, supplied in [
                ("location", args.location.strip()),
                ("topic", args.topic.strip()),
                ("intake", args.intake.strip()),
                ("asOf", as_of),
                ("scopeMode", expected_scope),
            ]:
                if str(existing.get(field, "")) != supplied:
                    mismatches.append(f"{field}: existing={existing.get(field)!r}, supplied={supplied!r}")
            existing_requested = existing.get("requestedSchools", [])
            if not isinstance(existing_requested, list) or sorted(
                normalize_scope_name(str(name)) for name in existing_requested
            ) != sorted(normalized_schools):
                mismatches.append(
                    "requestedSchools: existing="
                    f"{existing_requested!r}, supplied={schools_input!r}"
                )
            if mismatches:
                print(
                    "Resume parameters do not match the existing case:\n- " + "\n- ".join(mismatches),
                    file=sys.stderr,
                )
                return 4
            print(json.dumps({"status": "existing", "caseDir": str(case_dir)}, ensure_ascii=False))
            return 0
        print(f"Case already exists; use --resume instead of overwriting: {case_dir}", file=sys.stderr)
        return 3
    if case_dir.exists() and any(case_dir.iterdir()):
        print(f"Refusing to initialize a non-empty directory: {case_dir}", file=sys.stderr)
        return 3

    data_dir.mkdir(parents=True, exist_ok=True)
    case = {
        "schemaVersion": "1.2",
        "location": args.location.strip(),
        "topic": args.topic.strip(),
        "asOf": as_of,
        "intake": args.intake.strip(),
        "scopeMode": "named_schools" if schools_input else "qs_top_300",
        "requestedSchools": schools_input,
        "requestedSchoolResolutions": [],
        "qsThreshold": 300,
        "locationResolution": {
            "requestedLocation": args.location.strip(),
            "resolvedJurisdictions": [],
            "relationshipType": "",
            "sourceIds": [],
        },
        "scopeAudit": {
            "rankingSystem": "QS World University Rankings",
            "rankingEdition": "",
            "rankingPublicationDate": "",
            "jurisdictions": [],
            "rankingQuery": "",
            "eligibleInstitutionCount": None,
            "sourceIds": [],
            "includedSchoolIds": [],
            "excludedInstitutions": [],
        },
        "status": "draft",
        "discoveryPasses": [],
        "limitations": [],
    }
    schools = []
    base_ids = [slugify(name, "institution") for name in schools_input]
    base_counts = {base: base_ids.count(base) for base in set(base_ids)}
    for name, base_id, normalized_name in zip(schools_input, base_ids, normalized_schools):
        school_id = base_id
        if base_counts[base_id] > 1:
            suffix = hashlib.sha1(normalized_name.encode("utf-8")).hexdigest()[:8]
            school_id = f"{base_id}-{suffix}"
        schools.append(
            {
                "id": school_id,
                "officialName": name,
                "displayNameZh": name,
                "countryRegion": args.location.strip(),
                "namedByUser": True,
                "origin": "user_named",
                "inclusionDecision": "included",
                "inclusionReason": "Explicitly named by the user; QS status is contextual only.",
                "qs": {
                    "edition": "",
                    "publicationDate": "",
                    "rank": "",
                    "status": "not_verified",
                    "sourceIds": [],
                },
                "medicalSystem": {
                    "status": "unclear",
                    "summary": "",
                    "sourceIds": [],
                },
                "affiliatedInstitutions": [],
                "sourceIds": [],
            }
        )
        case["requestedSchoolResolutions"].append(
            {
                "requestedName": name,
                "schoolId": school_id,
                "decision": "unresolved",
                "sourceIds": [],
            }
        )

    coverage = [
        {
            "schoolId": school["id"],
            "area": area,
            "units": [],
            "status": "pending",
            "candidateIds": [],
            "sourceIds": [],
            "notes": "",
        }
        for school in schools
        for area in COVERAGE_AREA_ORDER
    ]

    write_json(data_dir / "case.json", case)
    write_json(data_dir / "schools.json", schools)
    write_json(data_dir / "coverage.json", coverage)
    write_json(data_dir / "records.json", [])
    write_json(data_dir / "sources.json", [])
    print(
        json.dumps(
            {
                "status": "created",
                "caseDir": str(case_dir),
                "scopeMode": case["scopeMode"],
                "schoolsInitialized": len(schools),
                "coverageRowsInitialized": len(coverage),
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
