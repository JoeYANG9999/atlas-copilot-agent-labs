"""不联网的单元测试：关注清单解析、洞察校验（引用必须真实）、兜底与渲染。

运行：python -m pytest Lab-01-Industry-Insight/tests -q
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "mcp_server"))

import industry_tools as t  # noqa: E402

FOCUS = """# 清单
## 汇报对象
- 读者：销售
## 锂电
- 搜索（中文）：锂电池 扩产
- 搜索（英文）：battery gigafactory
- 关注什么：扩产节奏
- 排除词：榜单, 排行榜
## 全局排除词
- CAGR, 研究报告
"""


def _signals(tmp_path: Path) -> Path:
    data = {
        "generated_at": "2026-10-16T00:00:00Z",
        "window": {"days": 7, "start": "2026-10-09", "end": "2026-10-16"},
        "coverage": [{"topic": "锂电", "items": 2, "requests_ok": 2, "requests_failed": []}],
        "items": [
            {"id": "S001", "topic": "锂电", "title": "某电池厂宣布扩产 20GWh", "url": "https://a.example/1",
             "source": "A", "via": "media", "signal_level": "A", "published_at": "2026-10-15T00:00:00Z", "summary": ""},
            {"id": "S002", "topic": "锂电", "title": "某电池厂宣布扩产20GWh项目", "url": "https://b.example/2",
             "source": "B", "via": "google_news", "signal_level": "B", "published_at": "2026-10-14T00:00:00Z", "summary": ""},
        ],
    }
    p = tmp_path / "raw_signals.json"
    p.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    return p


def test_parse_focus_reads_topics_queries_and_excludes():
    topics, global_exclude = t.parse_focus(FOCUS)
    lib = next(x for x in topics if x.name == "锂电")
    assert lib.queries_zh == ["锂电池 扩产"]
    assert lib.queries_en == ["battery gigafactory"]
    assert lib.exclude == ["榜单", "排行榜"]
    assert global_exclude == ["CAGR", "研究报告"]
    # 没有搜索词的说明段不会产生抓取请求
    plan = t._plan_requests(topics, [], 7)
    assert {r["topic"] for r in plan} == {"锂电"}
    assert all("when%3A7d" in r["url"] for r in plan)


def test_report_uses_only_real_signal_ids(tmp_path):
    sig = _signals(tmp_path)
    insights = {
        "summary": ["锂电扩产继续"],
        "topics": [{"topic": "锂电", "hotspots": [
            {"title": "电池厂扩产", "what_happened": "扩产 20GWh", "impact": "干燥压缩空气需求",
             "impact_area": "销售机会", "level": "高", "refs": ["S001", "S999"]},
            {"title": "没有出处的结论", "refs": ["S888"]},
        ]}],
        "actions": [{"owner": "销售", "action": "拜访该电池厂", "basis": "S001"}],
    }
    ip = tmp_path / "insights.json"
    ip.write_text(json.dumps(insights, ensure_ascii=False), encoding="utf-8")

    res = t.build_weekly_report(insights_path=ip, signals_path=sig, out_dir=tmp_path / "out", frontend_dir=None)
    assert res["mode"] == "llm"
    assert any("S999" in w for w in res["warnings"])
    assert any("没有出处的结论" in w for w in res["warnings"])

    report = json.loads((tmp_path / "out" / "report.json").read_text(encoding="utf-8"))
    hotspots = report["topics"][0]["hotspots"]
    assert [h["title"] for h in hotspots] == ["电池厂扩产"]
    assert hotspots[0]["references"][0]["url"] == "https://a.example/1"
    md = (tmp_path / "out" / "report.md").read_text(encoding="utf-8")
    assert "[A](https://a.example/1)" in md and "销售机会" in md


def test_invalid_insights_fall_back(tmp_path):
    sig = _signals(tmp_path)
    ip = tmp_path / "insights.json"
    ip.write_text("{not json", encoding="utf-8")
    res = t.build_weekly_report(insights_path=ip, signals_path=sig, out_dir=tmp_path / "out", frontend_dir=None)
    assert res["mode"] == "fallback"
    report = json.loads((tmp_path / "out" / "report.json").read_text(encoding="utf-8"))
    # 两条几乎相同的标题被归并成一个热点
    assert len(report["topics"][0]["hotspots"]) == 1
    assert len(report["topics"][0]["hotspots"][0]["references"]) == 2


def test_search_signals_matches_title_case_insensitive(tmp_path):
    sig = _signals(tmp_path)
    res = t.search_signals(keyword="电池厂", signals_path=sig)
    assert res["total"] == 2
    assert res["items"][0]["url"].startswith("https://")
    assert t.search_signals(keyword="不存在的公司", signals_path=sig)["total"] == 0
