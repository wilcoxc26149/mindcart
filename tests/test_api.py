"""Unit tests for Cognee HTTP remember/recall wrappers."""

from unittest.mock import patch

import httpx

from src import api


class _FakeResponse:
    def __init__(self, *, status_code: int, payload, text: str = "", url: str = "http://localhost:8000/api/v1/recall"):
        self.status_code = status_code
        self._payload = payload
        self.text = text
        self.request = httpx.Request("POST", url)

    @property
    def is_success(self) -> bool:
        return 200 <= self.status_code < 300

    def json(self):
        return self._payload


def test_remember_posts_multipart(monkeypatch):
    monkeypatch.setattr(api, "load_config", lambda: {"cognee_api_url": "http://localhost:8000"})
    captured = {}

    class FakeClient:
        def __init__(self, *args, **kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def post(self, url, data=None, files=None, json=None):
            captured["url"] = url
            captured["data"] = data
            captured["files"] = files
            return _FakeResponse(
                status_code=200,
                payload={"dataset_id": "ds-1", "items": [{"id": "d0", "name": "doc_0.txt"}]},
                url=url,
            )

    with patch("src.api.httpx.Client", FakeClient):
        result = api.remember(["hello world"], dataset_name="repo_memory")

    assert captured["url"] == "http://localhost:8000/api/v1/remember"
    assert captured["data"]["datasetName"] == "repo_memory"
    assert captured["data"]["run_in_background"] == "false"
    assert captured["files"][0][0] == "data"
    assert captured["files"][0][1][0] == "doc_0.txt"
    assert result["dataset_id"] == "ds-1"
    assert result["items"][0]["id"] == "d0"


def test_remember_uses_custom_filenames(monkeypatch):
    monkeypatch.setattr(api, "load_config", lambda: {"cognee_api_url": "http://localhost:8000"})
    captured = {}

    class FakeClient:
        def __init__(self, *args, **kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def post(self, url, data=None, files=None, json=None):
            captured["files"] = files
            return _FakeResponse(status_code=200, payload={}, url=url)

    with patch("src.api.httpx.Client", FakeClient):
        api.remember(["hello"], dataset_name="repo_memory", filenames=["README.md"])

    assert captured["files"][0][1][0] == "README.md"


def test_update_data_patches_query_and_file(monkeypatch):
    monkeypatch.setattr(api, "load_config", lambda: {"cognee_api_url": "http://localhost:8000"})
    captured = {}

    class FakeClient:
        def __init__(self, *args, **kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def patch(self, url, params=None, files=None, data=None, json=None):
            captured["url"] = url
            captured["params"] = params
            captured["files"] = files
            return _FakeResponse(status_code=200, payload={"status": "ok"}, url=url)

    with patch("src.api.httpx.Client", FakeClient):
        api.update_data(
            "Source file: README.md\n\n# hi\n",
            data_id="data-1",
            dataset_id="ds-1",
            filename="README.md",
        )

    assert captured["url"] == "http://localhost:8000/api/v1/update"
    assert captured["params"] == {"data_id": "data-1", "dataset_id": "ds-1"}
    assert captured["files"][0][1][0] == "README.md"


def test_forget_posts_json(monkeypatch):
    monkeypatch.setattr(api, "load_config", lambda: {"cognee_api_url": "http://localhost:8000"})
    captured = {}

    class FakeClient:
        def __init__(self, *args, **kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def post(self, url, data=None, files=None, json=None):
            captured["url"] = url
            captured["json"] = json
            return _FakeResponse(status_code=200, payload={"status": "ok"}, url=url)

    with patch("src.api.httpx.Client", FakeClient):
        api.forget(dataset="repo_memory", data_id="data-1")

    assert captured["url"] == "http://localhost:8000/api/v1/forget"
    assert captured["json"] == {"dataset": "repo_memory", "data_id": "data-1"}


def test_recall_formats_list(monkeypatch):
    monkeypatch.setattr(api, "load_config", lambda: {"cognee_api_url": "http://localhost:8000"})

    class FakeClient:
        def __init__(self, *args, **kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def post(self, url, data=None, files=None, json=None):
            assert json["query"] == "How does ingest work?"
            assert json["datasets"] == ["repo_memory"]
            return _FakeResponse(status_code=200, payload=["The pipeline walks globs."], url=url)

    with patch("src.api.httpx.Client", FakeClient):
        result = api.recall("How does ingest work?", ["repo_memory"])

    assert result == "[1] The pipeline walks globs."


def test_remember_raises_on_http_error(monkeypatch):
    monkeypatch.setattr(api, "load_config", lambda: {"cognee_api_url": "http://localhost:8000"})

    class FakeClient:
        def __init__(self, *args, **kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def post(self, url, data=None, files=None, json=None):
            return _FakeResponse(status_code=500, payload={}, text="boom", url=url)

    with patch("src.api.httpx.Client", FakeClient):
        try:
            api.remember("note", dataset_name="tenant_memory_admin")
        except RuntimeError as exc:
            assert "500" in str(exc)
            assert "boom" in str(exc)
        else:
            raise AssertionError("expected RuntimeError")
