import importlib
import json
import logging

import azure.functions as func


# ---- Fakes (minimal objects your functions need) ----

class FakeHttpRequest:
    """
    Minimal stand-in for azure.functions.HttpRequest.
    Your function uses:
      - req.params.get("name")
      - req.get_json()
    """
    def __init__(self, params=None, json_body=None, raise_on_json=False):
        self.params = params or {}
        self._json_body = json_body
        self._raise_on_json = raise_on_json

    def get_json(self):
        if self._raise_on_json:
            raise ValueError("Invalid JSON")
        return self._json_body


class FakeInputStream:
    """
    Minimal stand-in for azure.functions.InputStream.
    Your blob trigger uses:
      - myblob.name
      - myblob.length
    """
    def __init__(self, name: str, length: int):
        self.name = name
        self.length = length


def _load_module():
    """
    Change 'function_app' to the filename (without .py) where your code lives.
    Example:
      If your code is in 'function_app.py' -> keep as is.
      If it's in '__init__.py' under a function folder -> set accordingly.
    """
    return importlib.import_module("function_app")


# ---- Tests for HTTP trigger ----

def test_http_trigger_name_in_query():
    mod = _load_module()
    req = FakeHttpRequest(params={"name": "Fuad"})
    resp = mod.http_trigger(req)

    assert isinstance(resp, func.HttpResponse)
    assert resp.status_code == 200
    assert resp.get_body().decode("utf-8") == (
        "Hello, Fuad. This HTTP triggered function executed successfully."
    )


def test_http_trigger_name_in_body():
    mod = _load_module()
    req = FakeHttpRequest(params={}, json_body={"name": "Alice"})
    resp = mod.http_trigger(req)

    assert resp.status_code == 200
    assert "Hello, Alice." in resp.get_body().decode("utf-8")


def test_http_trigger_missing_name_returns_help_message():
    mod = _load_module()
    # params empty, get_json raises ValueError -> name stays None
    req = FakeHttpRequest(params={}, json_body=None, raise_on_json=True)
    resp = mod.http_trigger(req)

    assert resp.status_code == 200
    body = resp.get_body().decode("utf-8")
    assert "Pass a name in the query string" in body


# ---- Tests for Blob trigger ----

def test_blob_trigger_logs_blob_info(caplog):
    mod = _load_module()
    blob = FakeInputStream(name="containerfuad/test.txt", length=123)

    with caplog.at_level(logging.INFO):
        mod.BlobTrigger(blob)

    # Your log message concatenates strings; just verify key parts appear
    logs = " ".join([r.message for r in caplog.records])
    assert "Python blob trigger function processed blob" in logs
    assert "containerfuad/test.txt" in logs
    assert "123 bytes" in logs

