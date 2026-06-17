from hermes_cli.models import _PROVIDER_MODELS


def test_native_anthropic_curated_catalog_is_oauth_allowlist():
    assert _PROVIDER_MODELS["anthropic"] == [
        "claude-sonnet-4-6",
        "claude-opus-4-6",
        "claude-opus-4-8",
    ]
