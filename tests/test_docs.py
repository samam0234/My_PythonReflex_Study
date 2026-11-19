import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_study_contract_and_links():
    names = [f"study{i}.md" for i in range(19)] + ["studyMidpoint.md", "studyFinal.md"]
    assert sorted(p.name for p in ROOT.glob("study*.md")) == sorted(names)
    headings = [
        "## 📖 이론",
        "## 🛠️ 실기(코드·줄별 설명)",
        "## 오류 노트",
        "## ☐ 체크리스트",
        "## 다음 단계 연결",
    ]
    for name in names:
        text = (ROOT / name).read_text(encoding="utf-8")
        assert re.search(r"^목표: .+", text, re.M), name
        positions = [text.find(h) for h in headings]
        assert min(positions) >= 0 and positions == sorted(positions), name
        assert "- ☐ " in text and "\ufffd" not in text, name
        assert text.count("```") % 2 == 0, name
        for target in re.findall(r"\]\(([^)]+)\)", text):
            if not target.startswith(("https:", "http:", "#")):
                assert (ROOT / target.split("#")[0]).exists(), (name, target)
