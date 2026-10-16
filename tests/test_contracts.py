import json, pathlib, tomllib, jsonschema
ROOT = pathlib.Path(__file__).resolve().parents[1]
# test_hw1_trace_example_still_validates reads HW1's example trace from a clone of hw1-agent-architectures beside this one.
HW1 = ROOT.parent / "hw1-agent-architectures"
def schema(name): return json.loads((ROOT / f"{name}.schema.json").read_text())
def validator(name): return jsonschema.Draft202012Validator(schema(name))

def test_config_example_validates():
    cfg = tomllib.loads((ROOT / "examples/config.example.toml").read_text())
    validator("config").validate(cfg)

def test_config_requires_agent_mcp_sandbox():
    cfg = tomllib.loads((ROOT / "examples/config.example.toml").read_text())
    for key in ("agent", "mcp", "sandbox"):
        bad = {k: v for k, v in cfg.items() if k != key}
        assert list(validator("config").iter_errors(bad)), key

def test_trace_example_lines_validate():
    v = validator("trace")
    for line in (ROOT / "examples/trace.example.jsonl").read_text().splitlines():
        v.validate(json.loads(line))

def test_hw1_trace_example_still_validates():   # Review Focus 4
    v = validator("trace")
    for line in (HW1 / "briefs/trace.example.jsonl").read_text().splitlines():
        v.validate(json.loads(line))

def test_refused_by_is_closed_enum():
    v = validator("trace")
    bad = {"step": 1, "ts": 1.0, "run_id": "r", "alert_id": None, "kind": "tool_result", "tool": "x", "ok": False, "error": "e", "refused_by": "prompt"}
    assert list(v.iter_errors(bad))

def test_report_example_validates_and_requires_remediation():
    rep = json.loads((ROOT / "examples/report.example.json").read_text())
    validator("report").validate(rep)
    del rep["alerts"][0]["remediation"]
    assert list(validator("report").iter_errors(rep))


def trace_events():
    return [json.loads(line) for line in (ROOT / "examples/trace.example.jsonl").read_text().splitlines()]

def test_remediation_state_change_carries_checks_and_no_status():
    # spec 3.5: remediation writes node and the three checks. With alert_status and label it would
    # be a second event matching HW1 invariant 5 for an alert that was already settled at submit.
    found = [e for e in trace_events() if e["kind"] == "state_change" and e["node"] == "remediation"]
    assert found
    for e in found:
        assert "checks" in e and "alert_status" not in e and "label" not in e

def test_trace_example_settles_each_alert_exactly_once_at_submit():   # HW1 invariant 5
    ev = trace_events()
    for alert in {e["alert_id"] for e in ev if e["alert_id"] is not None}:
        settled = [e for e in ev if e["kind"] == "state_change" and e["alert_id"] == alert
                   and "alert_status" in e and "label" in e]
        assert [e["node"] for e in settled] == ["submit"], alert

def test_trace_example_meets_hw1_invariants_2_3_4_6():
    ev = trace_events()
    assert [e["step"] for e in ev] == list(range(1, len(ev) + 1))                      # 2
    assert [e["kind"] for e in ev].count("terminal") == 1 and ev[-1]["kind"] == "terminal"   # 3
    calls = [e["usage"] for e in ev if e["kind"] == "model_call"]
    counters = set(ev[-1]["usage_total"]).union(*calls)
    assert ev[-1]["usage_total"] == {k: sum(u.get(k, 0) for u in calls) for k in counters}   # 4
    for i, e in enumerate(ev):                                                         # 6
        if e["kind"] == "tool_request":
            assert ev[i + 1]["kind"] == "tool_result" and ev[i + 1]["tool"] == e["tool"], e["step"]
