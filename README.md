# KCSC MCP Server

> Meta Description: 국가건설기준센터 KCSC OpenAPI를 Claude Desktop 등 MCP 클라이언트에서 바로 검색하고 읽을 수 있게 만드는 Python MCP 서버입니다.
>
> Labels: mcp, kcsc, claude-desktop, python, construction, kcs, kds, openapi

건설기준 문서는 공개되어 있어도, 실제로 써보면 늘 한 걸음 멉니다. 검색은 웹에서 하고, 본문은 따로 열고, 필요한 조항은 다시 정리해야 합니다. 이 프로젝트는 그 왕복을 줄이기 위해 만들었습니다. 국가건설기준센터(KCSC) OpenAPI를 MCP 서버로 감싸서, Claude Desktop 같은 MCP 클라이언트 안에서 KCS와 KDS를 바로 찾고, 읽고, 문서 내부까지 검색할 수 있게 합니다.

쉽게 말하면 이 저장소는 "건설기준을 AI 작업 흐름 안으로 가져오는 다리"입니다.

## 왜 이 프로젝트가 필요한가

좋은 도구는 새로운 기능을 더하는 도구가 아니라, 이미 있는 지식을 더 가까이 가져오는 도구입니다. KCSC에는 이미 중요한 기준 문서가 있습니다. 문제는 접근 경로가 인간 중심이라는 점입니다. 사람이 브라우저를 열고, 키워드를 바꾸고, 페이지를 넘기고, 필요한 단락을 다시 복사하는 구조는 검토 속도를 늦춥니다.

MCP는 그 구조를 바꿉니다. 문서를 "파일"이나 "웹페이지"가 아니라 "대화 가능한 컨텍스트"로 바꿔주기 때문입니다. 이 서버를 붙이면 Claude Desktop 같은 클라이언트에서 다음이 가능해집니다.

- KCS/KDS 코드 목록 조회
- 키워드 기반 코드 검색
- 특정 기준 문서 본문 조회
- 문서 내부 제목/본문 단락 검색

검색의 길이가 짧아질수록 판단의 깊이는 길어집니다.

## 제공 도구

| Tool | 설명 |
|------|------|
| `kcsc_list_codes` | KCS/KDS 코드 목록을 조회합니다. 타입, 키워드, 페이지네이션을 지원합니다. |
| `kcsc_search_codes` | 코드명 기준으로 빠르게 검색합니다. |
| `kcsc_get_content` | 특정 문서의 전체 본문을 가져옵니다. HTML 제거 옵션을 지원합니다. |
| `kcsc_search_sections` | 특정 문서 안에서 제목과 본문 단락을 키워드로 검색합니다. |

## 이 프로젝트가 해결하는 실제 불편

KCSC 응답에는 `code`와 `fullCode`가 함께 등장합니다. 이 둘을 처음 보면 꽤 헷갈립니다. 실제 문서 본문 조회는 보통 6자리 `code` 기준으로 이뤄지지만, 목록 응답에서는 더 긴 `fullCode`가 더 눈에 잘 들어옵니다. 그래서 이 서버는 `kcsc_get_content`와 `kcsc_search_sections`에서 6자리 `code`와 더 긴 `fullCode`를 모두 받을 수 있게 처리해 두었습니다.

또 하나는 SSL 문제입니다. 일부 Windows 환경이나 사내망 환경에서는 `certifi` 체인만으로 KCSC HTTPS 연결이 실패할 수 있습니다. 이 프로젝트는 기본적으로 Windows 시스템 인증서 저장소를 우선 활용해서 그 문제를 완화합니다.

## 프로젝트 구조

```text
KCSC-MCP/
├─ server.py
├─ pyproject.toml
├─ requirements.txt
├─ .env.example
├─ tests/
│  └─ test_server.py
└─ README.md
```

## 빠른 시작

### 1. 저장소 준비

