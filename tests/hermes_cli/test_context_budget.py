from __future__ import annotations

import json


def test_context_budget_snapshot_defaults_to_normal_and_omits_volatile(monkeypatch, tmp_path):
    monkeypatch.setenv("HERMES_HOME", str(tmp_path / "hermes"))
    monkeypatch.delenv("HERMES_MODE", raising=False)

    from hermes_cli.context_budget import build_context_budget_snapshot, write_context_budget_receipt

    snap = build_context_budget_snapshot(
        session_id="sess-1",
        mode=None,
        provider="anthropic",
        model="claude-sonnet-4.6",
        toolsets=["web"],
        tool_count=2,
        system_prompt="stable identity law boundary",
    )

    assert snap["mode"] == "normal"
    assert snap["normalized_mode"] == "normal"
    assert snap["sacred_prefix"] == "first"
    assert snap["pruning"] == "none"
    assert snap["tool_filtering"] == "none"
    assert snap["enforcement"] == "none"
    assert snap["context"]["sections"]["sacred_prefix"]["loaded"] is True
    assert snap["context"]["sections"]["organism_pulse"]["loaded"] is False
    assert snap["context"]["sections"]["council"]["freshness"] == "not_loaded"
    assert snap["tools"]["class"] == "medium"

    path = write_context_budget_receipt(snap)
    saved = json.loads((tmp_path / "hermes" / "context-receipts" / "hermes-context-sess-1.json").read_text())
    assert path.endswith("hermes-context-sess-1.json")
    assert saved["schema"] == "hermes.context_budget.v1"
    assert saved["enforcement"] == "none"


def test_context_budget_deep_mode_banner_is_truthful_not_enforcement(monkeypatch, tmp_path):
    monkeypatch.setenv("HERMES_HOME", str(tmp_path / "hermes"))

    from hermes_cli.context_budget import build_context_budget_snapshot, format_startup_banner

    snap = build_context_budget_snapshot(
        session_id="deep",
        mode="deep",
        provider="openrouter",
        model="gpt-5.5",
        toolsets=["hermes-cli"],
        tool_count=20,
    )
    lines = "\n".join(format_startup_banner(snap))

    assert snap["mode"] == "deep"
    assert snap["tools"]["class"] == "heavy"
    assert snap["route"]["deep_confirmed"] is False
    assert "sacred continuity first" in lines
    assert "no pruning/enforcement" in lines
    assert "protected" not in lines.lower()
    assert "guaranteed" not in lines.lower()


def test_warn_only_deep_detector_warns_without_enforcement():
    from hermes_cli.context_budget import detect_deep_work_warnings

    warnings = detect_deep_work_warnings(
        "A) write law\nB) build test matrix\nC) add fail-closed audit for continuity",
        mode="lean",
    )

    assert len(warnings) == 1
    warning = warnings[0]
    assert warning["warning_type"] == "deep_work_detected"
    assert warning["current_mode"] == "lean"
    assert warning["action"] == "warn_only"
    assert warning["enforcement_applied"] is False


def test_warn_only_deep_detector_avoids_false_positives():
    from hermes_cli.context_budget import detect_deep_work_warnings

    assert detect_deep_work_warnings("take a deep breath", mode="normal") == []
    assert detect_deep_work_warnings('the fixture says "deep audit" only', mode="normal") == []
    assert detect_deep_work_warnings("deep audit", mode="deep") == []


def test_gate45_mode_behavior_is_descriptive_warn_only(monkeypatch, tmp_path):
    monkeypatch.setenv("HERMES_HOME", str(tmp_path / "hermes"))

    from hermes_cli.context_budget import build_context_budget_snapshot, describe_mode_behavior

    lean = describe_mode_behavior("lean")
    deep_snap = build_context_budget_snapshot(
        session_id="gate45-deep",
        mode="deep",
        provider="anthropic",
        model="claude-sonnet-4.6",
        toolsets=["terminal"],
        tool_count=18,
        system_prompt="IDENTITY\n\n# Hermes Budget Law\n\nTASK",
    )

    assert lean["mode"] == "lean"
    assert lean["descriptive_only"] is True
    assert lean["enforcement_state"] == "warn_only_preview"
    assert lean["effective_changes"]["prompt_pruning"] is False
    assert "identity_continuity" in lean["must_preserve"]
    assert "tool_catalog_examples" in lean["may_late_load"]

    policy = deep_snap["budget_policy"]
    assert policy["gate"] == "4/5-warn-only-design"
    assert policy["warn_only"] is True
    assert policy["mode_behavior"]["mode"] == "deep"
    assert policy["mode_behavior"]["receipt_detail"] == "expanded_provenance"
    assert policy["effective_changes"]["tool_filtering"] is False
    assert deep_snap["pruning"] == "none"
    assert deep_snap["tool_filtering"] == "none"
    assert deep_snap["enforcement"] == "none"


def test_gate45_tool_class_policy_records_shape_without_filtering(monkeypatch, tmp_path):
    monkeypatch.setenv("HERMES_HOME", str(tmp_path / "hermes"))

    from hermes_cli.context_budget import build_context_budget_snapshot, describe_tool_class

    light_policy = describe_tool_class("light")
    assert light_policy["class"] == "light"
    assert light_policy["filtering_state"] == "not_applied"
    assert light_policy["effective_changes"]["tool_filtering"] is False

    snap = build_context_budget_snapshot(
        session_id="gate45-tools",
        mode="normal",
        provider="openrouter",
        model="gpt-5.5",
        toolsets=["browser", "memory"],
        tool_count=9,
    )

    assert snap["tools"]["class"] == "heavy"
    assert snap["tools"]["policy"]["budget_shape"] == "large_schema_or_side_effect_capable_tooling"
    assert snap["tools"]["filtering_active"] is False
    assert snap["tools"]["classification_basis"]["policy_version"] == "gate4_5_warn_only_v1"
    assert snap["budget_policy"]["tool_class"]["class"] == "heavy"
    assert snap["budget_policy"]["tool_class"]["descriptive_only"] is True


def test_parser_accepts_hermes_mode_flag():
    from hermes_cli._parser import build_top_level_parser

    parser, _subs, chat_parser = build_top_level_parser()
    chat_parser.set_defaults(func=lambda _args: None)

    args = parser.parse_args(["chat", "--hermes-mode", "lean", "-q", "hello"])
    assert args.hermes_mode == "lean"

    top = parser.parse_args(["--hermes-mode", "deep", "chat", "-q", "hello"])
    assert top.hermes_mode == "deep"
