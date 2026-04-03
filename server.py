"""MCP server for the KCSC OpenAPI."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
import html
import json
import logging
import os
import re
import ssl
from time import monotonic
from typing import Any

import httpx
from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel, ConfigDict, Field, field_validator

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover - optional during bootstrap
    load_dotenv = None

try:
    import truststore
except ImportError:  # pragma: no cover - optional during bootstrap
    truststore = None


if load_dotenv is not None:
    load_dotenv()


BASE_URL = "https://kcsc.re.kr/OpenApi"
TIMEOUT = 30.0
VALID_CODE_TYPES = {"KCS", "KDS"}
FALSE_VALUES = {"0", "false", "no", "off"}
CACHE_TTL_SECONDS = float(os.environ.get("KCSC_CACHE_TTL_SECONDS", "600"))

logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)

mcp = FastMCP("kcsc_mcp")


@dataclass
class CacheEntry:
    value: Any
    expires_at: float


_CODE_LIST_CACHE: CacheEntry | None = None
_CONTENT_CACHE: dict[tuple[str, str], CacheEntry] = {}


def _client() -> httpx.AsyncClient:
    return httpx.AsyncClient(timeout=TIMEOUT, verify=_ssl_verify_config())


def _key() -> str:
    api_key = os.environ.get("KCSC_API_KEY", "").strip()
    if not api_key:
        raise ValueError(
            "KCSC_API_KEY environment variable is not set. "
            "Get your key at https://www.kcsc.re.kr/support/api"
        )
    return api_key


def _normalize_code_type(value: str | None) -> str | None:
    if value is None:
        return None

    normalized = value.upper()
    if normalized not in VALID_CODE_TYPES:
        raise ValueError("code_type must be either 'KCS' or 'KDS'")
    return normalized


def _handle_error(error: Exception) -> str:
    if isinstance(error, httpx.HTTPStatusError):
        if error.response.status_code == 401:
            return "Error: Invalid API key. Check KCSC_API_KEY."
        if error.response.status_code == 429:
            return "Error: Rate limit exceeded. Please wait."
        return f"Error: HTTP {error.response.status_code}"

    if isinstance(error, httpx.TimeoutException):
        return "Error: Request timed out."

    if isinstance(error, ValueError):
        return f"Error: {error}"

    return f"Error: {type(error).__name__}: {error}"


def _ssl_verify_config() -> bool | str | ssl.SSLContext:
    ca_bundle = os.environ.get("KCSC_CA_BUNDLE", "").strip()
    if ca_bundle:
        return ca_bundle

    verify_ssl = os.environ.get("KCSC_VERIFY_SSL", "true").strip().lower()
    if verify_ssl in FALSE_VALUES:
        return False

    if truststore is not None:
        return truststore.SSLContext(ssl.PROTOCOL_TLS_CLIENT)

    return True


def _strip_html(text: str) -> str:
    plain_text = re.sub(r"<[^>]+>", " ", text or "")
    plain_text = html.unescape(plain_text).replace("\xa0", " ")
    return re.sub(r"\s+", " ", plain_text).strip()


def _to_json(payload: Any) -> str:
    return json.dumps(payload, ensure_ascii=False, indent=2)


def _cache_get(entry: CacheEntry | None) -> Any | None:
    if entry is None or entry.expires_at <= monotonic():
        return None
    return deepcopy(entry.value)


def _cache_set(value: Any) -> CacheEntry:
    return CacheEntry(value=deepcopy(value), expires_at=monotonic() + CACHE_TTL_SECONDS)


def _summarize_code(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "no": item.get("no"),
        "codeType": item.get("codeType"),
        "code": item.get("code"),
        "fullCode": item.get("fullCode"),
        "name": item.get("name"),
        "version": item.get("version"),
        "updateDate": item.get("updateDate"),
    }


def _normalize_code_identifier(value: str) -> str:
    normalized = value.strip()
    if not re.fullmatch(r"\d{6,}", normalized):
        raise ValueError("code must be numeric and at least 6 digits long")
    return normalized


def _serialize_sections(sections: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "sort": section.get("sort"),
            "level": section.get("level"),
            "label": section.get("label"),
            "title": section.get("title"),
            "contents": section.get("contents"),
        }
        for section in sections
    ]


def _prepare_document(document: dict[str, Any], plain_text: bool) -> dict[str, Any]:
    prepared = deepcopy(document)
    sections = prepared.get("list") or []

    if plain_text:
        for section in sections:
            section["contents"] = _strip_html(section.get("contents", ""))

    return {
        "no": prepared.get("no"),
        "codeType": prepared.get("codeType"),
        "code": prepared.get("code"),
        "fullCode": prepared.get("fullCode"),
        "name": prepared.get("name"),
        "version": prepared.get("version"),
        "updateDate": prepared.get("updateDate"),
        "sections": _serialize_sections(sections),
    }


def _preview_match(text: str, keyword: str, context_chars: int) -> str:
    if not text:
        return ""

    normalized_text = re.sub(r"\s+", " ", text).strip()
    if not normalized_text:
        return ""

    lower_text = normalized_text.lower()
    lower_keyword = keyword.lower()
    index = lower_text.find(lower_keyword)

    if index < 0:
        return normalized_text[:context_chars].strip()

    start = max(0, index - context_chars // 2)
    end = min(len(normalized_text), index + len(keyword) + context_chars // 2)
    snippet = normalized_text[start:end].strip()

    if start > 0:
        snippet = f"... {snippet}"
    if end < len(normalized_text):
        snippet = f"{snippet} ..."

    return snippet


def _search_sections(
    *,
    sections: list[dict[str, Any]],
    keyword: str,
    context_chars: int,
    include_full_contents: bool,
) -> list[dict[str, Any]]:
    keyword_lower = keyword.lower()
    matches: list[dict[str, Any]] = []

    for section in sections:
        title = section.get("title") or ""
        contents = section.get("contents") or ""
        title_hit = keyword_lower in title.lower()
        contents_hit = keyword_lower in contents.lower()

        if not title_hit and not contents_hit:
            continue

        preview_source = contents if contents_hit else title
        item = {
            "sort": section.get("sort"),
            "level": section.get("level"),
            "label": section.get("label"),
            "title": title,
            "matchedIn": ["title"] * int(title_hit) + ["contents"] * int(contents_hit),
            "preview": _preview_match(preview_source, keyword, context_chars),
        }

        if include_full_contents:
            item["contents"] = contents

        matches.append(item)

    return matches


async def _fetch_code_list(client: httpx.AsyncClient) -> list[dict[str, Any]]:
    global _CODE_LIST_CACHE

    cached = _cache_get(_CODE_LIST_CACHE)
    if cached is not None:
        return cached

    response = await client.get(f"{BASE_URL}/CodeList", params={"key": _key()})
    response.raise_for_status()
    payload = response.json()
    _CODE_LIST_CACHE = _cache_set(payload)
    return deepcopy(payload)


async def _fetch_content_document(
    client: httpx.AsyncClient,
    *,
    code_type: str,
    code: str,
) -> dict[str, Any]:
    cache_key = (code_type, code)
    cached = _cache_get(_CONTENT_CACHE.get(cache_key))
    if cached is not None:
        return cached

    response = await client.get(
        f"{BASE_URL}/CodeViewer/{code_type}/{code}",
        params={"key": _key()},
    )
    response.raise_for_status()
    data = response.json()

    if not data:
        raise ValueError(f"No data found for {code_type} {code}")

    document = data[0] if isinstance(data, list) else data
    _CONTENT_CACHE[cache_key] = _cache_set(document)
    return deepcopy(document)


async def _resolve_code_identifier(
    client: httpx.AsyncClient,
    *,
    code_type: str,
    code_identifier: str,
) -> dict[str, Any]:
    if len(code_identifier) == 6:
        code_list = await _fetch_code_list(client)
        for item in code_list:
            if item.get("codeType") == code_type and item.get("code") == code_identifier:
                return item
        raise ValueError(f"No code found for {code_type} {code_identifier}")

    code_list = await _fetch_code_list(client)
    for item in code_list:
        if item.get("codeType") == code_type and item.get("fullCode") == code_identifier:
            return item

    raise ValueError(f"No fullCode found for {code_type} {code_identifier}")


class ListCodesInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    code_type: str | None = Field(
        default=None,
        description="Optional filter. Use 'KCS' or 'KDS'.",
    )
    keyword: str | None = Field(
        default=None,
        description="Optional keyword to match against the code name.",
    )
    limit: int = Field(
        default=50,
        ge=1,
        le=500,
        description="Maximum number of items to return.",
    )
    offset: int = Field(default=0, ge=0, description="Pagination offset.")

    @field_validator("code_type")
    @classmethod
    def validate_code_type(cls, value: str | None) -> str | None:
        return _normalize_code_type(value)


class GetContentInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    code_type: str = Field(..., description="Code type. Use 'KCS' or 'KDS'.")
    code: str = Field(
        ...,
        description="Six-digit code or eight-digit fullCode.",
    )
    plain_text: bool = Field(
        default=True,
        description="When true, remove HTML tags from section content.",
    )

    @field_validator("code_type")
    @classmethod
    def validate_code_type(cls, value: str) -> str:
        normalized = _normalize_code_type(value)
        assert normalized is not None
        return normalized

    @field_validator("code")
    @classmethod
    def validate_code(cls, value: str) -> str:
        return _normalize_code_identifier(value)


class SearchInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    keyword: str = Field(
        ...,
        min_length=1,
        description="Keyword to search in the code name.",
    )
    code_type: str | None = Field(
        default=None,
        description="Optional filter. Use 'KCS' or 'KDS'.",
    )
    limit: int = Field(default=20, ge=1, le=100, description="Maximum results.")

    @field_validator("code_type")
    @classmethod
    def validate_code_type(cls, value: str | None) -> str | None:
        return _normalize_code_type(value)


class SearchSectionsInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    code_type: str = Field(..., description="Code type. Use 'KCS' or 'KDS'.")
    code: str = Field(
        ...,
        description="Six-digit code or eight-digit fullCode.",
    )
    keyword: str = Field(
        ...,
        min_length=1,
        description="Keyword to search in section titles and contents.",
    )
    limit: int = Field(default=10, ge=1, le=100, description="Maximum results.")
    context_chars: int = Field(
        default=180,
        ge=40,
        le=1000,
        description="Approximate preview length around the match.",
    )
    plain_text: bool = Field(
        default=True,
        description="When true, remove HTML tags before searching.",
    )
    include_full_contents: bool = Field(
        default=False,
        description="When true, include the full section contents in results.",
    )

    @field_validator("code_type")
    @classmethod
    def validate_code_type(cls, value: str) -> str:
        normalized = _normalize_code_type(value)
        assert normalized is not None
        return normalized

    @field_validator("code")
    @classmethod
    def validate_code(cls, value: str) -> str:
        return _normalize_code_identifier(value)


@mcp.tool(
    name="kcsc_list_codes",
    annotations={
        "title": "List Construction Standard Codes",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
async def kcsc_list_codes(params: ListCodesInput) -> str:
    """List available KCSC codes with optional filtering and pagination."""
    try:
        async with _client() as client:
            filtered = await _fetch_code_list(client)

        if params.code_type:
            filtered = [item for item in filtered if item.get("codeType") == params.code_type]

        if params.keyword:
            keyword = params.keyword.lower()
            filtered = [
                item
                for item in filtered
                if keyword in (item.get("name") or "").lower()
            ]

        total = len(filtered)
        page = filtered[params.offset : params.offset + params.limit]

        return _to_json(
            {
                "total": total,
                "count": len(page),
                "offset": params.offset,
                "has_more": total > params.offset + len(page),
                "items": [_summarize_code(item) for item in page],
            }
        )
    except Exception as error:  # pragma: no cover - exercised through tool runtime
        return _handle_error(error)


@mcp.tool(
    name="kcsc_get_content",
    annotations={
        "title": "Get Standard Content",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
async def kcsc_get_content(params: GetContentInput) -> str:
    """Fetch the full document content for a specific KCS or KDS code."""
    try:
        async with _client() as client:
            code_item = await _resolve_code_identifier(
                client,
                code_type=params.code_type,
                code_identifier=params.code,
            )
            document = await _fetch_content_document(
                client,
                code_type=params.code_type,
                code=code_item["code"],
            )

        prepared = _prepare_document(document, plain_text=params.plain_text)
        prepared["requestedCode"] = params.code
        return _to_json(prepared)
    except Exception as error:  # pragma: no cover - exercised through tool runtime
        return _handle_error(error)


@mcp.tool(
    name="kcsc_search_codes",
    annotations={
        "title": "Search Construction Standard Codes",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
async def kcsc_search_codes(params: SearchInput) -> str:
    """Search KCSC codes by keyword."""
    try:
        async with _client() as client:
            filtered = await _fetch_code_list(client)

        keyword = params.keyword.lower()
        filtered = [
            item
            for item in filtered
            if keyword in (item.get("name") or "").lower()
        ]

        if params.code_type:
            filtered = [item for item in filtered if item.get("codeType") == params.code_type]

        return _to_json(
            {
                "keyword": params.keyword,
                "total": len(filtered),
                "items": [
                    {
                        "codeType": item.get("codeType"),
                        "code": item.get("code"),
                        "fullCode": item.get("fullCode"),
                        "name": item.get("name"),
                        "version": item.get("version"),
                        "updateDate": item.get("updateDate"),
                    }
                    for item in filtered[: params.limit]
                ],
            }
        )
    except Exception as error:  # pragma: no cover - exercised through tool runtime
        return _handle_error(error)


@mcp.tool(
    name="kcsc_search_sections",
    annotations={
        "title": "Search Sections Inside a Standard",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
async def kcsc_search_sections(params: SearchSectionsInput) -> str:
    """Search titles and contents inside a single KCSC document."""
    try:
        async with _client() as client:
            code_item = await _resolve_code_identifier(
                client,
                code_type=params.code_type,
                code_identifier=params.code,
            )
            document = await _fetch_content_document(
                client,
                code_type=params.code_type,
                code=code_item["code"],
            )

        prepared = _prepare_document(document, plain_text=params.plain_text)
        matches = _search_sections(
            sections=prepared["sections"],
            keyword=params.keyword,
            context_chars=params.context_chars,
            include_full_contents=params.include_full_contents,
        )

        return _to_json(
            {
                "keyword": params.keyword,
                "total": len(matches),
                "count": min(len(matches), params.limit),
                "document": {
                    "codeType": prepared["codeType"],
                    "requestedCode": params.code,
                    "code": prepared["code"],
                    "fullCode": prepared["fullCode"],
                    "name": prepared["name"],
                    "version": prepared["version"],
                    "updateDate": prepared["updateDate"],
                },
                "items": matches[: params.limit],
            }
        )
    except Exception as error:  # pragma: no cover - exercised through tool runtime
        return _handle_error(error)


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
