# KCSC MCP Server

**국가건설기준(KCS/KDS)을 AI 대화 안에서 바로 검색하고 읽습니다**
**Search and read Korean Construction Standards (KCS/KDS) directly within AI conversations**

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/Python-3.11+-green.svg)](https://python.org)
[![MCP](https://img.shields.io/badge/MCP-1.0-orange.svg)](https://modelcontextprotocol.io)

---

## 소개 | Introduction

KCSC MCP Server는 국가건설기준센터(KCSC) OpenAPI를 MCP 서버로 감싸서, Claude Desktop/Claude Code/Codex 등 AI 클라이언트 안에서 KCS(건설기준)와 KDS(설계기준)를 바로 검색하고, 본문을 읽고, 특정 조항을 찾을 수 있게 합니다.

KCSC MCP Server wraps the Korean Construction Standard Center (KCSC) OpenAPI as an MCP server, enabling AI clients like Claude Desktop, Claude Code, and Codex to search, read, and navigate KCS (Construction Standards) and KDS (Design Standards) documents directly.

> 브라우저를 열고, 키워드를 바꾸고, 페이지를 넘기는 대신 -- AI에게 물어보세요.
> Instead of opening a browser, changing keywords, and flipping pages -- just ask your AI.

---

## 이런 분들에게 유용합니다 | Who Is This For?

| 대상 | 활용 예시 |
|------|----------|
| **건설 엔지니어** | 설계 검토 중 KDS 기준 조항을 즉시 확인 |
| **시공 관리자** | KCS 시공 기준 본문을 AI 대화 안에서 바로 조회 |
| **건축사/감리원** | 관련 기준 문서를 키워드로 빠르게 검색 |
| **공무원** | 사업 기획 시 적용 기준 확인 |
| **학생/연구자** | 건설기준 학습 및 조항 검색 |

| Who | Use Case |
|-----|----------|
| **Civil engineers** | Instantly check KDS design standard clauses during review |
| **Construction managers** | Query KCS construction standards within AI conversations |
| **Architects / Supervisors** | Search related standard documents by keyword |
| **Government officials** | Verify applicable standards during project planning |
| **Students & researchers** | Study and search construction standard clauses |

---

## 제공 도구 | Available Tools

| # | 도구 Tool | 설명 Description |
|---|-----------|-----------------|
| 1 | `kcsc_list_codes` | KCS/KDS 코드 목록 조회 (타입, 키워드, 페이지네이션) / List codes with filtering |
| 2 | `kcsc_search_codes` | 코드명 기반 빠른 검색 / Quick search by code name |
| 3 | `kcsc_get_content` | 특정 문서 전체 본문 조회 (HTML 제거 옵션) / Get full document content |
| 4 | `kcsc_search_sections` | 문서 내부 제목/본문 키워드 검색 / Search sections within a document |

---

## 빠른 시작 가이드 | Quick Start Guide

### 1단계: 설치 | Step 1: Install

```bash
git clone https://github.com/sinmb79/KCSC-MCP.git     ---->github에서 git을 다운로드 설치함
cd KCSC-MCP

python -m venv .venv     ---->pythun이 안되면 py로 다시 실행 함

# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

# 설치 | Install
pip install -e ".[dev]"
```

### 2단계: API 키 설정 | Step 2: Configure API Key

KCSC API 키를 [https://www.kcsc.re.kr/support/api](https://www.kcsc.re.kr/support/api)에서 발급받으세요.

Get your API key from [https://www.kcsc.re.kr/support/api](https://www.kcsc.re.kr/support/api).

```bash
# Windows:
copy .env.example .env
# macOS/Linux:
cp .env.example .env
```

`.env` 파일을 편집합니다:

```env
KCSC_API_KEY=your_real_kcsc_api_key
```

### 3단계: 서버 실행 | Step 3: Start Server

```bash
# 방법 1: Python 직접 실행
python server.py

# 방법 2: 설치된 스크립트
kcsc-mcp
```

### 4단계: AI 클라이언트 연결 | Step 4: Connect AI Client

#### Claude Desktop

`%AppData%\Claude\claude_desktop_config.json` (Windows):

```json
{
  "mcpServers": {
    "kcsc": {
      "command": "D:/Workspace/KCSC-MCP/.venv/Scripts/python.exe",
      "args": ["D:/Workspace/KCSC-MCP/server.py"],
      "env": {
        "KCSC_API_KEY": "your_kcsc_api_key"
      }
    }
  }
}
```

#### Claude Code

```bash
claude mcp add --transport stdio kcsc -- python server.py
```

#### Codex

```bash
codex mcp add kcsc -- python server.py
```

---

## 실전 사용 예시 | Real-World Usage Examples

### 추천 사용 흐름 | Recommended Workflow

가장 효율적인 순서입니다. 처음부터 본문을 열지 마세요.

The most efficient order. Don't open full content first.

```
1. kcsc_search_codes  -->  관련 문서 후보 찾기
2. kcsc_list_codes    -->  범위 좁히기 (필요 시)
3. kcsc_search_sections --> 문서 내부에서 필요한 조항 확인
4. kcsc_get_content   -->  전체 문맥 읽기
```

### 예시 1: 콘크리트 관련 기준 찾기 | Example 1: Find Concrete Standards

**AI에게 이렇게 말하세요 | Say this:**
```
콘크리트 관련 KCS 기준을 찾아줘
```

**AI가 호출하는 도구 | Tool called:**
```python
kcsc_search_codes(keyword="콘크리트", code_type="KCS")
```

**결과 예시 | Example result:**
```json
[
  {"code": "114010", "fullCode": "2010114010", "codeName": "콘크리트 공사 일반"},
  {"code": "114020", "fullCode": "2010114020", "codeName": "콘크리트 배합"},
  {"code": "114030", "fullCode": "2010114030", "codeName": "콘크리트 타설"}
]
```

### 예시 2: 문서 내부 조항 검색 | Example 2: Search Within a Document

```
콘크리트 공사 일반 기준에서 거푸집 관련 내용을 찾아줘
```

```python
kcsc_search_sections(code_type="KCS", code="114010", keyword="거푸집", limit=5)
```

문서 전체를 읽지 않고도, 해당 키워드가 등장하는 제목과 본문 단락만 빠르게 확인할 수 있습니다.

### 예시 3: 기준 문서 본문 조회 | Example 3: Read Full Document

```
KCS 114010 전문을 보여줘
```

```python
kcsc_get_content(code_type="KCS", code="114010", plain_text=True)
```

`plain_text=True`로 설정하면 HTML 태그가 제거된 깨끗한 텍스트를 받습니다.

### 예시 4: 도로 설계기준 목록 조회 | Example 4: List Road Design Standards

```
도로 관련 KDS 기준 목록을 보여줘
```

```python
kcsc_list_codes(code_type="KDS", keyword="도로", limit=20)
```

---

## code와 fullCode | About `code` vs `fullCode`

KCSC API 응답에는 `code`(6자리)와 `fullCode`(10자리)가 함께 나옵니다:

| 필드 | 예시 | 설명 |
|------|------|------|
| `code` | `114010` | 문서 본문 조회에 사용하는 6자리 코드 |
| `fullCode` | `2010114010` | 목록에서 보이는 10자리 전체 코드 |

이 서버에서는 **둘 다** 입력으로 받을 수 있습니다. 내부적으로 적절한 코드로 변환하여 API를 호출합니다.

Both `code` and `fullCode` are accepted as input. The server normalizes them internally.

---

## 캐시 | Caching

반복 호출을 줄이기 위해 메모리 캐시를 사용합니다.

| 항목 Item | 설명 Description |
|----------|-----------------|
| 코드 목록 | 전체 코드 목록 캐시 |
| 문서 본문 | 문서별 본문 캐시 |
| 기본 TTL | 600초 (10분) |

```env
# 캐시 TTL 조정 (초) | Adjust cache TTL (seconds)
KCSC_CACHE_TTL_SECONDS=600
```

---

## SSL/네트워크 설정 | SSL/Network Configuration

일부 Windows/사내망 환경에서 SSL 인증서 문제가 발생할 수 있습니다.

SSL certificate issues may occur in some Windows/corporate network environments.

**검증 우선순위 | Verification priority:**

| 순위 | 방법 | 설정 |
|------|------|------|
| 1 (권장) | 기본 설정 그대로 | (설정 불필요) |
| 2 | 사내 CA 번들 지정 | `KCSC_CA_BUNDLE=C:\certs\corp-ca.pem` |
| 3 (비권장) | SSL 검증 비활성화 | `KCSC_VERIFY_SSL=false` |

---

## 프로젝트 구조 | Project Structure

```
KCSC-MCP/
|-- server.py          # MCP 서버 (4개 도구) | MCP server (4 tools)
|-- pyproject.toml     # 프로젝트 메타데이터 | Project metadata
|-- requirements.txt   # 의존성 | Dependencies
|-- .env.example       # 환경변수 템플릿 | Environment template
+-- tests/
    +-- test_server.py # 테스트 | Tests
```

---

## 테스트 실행 | Running Tests

```bash
pytest
```

테스트 항목: 코드 타입 검증, HTML 제거, 오류 정규화, 섹션 검색, 캐시 불변성

---

## 환경 변수 목록 | Environment Variables

| 변수 Variable | 필수 | 설명 Description |
|--------------|------|-----------------|
| `KCSC_API_KEY` | 필수 | KCSC OpenAPI 키 |
| `KCSC_CACHE_TTL_SECONDS` | 선택 | 캐시 TTL (기본: 600초) |
| `KCSC_CA_BUNDLE` | 선택 | 사내 CA 인증서 번들 경로 |
| `KCSC_VERIFY_SSL` | 선택 | SSL 검증 비활성화 (`false`) |

---

## 자주 묻는 질문 | FAQ

### API 키를 넣었는데 동작하지 않아요

- 키 만료 여부 확인
- `.env` 파일이 프로젝트 루트에 있는지 확인
- Claude Desktop 설정의 `env`에도 키를 넣었는지 확인

### SSL 인증서 오류가 나요

- 먼저 기본 설정으로 재시도
- 사내망이면 `KCSC_CA_BUNDLE`에 사내 CA 번들 지정
- 최후 수단으로만 `KCSC_VERIFY_SSL=false` 사용

### code와 fullCode가 헷갈려요

- 둘 다 입력 가능합니다. 서버가 자동으로 변환합니다.

---

## 라이선스 | License

MIT License -- 자유롭게 사용, 수정, 배포할 수 있습니다.

MIT License -- Free to use, modify, and distribute.

---

## 만든 사람 | Author

**22B Labs** (sinmb79) -- The 4th Path

문의사항이나 기여는 [Issues](https://github.com/sinmb79/KCSC-MCP/issues)를 이용해 주세요.

For questions or contributions, please use [Issues](https://github.com/sinmb79/KCSC-MCP/issues).
