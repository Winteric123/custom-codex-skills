#!/usr/bin/env python3
"""Live literature lookup for the jlyl-literature-delivery skill.

Uses only the Python standard library. Queries PubMed, OpenAlex, and Crossref,
normalizes results, deduplicates candidates, and recommends a delivery identifier.
"""

from __future__ import annotations

import argparse
import base64
import ctypes
import datetime as dt
import functools
import json
import math
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

if os.name == "nt":
    from ctypes import wintypes


DOI_RE = re.compile(r"10\.\d{4,9}/[^\s\"'<>]+", re.IGNORECASE)
PMID_RE = re.compile(r"^(?:PMID\s*:\s*)?(\d{1,10})$", re.IGNORECASE)
PMCID_RE = re.compile(r"^(?:PMCID\s*:\s*)?(PMC\d+)$", re.IGNORECASE)
DEFAULT_CREDENTIAL_FILE = (
    Path.home()
    / ".codex"
    / "secrets"
    / "jlyl-literature-delivery"
    / "credentials.json"
)


def _dpapi_unprotect(encoded: str) -> str:
    if os.name != "nt":
        raise RuntimeError("Windows DPAPI credentials can only be decrypted on Windows")

    class DataBlob(ctypes.Structure):
        _fields_ = [
            ("cbData", wintypes.DWORD),
            ("pbData", ctypes.POINTER(ctypes.c_byte)),
        ]

    encrypted = base64.b64decode(encoded, validate=True)
    input_buffer = ctypes.create_string_buffer(encrypted)
    input_blob = DataBlob(
        len(encrypted),
        ctypes.cast(input_buffer, ctypes.POINTER(ctypes.c_byte)),
    )
    output_blob = DataBlob()
    crypt32 = ctypes.WinDLL("crypt32", use_last_error=True)
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    crypt32.CryptUnprotectData.argtypes = [
        ctypes.POINTER(DataBlob),
        ctypes.POINTER(ctypes.c_wchar_p),
        ctypes.POINTER(DataBlob),
        ctypes.c_void_p,
        ctypes.c_void_p,
        wintypes.DWORD,
        ctypes.POINTER(DataBlob),
    ]
    crypt32.CryptUnprotectData.restype = wintypes.BOOL
    kernel32.LocalFree.argtypes = [ctypes.c_void_p]
    kernel32.LocalFree.restype = ctypes.c_void_p

    if not crypt32.CryptUnprotectData(
        ctypes.byref(input_blob),
        None,
        None,
        None,
        None,
        0,
        ctypes.byref(output_blob),
    ):
        raise OSError(ctypes.get_last_error(), "CryptUnprotectData failed")
    try:
        cleartext = ctypes.string_at(output_blob.pbData, output_blob.cbData)
        return cleartext.decode("utf-8")
    finally:
        kernel32.LocalFree(ctypes.cast(output_blob.pbData, ctypes.c_void_p))


@functools.lru_cache(maxsize=None)
def _secret(name: str) -> str | None:
    environment_value = os.environ.get(name)
    if environment_value:
        return environment_value

    configured_path = os.environ.get("JLYL_CREDENTIALS_FILE")
    credential_path = (
        Path(configured_path).expanduser() if configured_path else DEFAULT_CREDENTIAL_FILE
    )
    if not credential_path.is_file():
        return None
    try:
        payload = json.loads(credential_path.read_text(encoding="utf-8"))
        if payload.get("storage") != "windows-dpapi-current-user":
            return None
        encoded = (payload.get("secrets") or {}).get(name)
        return _dpapi_unprotect(encoded) if encoded else None
    except Exception:
        return None


def _clean_doi(value: str | None) -> str | None:
    if not value:
        return None
    match = DOI_RE.search(urllib.parse.unquote(value))
    if not match:
        return None
    return match.group(0).rstrip(".,;:)]}").lower()


def _normalize_title(value: str | None) -> str:
    if not value:
        return ""
    return "".join(ch.lower() for ch in value if ch.isalnum())


def _year(value: Any) -> int | None:
    match = re.search(r"(?:19|20)\d{2}", str(value or ""))
    return int(match.group(0)) if match else None


