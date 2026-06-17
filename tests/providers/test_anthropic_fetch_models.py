import importlib.util
from pathlib import Path


class _Resp:
    def __init__(self, payload: bytes):
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def read(self):
        return self.payload


def _load_anthropic_plugin():
    root = Path(__file__).resolve().parents[2]
    path = root / "plugins" / "model-providers" / "anthropic" / "__init__.py"
    spec = importlib.util.spec_from_file_location("_test_anthropic_provider_plugin", path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def test_fetch_models_uses_bearer_for_claude_oauth_without_api_key_probe(monkeypatch):
    module = _load_anthropic_plugin()
    calls = []

    def fake_urlopen(req, timeout=0):
        calls.append(dict(req.header_items()))
        return _Resp(b'{"data":[{"id":"claude-opus-4-8"},{"id":"claude-sonnet-4-6"}]}')

    monkeypatch.setattr(module.urllib.request, "urlopen", fake_urlopen)

    models = module.AnthropicProfile(name="anthropic").fetch_models(api_key="sk-ant-oat01-oauth")

    assert models == ["claude-opus-4-8", "claude-sonnet-4-6"]
    assert len(calls) == 1
    auth_headers = {k.lower(): v for k, v in calls[0].items()}
    assert auth_headers["authorization"] == "Bearer sk-ant-oat01-oauth"
    assert "x-api-key" not in auth_headers


def test_fetch_models_uses_api_key_without_bearer_retry(monkeypatch):
    module = _load_anthropic_plugin()
    calls = []

    def fake_urlopen(req, timeout=0):
        calls.append(dict(req.header_items()))
        return _Resp(b'{"data":[{"id":"claude-opus-4-6"}]}')

    monkeypatch.setattr(module.urllib.request, "urlopen", fake_urlopen)

    models = module.AnthropicProfile(name="anthropic").fetch_models(api_key="sk-ant-api03-test")

    assert models == ["claude-opus-4-6"]
    assert len(calls) == 1
    assert any(k.lower() == "x-api-key" for k in calls[0])
