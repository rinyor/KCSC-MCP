import httpx
import pytest

import server


def test_normalize_code_type_accepts_lowercase() -> None:
    assert server._normalize_code_type("kcs") == "KCS"
    assert server._normalize_code_type("kds") == "KDS"


def test_normalize_code_type_rejects_unknown_value() -> None:
    with pytest.raises(ValueError):
        server._normalize_code_type("abc")


def test_strip_html_removes_tags_and_entities() -> None:
    raw = "<p>Hello&nbsp;<strong>world</strong></p>"
    assert server._strip_html(raw) == "Hello world"


def test_handle_error_returns_readable_http_message() -> None:
    request = httpx.Request("GET", "https://example.com")
    response = httpx.Response(401, request=request)
    error = httpx.HTTPStatusError("unauthorized", request=request, response=response)
    assert server._handle_error(error) == "Error: Invalid API key. Check KCSC_API_KEY."


def test_preview_match_focuses_on_keyword_context() -> None:
    text = "0123456789 important keyword lives here and continues afterward"
    preview = server._preview_match(text, "keyword", 30)
    assert "keyword" in preview
    assert len(preview) <= 50


def test_search_sections_returns_title_and_content_hits() -> None:
    sections = [
        {
            "sort": 1,
            "level": 1,
            "label": "1",
            "title": "General concrete rules",
            "contents": "This section explains materials.",
        },
        {
            "sort": 2,
            "level": 1,
            "label": "2",
            "title": "Materials",
            "contents": "Concrete curing keyword appears here.",
        },
    ]

    matches = server._search_sections(
        sections=sections,
        keyword="keyword",
        context_chars=80,
        include_full_contents=False,
    )

    assert len(matches) == 1
    assert matches[0]["matchedIn"] == ["contents"]
    assert "keyword" in matches[0]["preview"].lower()


def test_prepare_document_keeps_cached_source_immutable() -> None:
    document = {
        "codeType": "KCS",
        "code": "114010",
        "fullCode": "11401000",
        "name": "Sample",
        "version": "2024",
        "updateDate": "2024-01-01T00:00:00",
        "list": [
            {
                "sort": 1,
                "level": 1,
                "label": "1",
                "title": "Intro",
                "contents": "<p>Hello <strong>world</strong></p>",
            }
        ],
    }

    prepared = server._prepare_document(document, plain_text=True)

    assert prepared["sections"][0]["contents"] == "Hello world"
    assert document["list"][0]["contents"] == "<p>Hello <strong>world</strong></p>"


def test_normalize_code_identifier_accepts_code_and_full_code() -> None:
    assert server._normalize_code_identifier("114010") == "114010"
    assert server._normalize_code_identifier("2010114010") == "2010114010"


def test_normalize_code_identifier_rejects_invalid_value() -> None:
    with pytest.raises(ValueError):
        server._normalize_code_identifier("1140A0")


@pytest.mark.anyio
async def test_resolve_code_identifier_accepts_full_code(monkeypatch: pytest.MonkeyPatch) -> None:
    async def fake_fetch_code_list(client: httpx.AsyncClient) -> list[dict[str, str]]:
        return [
            {
                "codeType": "KCS",
                "code": "114010",
                "fullCode": "11401000",
                "name": "Sample",
            }
        ]

    monkeypatch.setattr(server, "_fetch_code_list", fake_fetch_code_list)

    resolved = await server._resolve_code_identifier(
        client=httpx.AsyncClient(),
        code_type="KCS",
        code_identifier="11401000",
    )

    assert resolved["code"] == "114010"
    assert resolved["fullCode"] == "11401000"