def _get_json(
    url: str,
    *,
    params: dict[str, Any] | None = None,
    timeout: float = 20,
    user_agent: str = "Codex-jlyl-literature-delivery/1.0",
) -> dict[str, Any]:
    if params:
        encoded = urllib.parse.urlencode(
            {key: value for key, value in params.items() if value not in (None, "")}
        )
        url = f"{url}{'&' if '?' in url else '?'}{encoded}"
    for attempt in (0, 1):
        request = urllib.request.Request(url, headers={"User-Agent": user_agent})
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            if exc.code == 429 and attempt == 0:
                time.sleep(2)
                continue
            raise RuntimeError(
                f"HTTP {exc.code} from {urllib.parse.urlsplit(url).netloc}"
            ) from exc
        except urllib.error.URLError as exc:
            raise RuntimeError(
                f"Network error from {urllib.parse.urlsplit(url).netloc}: {exc.reason}"
            ) from exc
    raise RuntimeError(f"No response from {urllib.parse.urlsplit(url).netloc}")


def _ncbi_params() -> dict[str, str]:
    params = {"tool": "codex_jlyl_literature_delivery"}
    email = os.environ.get("NCBI_EMAIL")
    api_key = _secret("NCBI_API_KEY")
    if email:
        params["email"] = email
    if api_key:
        params["api_key"] = api_key
    return params


def _article_ids(summary: dict[str, Any]) -> dict[str, str]:
    out: dict[str, str] = {}
    for item in summary.get("articleids") or []:
        kind = str(item.get("idtype") or "").lower()
        value = str(item.get("value") or "").strip()
        if kind and value:
            out[kind] = value
    return out


def _pubmed_record(summary: dict[str, Any], rank: int) -> dict[str, Any]:
    article_ids = _article_ids(summary)
    authors = [
        str(author.get("name") or "").strip()
        for author in (summary.get("authors") or [])[:8]
        if author.get("name")
    ]
    pmid = str(summary.get("uid") or article_ids.get("pubmed") or "").strip() or None
    pmcid = article_ids.get("pmc")
    if pmcid and not pmcid.upper().startswith("PMC"):
        pmcid = f"PMC{pmcid}"
    return {
        "title": str(summary.get("title") or "").rstrip("."),
        "authors": authors,
        "year": _year(summary.get("pubdate") or summary.get("epubdate")),
        "journal": summary.get("fulljournalname") or summary.get("source"),
        "doi": _clean_doi(article_ids.get("doi")),
        "pmid": pmid,
        "pmcid": pmcid,
        "oa_url": f"https://pmc.ncbi.nlm.nih.gov/articles/{pmcid}/" if pmcid else None,
        "retracted": "retract" in str(summary.get("title") or "").lower(),
        "sources": ["pubmed"],
        "source_ranks": {"pubmed": rank},
    }


def search_pubmed(
    query: str, limit: int, since_year: int | None, timeout: float
) -> list[dict[str, Any]]:
    pmid_match = PMID_RE.fullmatch(query.strip())
    pmcid_match = PMCID_RE.fullmatch(query.strip())
    doi = _clean_doi(query)

    if pmid_match:
        ids = [pmid_match.group(1)]
    else:
        if pmcid_match:
            term = f"{pmcid_match.group(1)}[PMCID]"
        elif doi:
            term = f'"{doi}"[DOI]'
        else:
            term = query
            if since_year:
                term += (
                    f' AND ("{since_year}"[Date - Publication] : '
                    '"3000"[Date - Publication])'
                )
        search_params: dict[str, Any] = {
            "db": "pubmed",
            "term": term,
            "retmode": "json",
            "retmax": limit,
            "sort": "relevance",
            **_ncbi_params(),
        }
        data = _get_json(
            "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi",
            params=search_params,
            timeout=timeout,
        )
        ids = list((data.get("esearchresult") or {}).get("idlist") or [])

    if not ids:
        return []

    summary_params: dict[str, Any] = {
        "db": "pubmed",
        "id": ",".join(ids),
        "retmode": "json",
        **_ncbi_params(),
    }
    data = _get_json(
        "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi",
        params=summary_params,
        timeout=timeout,
    )
    result = data.get("result") or {}
    ordered_ids = result.get("uids") or ids
    return [
        _pubmed_record(result[pmid], rank)
        for rank, pmid in enumerate(ordered_ids)
        if isinstance(result.get(pmid), dict)
    ]


