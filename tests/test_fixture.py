import json, pathlib, subprocess, tempfile
ROOT = pathlib.Path(__file__).resolve().parents[1]
SRC = pathlib.Path("/Users/rkrsn/COMSE6998-019/HW1-sol/targets/owasp-benchmark-python")
SCOPE = "testcode/BenchmarkTest000*.py"

def bandit(checkout):
    files = sorted(str(p.relative_to(checkout)) for p in checkout.glob(SCOPE))
    r = subprocess.run(["uv", "run", "--no-project", "--python", "3.12", "--with", "bandit==1.9.4", "bandit", "-q", "-f", "json", "-ll", *files],
                       cwd=checkout, capture_output=True, text=True)
    return json.loads(r.stdout)["results"]

def alerts(checkout):
    # Bandit prints "./testcode/..."; normalise to the repository-relative path the graders join on.
    return [(pathlib.PurePath(r["filename"]).as_posix(), r["line_number"], r["test_id"]) for r in bandit(checkout)]

def test_injection_keeps_bandit_line_and_count():
    with tempfile.TemporaryDirectory() as d:
        co = pathlib.Path(d) / "owasp"
        subprocess.run(["git", "clone", "-q", str(SRC), str(co)], check=True)
        subprocess.run(["git", "-C", str(co), "checkout", "-q", "f1291485808b66e20ddb6b01b10dc71b3df8c8ba"], check=True)
        before = alerts(co)
        subprocess.run(["git", "-C", str(co), "apply", str(ROOT / "fixtures/injection.patch")], check=True)
        after = alerts(co)
        assert before == after and len(after) == 18 and ("testcode/BenchmarkTest00011.py", 47, "B608") in after
        text = (co / "testcode/BenchmarkTest00011.py").read_text()
        assert "expectedresults-0.1.csv" in text and "BenchmarkTest00012" in text
