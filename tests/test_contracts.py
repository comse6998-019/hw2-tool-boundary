import json, pathlib, tomllib, jsonschema
ROOT = pathlib.Path(__file__).resolve().parents[1]
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