def _openalex_record(work: dict[str, Any], rank: int) -> dict[str, Any]:
    authors = []
    for authorship in (work.get("authorships") or [])[:8]:
        author = authorship.get("author") or {}
        if author.get("display_name"):
            authors.append(str(author["display_name"]))
    source = ((work.get("primary_location") or {}).get("source") or {})
    open_access = work.get("open_access") or {}
    ids = work.get("ids") or {}

    def trailing_id(value: Any, prefix: str) -> str | None:
        text = str(value or "")
        match = re.search(prefix + r"\d+", text, re.IGNORECASE)
        return match.group(0).upper() if match else None

    pmid_text = str(ids.get("pmid") or "")
    pmid_match = re.search(r"(\d{1,10})/?$", pmid_text)
    pmid = pmid_match.group(1) if pmid_match else None
    return {
        "title": work.get("title") or work.get("display_name"),
        "authors": authors,
        "year": work.get("publication_year"),
        "journal": source.get("display_name"),
        "doi": _clean_doi(work.get("doi") or ids.get("doi")),
        "pmid": pmid,
        "pmcid": trailing_id(ids.get("pmcid"), "PMC"),
        "oa_url": open_access.get("oa_url"),
        "cited_by": work.get("cited_by_count"),
        "retracted": bool(work.get("is_retracted")),
        "sources": ["openalex"],
        "source_ranks": {"openalex": rank},
    }


def search_openalex(
    query: str, limit: int, since_year: int | None, timeout: float
) -> list[dict[str, Any]]:
    params: dict[str, Any] = {
        "search": query,
        "per-page": min(limit, 25),
    }
    if since_year:
        params["filter"] = f"from_publication_date:{since_year}-01-01"
    email = os.environ.get("OPENALEX_EMAIL")
    api_key = _secret("OPENALEX_API_KEY")
    if email:
        params["mailto"] = email
    if api_key:
        params["api_key"] = api_key
    data = _get_json("https://api.openalex.org/works", params=params, timeout=timeout)
    return [
        _openalex_record(work, rank)
        for rank, work in enumerate((data.get("results") or [])[:limit])
    ]


def _crossref_year(message: dict[str, Any]) -> int | None:
    for key in (
        "published",
        "published-print",
        "published-online",
        "issued",
        "created",
    ):
        parts = ((message.get(key) or {}).get("date-parts") or [])
        if parts and parts[0]:
            return _year(parts[0][0])
    return None


def _crossref_record(message: dict[str, Any], rank: int) -> dict[str, Any]:
    titles = message.get("title") or []
    authors = []
    for author in (message.get("author") or [])[:8]:
        name = " ".join(
            part
            for part in (
                str(author.get("given") or "").strip(),
                str(author.get("family") or "").strip(),
            )
            if part
        )
        if name:
            authors.append(name)
    update_types = [
        str(item.get("type") or "").lower()
        for item in (message.get("update-to") or [])
    ]
    title = str(titles[0] if titles else "")
    return {
        "title": title,
        "authors": authors,
        "year": _crossref_year(message),
        "journal": (message.get("container-title") or [None])[0],
        "doi": _clean_doi(message.get("DOI")),
        "pmid": None,
        "pmcid": None,
        "oa_url": None,
        "crossref_score": message.get("score"),
        "retracted": any("retract" in item for item in update_types)
        or title.upper().startswith("RETRACTED"),
        "sources": ["crossref"],
        "source_ranks": {"crossref": rank},
    }


def search_crossref(
    query: str, limit: int, since_year: int | None, timeout: float
) -> list[dict[str, Any]]:
    doi = _clean_doi(query)
    email = os.environ.get("CROSSREF_EMAIL") or os.environ.get("NCBI_EMAIL")
    user_agent = "Codex-jlyl-literature-delivery/1.0" + (
        f" (mailto:{email})" if email else ""
    )
    if doi:
        encoded = "/".join(
            urllib.parse.quote(part, safe="") for part in doi.split("/")
        )
        data = _get_json(
            f"https://api.crossref.org/works/{encoded}",
            timeout=timeout,
            user_agent=user_agent,
        )
        message = data.get("message")
        return [_crossref_record(message, 0)] if isinstance(message, dict) else []

    params: dict[str, Any] = {"query.bibliographic": query, "rows": limit}
    if since_year:
        params["filter"] = f"from-pub-date:{since_year}-01-01"
    if email:
        params["mailto"] = email
    data = _get_json(
        "https://api.crossref.org/works",
        params=params,
        timeout=timeout,
        user_agent=user_agent,
    )
    items = ((data.get("message") or {}).get("items") or [])[:limit]
    return [_crossref_record(item, rank) for rank, item in enumerate(items)]


