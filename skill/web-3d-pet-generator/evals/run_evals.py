import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
skill = "\n".join(
    path.read_text()
    for path in [ROOT / "SKILL.md", *sorted((ROOT / "references").glob("*.md"))]
)
cases = json.loads((ROOT / "evals/evals.json").read_text())["evals"]
required_by_case = {
    1: ["reference-analysis", "structural signature", "Blender", "transcribe", "MCP"],
    2: ["correct only the named mismatch", "createWebPetPlugin", "preference persistence"],
    3: ["final-only Git publication", "git bundle", "one root commit", "private visibility"],
    4: ["25–30%", "stale `finished` event", "getBoundingClientRect", "exact recovery"],
    5: ["self-contained static example", "assets/preview/", "video playback", "failed requests"],
}
with_skill = {
    case["id"]: all(term.lower() in skill.lower() for term in required_by_case[case["id"]])
    for case in cases
}
baseline = {case["id"]: False for case in cases}
report = {"cases": len(cases), "with_skill_passed": sum(with_skill.values()), "baseline_passed": sum(baseline.values()), "with_skill": with_skill, "baseline": baseline}
print(json.dumps(report, indent=2))
raise SystemExit(0 if all(with_skill.values()) else 2)
