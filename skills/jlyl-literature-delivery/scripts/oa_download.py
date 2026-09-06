#!/usr/bin/env python3
"""Retrieve and validate one public PMC PDF from current lawful sources."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import tempfile
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any


BUCKET_BASE = "https://pmc-oa-opendata.s3.amazonaws.com"
EUROPE_PMC = "https://europepmc.org/articles/{pmcid}?pdf=render"
USER_AGENT = "jlyl-literature-delivery/1.0"


def normalize_pmcid(value: str) -> str:
    text = value.strip().upper()
    if not text.startswith("PMC"):
        text = "PMC" + text
    if not re.fullmatch(r"PMC\d+", text):
        raise ValueError("PMCID must look like PMC123456")
    return text


def request_bytes(url: str, timeout: float) -> tuple[bytes, int, str]:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        data = response.read()
        return data, int(response.status), response.headers.get_content_type()


def list_bucket(
    *, prefix: str, timeout: float, delimiter: str | None = None
) -> tuple[list[str], list[str]]:
    query: dict[str, str] = {"list-type": "2", "prefix": prefix}
    if delimiter:
        query["delimiter"] = delimiter
    url = BUCKET_BASE + "/?" + urllib.parse.urlencode(query)
    data, _, _ = request_bytes(url, timeout)
    root = ET.fromstring(data)
    prefixes = [node.text or "" for node in root.findall(".//{*}CommonPrefixes/{*}Prefix")]
    keys = [node.text or "" for node in root.findall(".//{*}Contents/{*}Key")]
    return prefixes, keys


def get_json(url: str, timeout: float) -> dict[str, Any]:
    data, _, _ = request_bytes(url, timeout)
    value = json.loads(data.decode("utf-8"))
    if not isinstance(value, dict):
        raise ValueError("Metadata response is not a JSON object")
    return value


def aws_candidates(pmcid: str, timeout: float) -> list[dict[str, Any]]:
    prefixes, _ = list_bucket(prefix=f"{pmcid}.", delimiter="/", timeout=timeout)
    candidates: list[dict[str, Any]] = []
    for prefix in prefixes:
        _, keys = list_bucket(prefix=prefix, timeout=timeout)
        stem = prefix.rstrip("/")
        pdf_keys = [key for key in keys if key.lower().endswith(".pdf")]
        json_keys = [key for key in keys if key.lower().endswith(".json")]
        metadata: dict[str, Any] = {}
        preferred_json = next((key for key in json_keys if key == stem + ".json"), None)
        metadata_key = preferred_json or (json_keys[0] if json_keys else None)
        if metadata_key:
            try:
                metadata = get_json(
                    f"{BUCKET_BASE}/{urllib.parse.quote(metadata_key, safe='/')}", timeout
                )
            except Exception:
                metadata = {}
        version_match = re.search(r"\.(\d+)/$", prefix)
        preferred_pdf = next((key for key in pdf_keys if key == stem + ".pdf"), None)
        if preferred_pdf is None and pdf_keys:
            preferred_pdf = sorted(
                pdf_keys,
                key=lambda key: (
                    bool(re.search(r"(?:^|[-_.])(sup|supp|supplement)(?:[-_.]|$)", key, re.IGNORECASE)),
                    len(key),
                    key,
                ),
            )[0]
        candidates.append(
            {
                "prefix": prefix,
                "version": int(version_match.group(1)) if version_match else 0,
                "pdf_key": preferred_pdf,
                "metadata": metadata,
            }
        )
    candidates.sort(
        key=lambda item: (
            bool(item["metadata"].get("is_retracted", False)),
            bool(item["metadata"].get("is_manuscript", False)),
            -int(item["version"]),
        )
    )
    return candidates


def stream_to_file(url: str, path: Path, timeout: float) -> dict[str, Any]:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    digest = hashlib.sha256()
    size = 0
    with urllib.request.urlopen(request, timeout=timeout) as response, path.open("wb") as stream:
        content_type = response.headers.get_content_type()
        while True:
            chunk = response.read(1024 * 1024)
            if not chunk:
                break
            stream.write(chunk)
            digest.update(chunk)
            size += len(chunk)
        return {
            "http_status": int(response.status),
            "content_type": content_type,
            "bytes": size,
            "sha256": digest.hexdigest().upper(),
            "final_url": response.geturl(),
        }


def validate_pdf(path: Path) -> dict[str, Any]:
    with path.open("rb") as stream:
        signature = stream.read(5)
    if signature != b"%PDF-":
        raise ValueError("response does not begin with %PDF-")

    try:
        from pypdf import PdfReader
    except ImportError as exc:
        raise RuntimeError("pypdf is required for PDF validation") from exc

    reader = PdfReader(str(path))
    page_count = len(reader.pages)
    if page_count < 1:
        raise ValueError("PDF parser found no pages")
    metadata = reader.metadata or {}
    title = str(metadata.get("/Title") or "")
    first_page_text = " ".join((reader.pages[0].extract_text() or "").split())[:500]
    return {
        "page_count": page_count,
        "encrypted": bool(reader.is_encrypted),
        "metadata_title": title,
        "first_page_text": first_page_text,
    }


def attempt_download(
    *, route: str, url: str, part_path: Path, timeout: float, version_type: str
) -> tuple[dict[str, Any], bool]:
    attempt: dict[str, Any] = {"route": route, "source_url": url}
    try:
        transfer = stream_to_file(url, part_path, timeout)
        attempt.update(transfer)
        validation = validate_pdf(part_path)
        attempt.update(validation)
        attempt["version_type"] = version_type
        attempt["status"] = "valid_pdf"
        return attempt, True
    except urllib.error.HTTPError as exc:
        attempt.update({"status": "failed", "http_status": exc.code, "error": str(exc)})
    except Exception as exc:
        attempt.update({"status": "failed", "error": str(exc)})
    finally:
        if attempt.get("status") != "valid_pdf" and part_path.exists():
            part_path.unlink()
    return attempt, False


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Try PMC AWS, then Europe PMC, and validate the resulting PDF."
    )
    parser.add_argument("--pmcid", required=True)
    parser.add_argument("--output", help="Staging PDF path; existing files are never overwritten")
    parser.add_argument(
        "--check-only",
        action="store_true",
        help="Download, validate, report, and remove the temporary PDF",
    )
    parser.add_argument("--timeout", type=float, default=90.0)
    args = parser.parse_args()

    try:
        pmcid = normalize_pmcid(args.pmcid)
    except ValueError as exc:
        parser.error(str(exc))

    if not args.check_only and not args.output:
        parser.error("--output is required unless --check-only is used")
    if args.output and args.check_only:
        parser.error("use either --output or --check-only, not both")

    output_path: Path | None = None
    if args.check_only:
        handle, temp_name = tempfile.mkstemp(prefix=f"{pmcid}-", suffix=".pdf")
        os.close(handle)
        Path(temp_name).unlink()
        part_path = Path(temp_name)
    else:
        output_path = Path(args.output).expanduser().resolve()
        if output_path.exists():
            parser.error(f"output already exists: {output_path}")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        handle, temp_name = tempfile.mkstemp(
            prefix=output_path.name + ".", suffix=".part", dir=output_path.parent
        )
        os.close(handle)
        Path(temp_name).unlink()
        part_path = Path(temp_name)

    attempts: list[dict[str, Any]] = []
    selected: dict[str, Any] | None = None
    fallback_version_type = "unknown"

    try:
        try:
            candidates = aws_candidates(pmcid, args.timeout)
        except Exception as exc:
            attempts.append({"route": "pmc_aws", "status": "failed", "error": str(exc)})
            candidates = []

        for candidate in candidates:
            metadata = candidate["metadata"]
            if not bool(metadata.get("is_retracted", False)):
                fallback_version_type = (
                    "author_manuscript"
                    if metadata.get("is_manuscript")
                    else "version_of_record"
                )
                break

        for candidate in candidates:
            metadata = candidate["metadata"]
            pdf_key = candidate["pdf_key"]
            if bool(metadata.get("is_retracted", False)):
                attempts.append(
                    {
                        "route": "pmc_aws",
                        "status": "skipped_retracted",
                        "prefix": candidate["prefix"],
                    }
                )
                continue
            if not pdf_key:
                attempts.append(
                    {
                        "route": "pmc_aws",
                        "status": "no_pdf_object",
                        "prefix": candidate["prefix"],
                    }
                )
                continue
            url = f"{BUCKET_BASE}/{urllib.parse.quote(pdf_key, safe='/')}"
            version_type = "author_manuscript" if metadata.get("is_manuscript") else "version_of_record"
            attempt, ok = attempt_download(
                route="pmc_aws",
                url=url,
                part_path=part_path,
                timeout=args.timeout,
                version_type=version_type,
            )
            attempt["prefix"] = candidate["prefix"]
            attempts.append(attempt)
            if ok:
                selected = attempt
                break

        if selected is None:
            url = EUROPE_PMC.format(pmcid=pmcid)
            attempt, ok = attempt_download(
                route="europe_pmc",
                url=url,
                part_path=part_path,
                timeout=args.timeout,
                version_type=fallback_version_type,
            )
            attempts.append(attempt)
            if ok:
                selected = attempt

        if selected is None:
            result = {
                "status": "not_downloaded",
                "pmcid": pmcid,
                "next_step": "Try publisher open PDF, then authorized Chrome PMC fallback.",
                "attempts": attempts,
            }
            print(json.dumps(result, ensure_ascii=False, indent=2))
            return 1

        if args.check_only:
            part_path.unlink(missing_ok=True)
            saved_path = None
        else:
            assert output_path is not None
            os.replace(part_path, output_path)
            saved_path = str(output_path)

        result = {
            "status": "downloaded" if saved_path else "validated",
            "pmcid": pmcid,
            "route": selected["route"],
            "version_type": selected.get("version_type"),
            "source_url": selected.get("source_url"),
            "output": saved_path,
            "bytes": selected.get("bytes"),
            "page_count": selected.get("page_count"),
            "sha256": selected.get("sha256"),
            "metadata_title": selected.get("metadata_title"),
            "attempts": attempts,
        }
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    finally:
        if part_path.exists():
            part_path.unlink()


if __name__ == "__main__":
    raise SystemExit(main())