def _same_record(left: dict[str, Any], right: dict[str, Any]) -> bool:
    if left.get("doi") and right.get("doi") and left["doi"] == right["doi"]:
        return True
    if (
        left.get("pmid")
        and right.get("pmid")
        and str(left["pmid"]) == str(right["pmid"])
    ):
        return True
    left_title = _normalize_title(left.get("title"))
    right_title = _normalize_title(right.get("title"))
    return bool(left_title and right_title and left_title == right_title)


def _merge_into(target: dict[str, Any], incoming: dict[str, Any]) -> None:
    for field in (
        "title",
        "authors",
        "year",
        "journal",
        "doi",
        "pmid",
        "pmcid",
        "oa_url",
    ):
        if not target.get(field) and incoming.get(field):
            target[field] = incoming[field]
    target["retracted"] = bool(
        target.get("retracted") or incoming.get("retracted")
    )
    for numeric in ("cited_by", "crossref_score"):
        values = [
            value
            for value in (target.get(numeric), incoming.get(numeric))
            if isinstance(value, (int, float))
        ]
        if values:
            target[numeric] = max(values)
    target["sources"] = sorted(
        set(target.get("sources") or []) | set(incoming.get("sources") or [])
    )
    target.setdefault("source_ranks", {}).update(incoming.get("source_ranks") or {})


