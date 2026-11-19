# study12 — 렌더링·쿼리·번들 성능 측정

목표: 같은 데이터·환경에서 전체 조회와 목록 DTO를 비교하고 쿼리·전송 비용을 줄인다.

실제 구현: [project/project/services/posts.py](project/project/services/posts.py), [tools/benchmark.py](tools/benchmark.py). 설치·검증 명령은 [README](README.md)를 따른다.

## 📖 이론

Reflex 응답 비용은 DB, Python 변환, State 직렬화·WebSocket 전송, 브라우저 렌더링으로 나뉜다. 목록은 본문을 제외한 20개 DTO만 반환하고 상세 화면에서 한 글을 조회한다. `Post.created_at,id` 복합 인덱스로 정렬 순서를 안정화한다.

구현은 [조회 서비스](project/project/services/posts.py), [Post 인덱스](project/project/models.py), [측정 도구](tools/benchmark.py)다. DB 원본은 영속 저장하고 State는 짧은 화면 캐시로 사용한다.

## 🛠️ 실기(코드·줄별 설명)

아래는 실제 `list_posts` 함수 발췌다. import·DTO·`PAGE_SIZE=20`은 연결된 원본 파일에 있다.
```python
def list_posts(session: Session, page: int = 0, search: str = "") -> PostPage:
    page = max(0, min(page, 1000))
    search = search.strip()[:64]
    query = select(col(Post.id), col(Post.title), col(Post.author), col(Post.created_at))
    count = select(func.count(col(Post.id)))
    if search:
        query = query.where(col(Post.title).contains(search, autoescape=True))
        count = count.where(col(Post.title).contains(search, autoescape=True))
    total = session.exec(count).one()
    # 검색 결과가 줄어 마지막 페이지를 벗어나면 실제 범위로 되돌린다.
    page = min(page, max(0, (total - 1) // PAGE_SIZE))
    rows = session.exec(
        query.order_by(col(Post.created_at).desc(), col(Post.id).desc())
        .offset(page * PAGE_SIZE)
        .limit(PAGE_SIZE)
    ).all()
    items = [
        PostSummary(id=pid, title=title, author=author, created_at=utc_text(created))
        for pid, title, author, created in rows
        if pid is not None
    ]
    return PostPage(items=items, total=total, page=page)
```

- `page`, `search`는 요청 범위를 제한한다.
- `select`는 ID·제목·작성자·작성 시각만 고른다. 본문은 가져오지 않는다.
- `contains(..., autoescape=True)`는 `%`, `_` 입력을 임의 wildcard로 확대하지 않는다.
- count 결과로 실제 페이지 범위를 다시 계산한다.
- 두 정렬 키·offset·limit는 순서와 조회량을 고정한다.
- `PostSummary`는 직렬화 가능한 데이터만 담는다.

저장소 루트에서 실행한다.

```powershell
python tools/benchmark.py
python tools/verify_app.py --app project --mode prod
```

첫 명령은 **임시 SQLite**에 글 1,000개·본문 1,000자를 만들고 예열 3회·측정 30회를 수행한다. 실제 프로젝트 DB에는 쓰지 않는다. 둘째 명령은 별도 임시 DB에서 prod 빌드·서버·브라우저의 페이지네이션·검색을 검증한다.

2026-11-19 로컬 Windows / Python 3.12.10 측정:

| 지표 | 전체 조회 | 20개 목록 DTO |
|---|---:|---:|
| 조회·DTO 변환 p95 (ms) | 33.046 | 0.707 |
| JSON UTF-8 바이트 | 3154783 | 2298 |

실행 계획은 `SCAN post USING INDEX ix_post_created_id`였다. JSON 수치는 직렬화 결과 크기이며 실제 압축 WebSocket 전송량과는 다르다. 측정 조건·원본 결과는 `artifacts/benchmark.json`에 저장한다.

번들은 동일 prod 빌드에서 브라우저 Network의 JS 전송량·캐시·압축 조건을 기록한다. 큰 라이브러리 제거 전후를 재빌드해 비교하고 `.web/`는 직접 수정하지 않는다. 현재 차트 도입 전후의 번들 전송량은 별도 미측정 항목이다.

## 오류 노트

- 개발·prod 수치를 섞지 않는다. 캐시 예열 여부도 맞춘다.
- background 안의 동기 DB 작업은 자동으로 비차단이 되지 않는다. 세션을 여는 동기 함수 전체를 `asyncio.to_thread`로 분리한다.
- 조회 캐시는 다른 사용자의 변경을 자동 감지하지 않는다. 명시적 새로 조회·TTL·쓰기 후 무효화가 필요하다.

## ☐ 체크리스트

- ☐ DB·직렬화·실제 네트워크·브라우저 비용을 구분한다.
- ☐ 목록 20행·본문 미전송·안정 정렬을 확인한다.
- ☐ [노션 delta 흐름] 실제 WS 프레임과 JSON 측정값의 차이를 설명한다.
- ☐ 쿼리 계획과 복합 인덱스 migration을 확인한다.
- ☐ 동일 조건의 p95·표본 수·환경과 번들 미측정 항목을 기록한다.

## 다음 단계 연결

[study13](study13.md)에서 UI 라이브러리의 기능과 비용을 확인한다.