```powershell
git clone https://github.com/sinmb79/KCSC-MCP.git
cd KCSC-MCP
```

### 2. 가상환경 생성

```powershell
python -m venv .venv
.\.venv\Scripts\python -m pip install --upgrade pip
```

### 3. 의존성 설치

가장 간단한 방법은 editable 모드로 설치하는 것입니다.

```powershell
.\.venv\Scripts\python -m pip install -e ".[dev]"
```

또는 아래처럼 설치해도 됩니다.

```powershell
.\.venv\Scripts\python -m pip install -r requirements.txt
```

### 4. 환경 변수 설정

`.env.example`을 복사해 `.env`를 만듭니다.

```powershell
Copy-Item .env.example .env
```

그다음 `.env`에서 `KCSC_API_KEY` 값을 실제 발급 키로 채워주세요.

```env
KCSC_API_KEY=your_real_kcsc_api_key
```

KCSC API 키 발급 페이지:

[https://www.kcsc.re.kr/support/api](https://www.kcsc.re.kr/support/api)

## 실행 방법

### 방법 1. Python 파일 직접 실행

```powershell
.\.venv\Scripts\python server.py
```

### 방법 2. 설치된 스크립트로 실행

```powershell
.\.venv\Scripts\kcsc-mcp
```

둘 중 어느 쪽을 써도 됩니다. 내부적으로는 같은 MCP 서버를 실행합니다.

## Claude Desktop 연결 방법

Windows 기준 설정 파일은 보통 아래 경로에 있습니다.

```text
%AppData%\Claude\claude_desktop_config.json
```

예시:

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

또는 스크립트 진입점을 써도 됩니다.

```json
{
  "mcpServers": {
    "kcsc": {
      "command": "D:/Workspace/KCSC-MCP/.venv/Scripts/kcsc-mcp.exe"
    }
  }
}
```

## 각 도구를 어떻게 써야 하나

### `kcsc_list_codes`

전체 목록을 보고 싶을 때 씁니다. 아직 어떤 코드가 있는지 모를 때 가장 먼저 쓰기 좋습니다.

예시:

```text
kcsc_list_codes(code_type="KCS", limit=20)
kcsc_list_codes(keyword="콘크리트", limit=30)
kcsc_list_codes(code_type="KDS", keyword="도로", limit=10)
```

### `kcsc_search_codes`

이미 키워드는 알고 있고, 빠르게 후보만 추리고 싶을 때 적합합니다.

예시:

```text
kcsc_search_codes(keyword="콘크리트")
kcsc_search_codes(keyword="교량", code_type="KDS", limit=15)
```

### `kcsc_get_content`

특정 문서의 전체 본문이 필요할 때 사용합니다. `code` 또는 `fullCode` 둘 다 받을 수 있습니다.

예시:

```text
kcsc_get_content(code_type="KCS", code="114010")
kcsc_get_content(code_type="KCS", code="2010114010")
kcsc_get_content(code_type="KDS", code="10101000", plain_text=True)
```

### `kcsc_search_sections`

문서 전체를 다 읽기 전에, 특정 주제가 어디에 나오는지 바로 찾고 싶을 때 가장 유용합니다. 제목과 본문 내용을 같이 검색합니다.

예시:

```text
kcsc_search_sections(code_type="KCS", code="114010", keyword="공사")
kcsc_search_sections(code_type="KCS", code="2010114010", keyword="거푸집", limit=5)
kcsc_search_sections(code_type="KDS", code="10101000", keyword="하중", include_full_contents=True)
```

## 추천 사용 흐름

처음부터 본문을 여는 것보다, 아래 흐름이 더 효율적입니다.

1. `kcsc_search_codes`로 관련 문서 후보를 찾습니다.
2. 후보가 많으면 `kcsc_list_codes`로 범위를 더 좁힙니다.
3. `kcsc_search_sections`로 문서 내부에서 필요한 조항이 있는지 먼저 확인합니다.
4. 마지막으로 `kcsc_get_content`로 전체 문맥을 읽습니다.

이 순서는 검색 비용을 줄이고, 필요한 문맥만 더 빨리 확보하게 해줍니다.

## 캐시 동작

반복 호출을 줄이기 위해 메모리 캐시를 사용합니다.

- 코드 목록 캐시
- 문서 본문 캐시

기본 TTL은 600초이며, 아래 환경 변수로 조정할 수 있습니다.

```env
KCSC_CACHE_TTL_SECONDS=600
```

짧게 두면 최신성이 좋아지고, 길게 두면 응답 속도와 API 호출 효율이 좋아집니다. 무엇을 최적화할지는 사용 맥락에 달려 있습니다.

## SSL / 네트워크 관련 참고

기본적으로는 아래 순서로 TLS 검증을 처리합니다.

1. `KCSC_CA_BUNDLE`이 있으면 해당 인증서 번들을 사용
2. `KCSC_VERIFY_SSL=false`면 검증 비활성화
3. 가능하면 `truststore`를 통해 시스템 인증서 저장소 사용
4. 마지막으로 기본 `httpx` 검증 사용

권장 순서는 다음과 같습니다.

- 가장 좋음: 기본 설정 그대로 사용
- 차선: `KCSC_CA_BUNDLE`에 사내 CA 번들 지정
- 마지막 수단: `KCSC_VERIFY_SSL=false`

예시:

```env
KCSC_CA_BUNDLE=C:\certs\corp-ca.pem
```

```env
KCSC_VERIFY_SSL=false
```

검증을 끄는 것은 편하지만, 보안과 무결성의 대가를 치릅니다. 편리함이 옳음보다 앞서면 시스템은 오래 못 갑니다.

## 테스트

```powershell
.\.venv\Scripts\python -m pytest
```

현재 테스트는 아래를 확인합니다.

- 코드 타입 검증
- HTML 제거 로직
- 오류 메시지 정규화
- 프리뷰 생성 로직
- 섹션 검색 로직
- 캐시 원본 불변성

## 개발 메모

- Python 3.11 이상을 권장합니다.
- 로컬 개발에서는 `.env`를 자동으로 읽습니다.
- `httpx` 및 `httpcore`의 과도한 요청 로그는 기본적으로 낮춰 두었습니다. API 키가 URL에 드러나는 상황을 피하기 위함입니다.

## 자주 막히는 지점

### 1. API 키를 넣었는데 동작하지 않을 때

- 키가 만료되지 않았는지 확인합니다.
- `.env` 경로가 프로젝트 루트에 있는지 확인합니다.
- Claude Desktop 설정 파일의 `env`에도 값을 직접 넣었는지 확인합니다.

### 2. SSL 인증서 오류가 날 때

- 먼저 기본 설정 그대로 다시 시도합니다.
- 사내망/보안 솔루션 환경이면 `KCSC_CA_BUNDLE`을 우선 고려합니다.
- 정말 불가피할 때만 `KCSC_VERIFY_SSL=false`를 사용합니다.

### 3. `code`와 `fullCode`가 헷갈릴 때

- 이 프로젝트에서는 둘 다 받을 수 있게 처리했습니다.
- 다만 API 내부 조회는 적절한 `code`로 정규화한 뒤 수행합니다.

## 로드맵

이 프로젝트는 지금도 쓸 수 있지만, 더 좋아질 수 있습니다.

- 응답 스키마 문서화 강화
- 더 정교한 본문 정제
- 문서 간 연관 검색
- 배포 패키지 구조 분리

도구는 완성되는 것이 아니라 성숙해집니다.

## 만든 사람

**22B Labs · 제4의 길 (The 4th Path)**  
GitHub: `sinmb79`

기술은 결국 인간의 사유 반경을 넓혀야 합니다. 그렇지 않다면 그것은 자동화일 뿐, 협력은 아닙니다.