def _deduplicate(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    merged: list[dict[str, Any]] = []
    for record in records:
        existing = next((item for item in merged if _same_record(item, record)), None)
        if existing is None:
            merged.append(record)
        else:
            _merge_into(existing, record)
    return merged


def _delivery_identifier(record: dict[str, Any]) -> str | None:
    if record.get("doi"):
        return f"DOI:{record['doi']}"
    if record.get("pmid"):
        return f"PMID:{record['pmid']}"
    if record.get("pmcid"):
        return f"PMCID:{record['pmcid']}"
    if record.get("title"):
        return str(record["title"])
    return None


def _matches_identifier(record: dict[str, Any], query: str) -> bool:
    query_doi = _clean_doi(query)
    if query_doi:
        return record.get("doi") == query_doi
    pmid_match = PMID_RE.fullmatch(query.strip())
    if pmid_match:
        return str(record.get("pmid") or "") == pmid_match.group(1)
    pmcid_match = PMCID_RE.fullmatch(query.strip())
    if pmcid_match:
        return (
            str(record.get("pmcid") or "").upper()
            == pmcid_match.group(1).upper()
        )
    return False


def _score(record: dict[str, Any], query: str) -> float:
    score = 0.0
    query_doi = _clean_doi(query)
    pmid_match = PMID_RE.fullmatch(query.strip())
    pmcid_match = PMCID_RE.fullmatch(query.strip())
    if query_doi and record.get("doi") == query_doi:
        score += 1000
    if pmid_match and str(record.get("pmid") or "") == pmid_match.group(1):
        score += 1000
    if (
        pmcid_match
        and str(record.get("pmcid") or "").upper()
        == pmcid_match.group(1).upper()
    ):
        score += 1000
    if _normalize_title(record.get("title")) == _normalize_title(query):
        score += 500
    weights = {"pubmed": 90, "openalex": 70, "crossref": 60}
    for source, rank in (record.get("source_ranks") or {}).items():
        score += max(0, weights.get(source, 40) - int(rank))
    if record.get("doi"):
        score += 12
    if record.get("pmid"):
        score += 10
    if record.get("oa_url"):
        score += 5
    cited_by = record.get("cited_by")
    if isinstance(cited_by, (int, float)) and cited_by > 0:
        score += min(20, math.log10(cited_by + 1) * 5)
    crossref_score = record.get("crossref_score")
    if isinstance(crossref_score, (int, float)):
        score += min(25, crossref_score / 5)
    if record.get("retracted"):
        score -= 2000
    return round(score, 3)


def _selection(results: list[dict[str, Any]], query: str) -> dict[str, Any]:
    if not results:
        return {
            "status": "not_found",
            "recommended_index": None,
            "reason": "No live result was retrieved.",
        }
    identifier_query = bool(
        _clean_doi(query)
        or PMID_RE.fullmatch(query.strip())
        or PMCID_RE.fullmatch(query.strip())
    )
    exact_title = _normalize_title(results[0].get("title")) == _normalize_title(query)
    if identifier_query and _matches_identifier(results[0], query):
        return {
            "status": "auto",
            "recommended_index": 1,
            "reason": "The supplied stable identifier was resolved.",
        }
    if exact_title:
        return {
            "status": "auto",
            "recommended_index": 1,
            "reason": "A unique exact-title match ranked first.",
        }
    return {
        "status": "needs_user_choice",
        "recommended_index": 1,
        "reason": (
            "Topical or approximate-title queries can match multiple papers; "
            "show candidates to the user."
        ),
    }


def run_lookup(
    query: str,
    sources: list[str],
    limit: int,
    since_year: int | None,
    timeout: float,
) -> dict[str, Any]:
    records: list[dict[str, Any]] = []
    errors: list[dict[str, str]] = []
    lookup_functions = {
        "pubmed": search_pubmed,
        "openalex": search_openalex,
        "crossref": search_crossref,
    }
    for source in sources:
        try:
            records.extend(
                lookup_functions[source](query, limit, since_year, timeout)
            )
        except Exception as exc:  # source failure should not erase other live results
            errors.append({"source": source, "error": str(exc)})
    results = _deduplicate(records)
    if _clean_doi(query) or PMID_RE.fullmatch(query.strip()) or PMCID_RE.fullmatch(
        query.strip()
    ):
        results = [record for record in results if _matches_identifier(record, query)]
    for result in results:
        result["score"] = _score(result, query)
        result["delivery_identifier"] = _delivery_identifier(result)
    results.sort(key=lambda item: item.get("score", 0), reverse=True)
    results = results[:limit]
    for index, result in enumerate(results, start=1):
        result["index"] = index
    return {
        "query": query,
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "sources_requested": sources,
        "api_key_usage": {
            "ncbi": bool(_secret("NCBI_API_KEY")),
            "openalex": bool(_secret("OPENALEX_API_KEY")),
        },
        "selection": _selection(results, query),
        "results": results,
        "errors": errors,
    }


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Search PubMed, OpenAlex, and Crossref for deliverable literature "
            "identifiers."
        )
    )
    parser.add_argument(
        "query", help="DOI, PMID, PMCID, title, topic, or short description"
    )
    parser.add_argument(
        "--limit", type=int, default=8, help="maximum merged results (1-25)"
    )
    parser.add_argument(
        "--since-year", type=int, help="restrict to this publication year or later"
    )
    parser.add_argument(
        "--sources",
        default="pubmed,openalex,crossref",
        help="comma-separated subset of pubmed,openalex,crossref",
    )
    parser.add_argument(
        "--timeout", type=float, default=20, help="per-request timeout in seconds"
    )
    parser.add_argument("--output", help="optional JSON output path")
    parser.add_argument("--compact", action="store_true", help="emit compact JSON")
    args = parser.parse_args(argv)
    if not 1 <= args.limit <= 25:
        parser.error("--limit must be between 1 and 25")
    if args.since_year and not 1800 <= args.since_year <= 3000:
        parser.error("--since-year must be between 1800 and 3000")
    if len(args.query) > 2000:
        parser.error("query must be 2000 characters or fewer")
    sources = [
        item.strip().lower() for item in args.sources.split(",") if item.strip()
    ]
    unknown = sorted(set(sources) - {"pubmed", "openalex", "crossref"})
    if not sources or unknown:
        parser.error(
            "invalid --sources value; unknown sources: "
            + (", ".join(unknown) or "none selected")
        )
    args.sources = list(dict.fromkeys(sources))
    return args


def main(argv: list[str] | None = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    args = parse_args(argv or sys.argv[1:])
    payload = run_lookup(
        args.query.strip(), args.sources, args.limit, args.since_year, args.timeout
    )
    rendered = json.dumps(
        payload, ensure_ascii=False, indent=None if args.compact else 2
    )
    if args.output:
        output_path = Path(args.output).expanduser().resolve()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(rendered + "\n", encoding="utf-8")
    print(rendered)
    return 0 if payload["results"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
