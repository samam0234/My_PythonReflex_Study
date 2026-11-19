from types import SimpleNamespace

import pytest


def test_board_v1_contract(monkeypatch, tmp_path):
    pytest.importorskip("fastapi")
    from fastapi.testclient import TestClient

    from backend import main as board

    monkeypatch.setenv("BOARD_V1_DB", str(tmp_path / "board.sqlite3"))
    monkeypatch.setattr(board, "time", SimpleNamespace(time=lambda: 1_800_000_000))

    def account(client, name):
        credentials = {"email": f"{name}@example.com", "password": "Test-password-123"}
        payload = {**credentials, "nickname": name}
        assert client.post("/api/auth/signup", json=payload).status_code == 201
        assert client.post("/api/auth/signup", json=payload).status_code == 409
        login = client.post("/api/auth/login", json=credentials).json()["data"]
        return {"Authorization": f"Bearer {login['accessToken']}"}

    with TestClient(board.app) as client:
        assert client.get("/health").json() == {"status": "ok"}
        assert client.get("/api-docs").status_code == 200
        owner, other = (account(client, name) for name in ("ming", "yuna"))
        assert client.get("/api/auth/me", headers=owner).json()["data"]["nickname"] == "ming"

        payload = {"title": "첫 글", "body": "CaseFold 검색", "tags": ["intro"]}
        assert client.post("/api/posts", json=payload).status_code == 401
        created = client.post("/api/posts", json=payload, headers=owner)
        assert created.status_code == 201
        path = created.headers["Location"]
        assert path == f"/api/posts/{created.json()['data']['id']}"

        listing = client.get("/api/posts", params={"q": "casefold", "limit": 90}).json()
        assert listing["meta"] == {
            "page": 1,
            "limit": 50,
            "total": 1,
            "totalPages": 1,
            "q": "casefold",
        }
        assert "body" not in listing["data"][0]
        assert client.patch(path, json={"title": "다른 이름"}, headers=other).status_code == 403
        assert client.delete(path, headers=other).status_code == 403
        updated = client.patch(path, json={"title": "수정 제목"}, headers=owner).json()["data"]
        assert updated["body"] == payload["body"] and updated["tags"] == ["intro"]

        comment = client.post(f"{path}/comments", json={"body": "댓글"}, headers=other).json()[
            "data"
        ]
        assert client.get(path).json()["data"]["commentCount"] == 1
        assert client.get(f"{path}/comments").json()["data"] == [comment]
        comment_path = f"/api/comments/{comment['id']}"
        assert client.delete(comment_path, headers=owner).status_code == 403
        assert client.delete(comment_path, headers=other).status_code == 204

        bad = client.get("/api/posts/abc", headers={"X-Request-Id": "study-check"})
        assert bad.status_code == 400
        assert bad.headers["X-Request-Id"] == bad.json()["error"]["requestId"] == "study-check"
        invalid = client.post("/api/posts", json={**payload, "title": ""}, headers=owner)
        assert invalid.status_code == 400 and "title" in invalid.json()["error"]["fields"]
        assert client.delete(path, headers=owner).status_code == 204
        assert client.get(path).status_code == 404
        assert client.post("/api/auth/logout", headers=owner).status_code == 204
        assert client.get("/api/auth/me", headers=owner).status_code == 401
        for _ in range(5):
            assert (
                client.post(
                    "/api/auth/login",
                    json={
                        "email": "unknown@example.com",
                        "password": "Test-password-123",
                    },
                ).status_code
                == 401
            )
        assert (
            client.post(
                "/api/auth/login",
                json={
                    "email": "unknown@example.com",
                    "password": "Test-password-123",
                },
            ).status_code
            == 429
        )
