"""行业洞察智能体的工具实现（抓取 → 信号 → 校验/兜底 → 周报）。

同一套函数有两个入口：
- server.py：标准 MCP 服务器（stdio），给 VS Code Copilot Agent 模式用；
- cli.py：给 gh-aw 的 mcp-scripts 调用（每周定时跑）。

大块数据一律落盘、传路径，不把大 JSON 当参数来回传（gh-aw 单参数 10KB 上限，
而且来回粘贴大段上下文会让 token 用量失控）。
"""

from __future__ import annotations

import html
import json
import re
import shutil
import urllib.parse
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from difflib import SequenceMatcher
from email.utils import parsedate_to_datetime
from pathlib import Path
from typing import Any

import feedparser
import httpx

LAB_DIR = Path(__file__).resolve().parent.parent
DEFAULT_FOCUS = LAB_DIR / "focus.md"
DEFAULT_SOURCES = LAB_DIR / "input" / "sources.json"
DEFAULT_OUTPUT = LAB_DIR / "output"
DEFAULT_FRONTEND = LAB_DIR / "frontend"
REPO_ROOT = LAB_DIR.parent

USER_AGENT = "Mozilla/5.0 (compatible; IndustryInsightAgent/1.0; +https://github.com)"
IMPACT_AREAS = ["销售机会", "产品", "市场", "风险"]
LEVELS = ["高", "中", "低"]


# --------------------------------------------------------------------------- #
# 关注清单（focus.md）
# --------------------------------------------------------------------------- #

@dataclass
class Topic:
    name: str
    queries_zh: list[str] = field(default_factory=list)
    queries_en: list[str] = field(default_factory=list)
    exclude: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "queries_zh": self.queries_zh,
            "queries_en": self.queries_en,
            "exclude": self.exclude,
            "notes": self.notes,
        }


_SEARCH_RE = re.compile(r"^[-*]\s*搜索[（(](中文|英文)[)）]\s*[:：]\s*(.+)$")
_EXCLUDE_RE = re.compile(r"^[-*]\s*排除词\s*[:：]\s*(.+)$")


def _split_words(value: str) -> list[str]:
    return [w.strip() for w in re.split(r"[,，、;；]", value) if w.strip()]


def parse_focus(text: str) -> tuple[list[Topic], list[str]]:
    """解析 focus.md。

    规则：每个 `## 标题` 是一个候选主题；其下的「- 搜索（中文/英文）：」行变成
    Google News 查询，「- 排除词：」行用于过滤噪音，其余列表行当作分析视角。
    `## 全局排除词` 段只放排除词，对所有主题生效。
    """
    topics: list[Topic] = []
    global_exclude: list[str] = []
    current: Topic | None = None
    in_global = False

    for raw in text.splitlines():
        line = raw.strip()
        if line.startswith("## "):
            title = line[3:].strip()
            in_global = title.startswith("全局排除词")
            current = None if in_global else Topic(name=title)
            if current:
                topics.append(current)
            continue
        if line.startswith("# "):
            current, in_global = None, False
            continue
        if in_global:
            m = _EXCLUDE_RE.match(line)
            if m:
                global_exclude += _split_words(m.group(1))
            elif line.startswith(("-", "*")):
                global_exclude += _split_words(line.lstrip("-* "))
            continue
        if current is None or not line.startswith(("-", "*")):
            continue
        m = _SEARCH_RE.match(line)
        if m:
            (current.queries_zh if m.group(1) == "中文" else current.queries_en).append(m.group(2).strip())
            continue
        m = _EXCLUDE_RE.match(line)
        if m:
            current.exclude += _split_words(m.group(1))
            continue
        current.notes.append(line.lstrip("-* ").strip())

    return topics, global_exclude


def read_focus(focus_path: str | Path = DEFAULT_FOCUS, sources_path: str | Path = DEFAULT_SOURCES) -> dict[str, Any]:
    topics, global_exclude = parse_focus(Path(focus_path).read_text(encoding="utf-8"))
    sources = _read_sources(sources_path)
    names = {t.name for t in topics}
    feeds_by_topic: dict[str, int] = {}
    for s in sources:
        feeds_by_topic[s["topic"]] = feeds_by_topic.get(s["topic"], 0) + 1
    active = [t for t in topics if t.queries_zh or t.queries_en or feeds_by_topic.get(t.name)]
    return {
        "focus_path": _rel(focus_path),
        "topics": [
            {**t.as_dict(), "media_feeds": feeds_by_topic.get(t.name, 0)} for t in active
        ],
        "global_exclude": global_exclude,
        "unmatched_feed_topics": sorted({s["topic"] for s in sources} - names),
    }


# --------------------------------------------------------------------------- #
# 抓取
# --------------------------------------------------------------------------- #

def _read_sources(path: str | Path) -> list[dict[str, Any]]:
    p = Path(path)
    if not p.is_file():
        return []
    data = json.loads(p.read_text(encoding="utf-8"))
    rows = data.get("sources", []) if isinstance(data, dict) else data
    out = []
    for s in rows:
        if isinstance(s, dict) and s.get("url") and s.get("topic"):
            out.append({
                "name": str(s.get("name") or s["url"]),
                "topic": str(s["topic"]),
                "url": str(s["url"]),
                "kind": "media",
                "signal_level": str(s.get("signal_level") or "B").upper(),
            })
    return out


def _rel(p: str | Path) -> str:
    """返回相对仓库根目录的路径，给智能体看的输出更短也更好懂。"""
    try:
        return str(Path(p).resolve().relative_to(REPO_ROOT))
    except ValueError:
        return str(p)


def google_news_url(query: str, lang: str, days: int) -> str:
    params = {"q": f"{query} when:{days}d"}
    if lang == "zh":
        params.update(hl="zh-CN", gl="CN", ceid="CN:zh-Hans")
    else:
        params.update(hl="en-US", gl="US", ceid="US:en")
    return "https://news.google.com/rss/search?" + urllib.parse.urlencode(params)


def _plan_requests(topics: list[Topic], sources: list[dict[str, Any]], days: int) -> list[dict[str, Any]]:
    names = {t.name for t in topics}
    plan = [s for s in sources if s["topic"] in names]
    for t in topics:
        for lang, queries in (("zh", t.queries_zh), ("en", t.queries_en)):
            for q in queries:
                plan.append({
                    "name": f"Google News（{'中文' if lang == 'zh' else '英文'}）：{q}",
                    "topic": t.name,
                    "url": google_news_url(q, lang, days),
                    "kind": "google_news",
                    "signal_level": "B",
                })
    return plan


def _clean_text(value: str, limit: int) -> str:
    s = re.sub(r"<[^>]+>", " ", value or "")
    s = re.sub(r"\s+", " ", html.unescape(s)).strip()
    return s if len(s) <= limit else s[: limit - 1].rstrip() + "…"


def _entry_time(e: Any) -> datetime | None:
    for key in ("published", "updated"):
        v = e.get(key)
        if v:
            try:
                dt = parsedate_to_datetime(v)
                return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
            except (TypeError, ValueError):
                pass
    for key in ("published_parsed", "updated_parsed"):
        v = e.get(key)
        if v:
            return datetime(*v[:6], tzinfo=timezone.utc)
    return None


def _fetch_one(client: httpx.Client, req: dict[str, Any], cutoff: datetime, max_items: int) -> dict[str, Any]:
    status: dict[str, Any] = {k: req[k] for k in ("name", "topic", "kind")}
    status.update(url=req["url"], ok=False, items=0, error=None)
    try:
        r = client.get(req["url"])
        status["status_code"] = r.status_code
        if r.status_code >= 400:
            status["error"] = f"HTTP {r.status_code}"
            return {"status": status, "items": []}
        feed = feedparser.parse(r.content)
    except Exception as exc:  # 网络错误如实记录为缺口，不中断整批抓取
        status["error"] = str(exc)[:200]
        return {"status": status, "items": []}

    items = []
    for e in feed.entries:
        title = _clean_text(e.get("title", ""), 200)
        link = (e.get("link") or "").strip()
        if not title or not link:
            continue
        dt = _entry_time(e)
        if dt and dt < cutoff:
            continue
        publisher = ""
        src = e.get("source")
        if req["kind"] == "google_news":
            publisher = (src.get("title") if isinstance(src, dict) else "") or ""
            # Google News 标题形如「标题 - 媒体名」，摘要只是链接 HTML，没有信息量
            if publisher and title.endswith(f" - {publisher}"):
                title = title[: -len(publisher) - 3].strip()
            summary = ""
        else:
            publisher = req["name"]
            summary = _clean_text(e.get("summary", "") or e.get("description", ""), 240)
        items.append({
            "topic": req["topic"],
            "title": title,
            "url": link,
            "source": publisher or req["name"],
            "via": req["kind"],
            "signal_level": req["signal_level"],
            "published_at": dt.isoformat().replace("+00:00", "Z") if dt else None,
            "summary": summary,
        })
        if len(items) >= max_items:
            break
    status.update(ok=True, items=len(items))
    return {"status": status, "items": items}


def _norm_title(t: str) -> str:
    t = re.sub(r"[^0-9a-z一-鿿]+", "", t.lower())
    return t


def _is_excluded(title: str, words: list[str]) -> bool:
    low = title.lower()
    return any(w.lower() in low for w in words if w)


def fetch_industry_signals(
    *,
    focus_path: str | Path = DEFAULT_FOCUS,
    sources_path: str | Path = DEFAULT_SOURCES,
    out_path: str | Path = DEFAULT_OUTPUT / "raw_signals.json",
    days: int = 7,
    max_items_per_source: int = 8,
    timeout_seconds: int = 15,
) -> dict[str, Any]:
    """按 focus.md 抓取行业媒体 RSS + Google News，过滤、去重后写入 out_path。"""
    days = max(1, min(int(days or 7), 30))
    topics, global_exclude = parse_focus(Path(focus_path).read_text(encoding="utf-8"))
    plan = _plan_requests(topics, _read_sources(sources_path), days)
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(days=days)

    with httpx.Client(timeout=timeout_seconds, follow_redirects=True, headers={"User-Agent": USER_AGENT}) as client:
        with ThreadPoolExecutor(max_workers=8) as pool:
            results = list(pool.map(lambda r: _fetch_one(client, r, cutoff, max_items_per_source), plan))

    excludes = {t.name: t.exclude + global_exclude for t in topics}
    seen: list[str] = []
    items: list[dict[str, Any]] = []
    dropped = {"excluded": 0, "duplicate": 0}
    for res in results:
        for it in res["items"]:
            if _is_excluded(it["title"], excludes.get(it["topic"], [])):
                dropped["excluded"] += 1
                continue
            key = _norm_title(it["title"])
            if any(key == k or SequenceMatcher(None, key, k).ratio() > 0.9 for k in seen):
                dropped["duplicate"] += 1
                continue
            seen.append(key)
            items.append(it)

    level_rank = {"S": 0, "A": 1, "B": 2}
    items.sort(key=lambda x: (x["topic"], level_rank.get(x["signal_level"], 3), -(_ts(x["published_at"]))))
    order = {t.name: i for i, t in enumerate(topics)}
    items.sort(key=lambda x: order.get(x["topic"], 99))
    for i, it in enumerate(items, start=1):
        it["id"] = f"S{i:03d}"

    statuses = [r["status"] for r in results]
    coverage = []
    for t in topics:
        st = [s for s in statuses if s["topic"] == t.name]
        if not st:
            continue
        coverage.append({
            "topic": t.name,
            "items": sum(1 for it in items if it["topic"] == t.name),
            "requests_ok": sum(1 for s in st if s["ok"]),
            "requests_failed": [s["name"] for s in st if not s["ok"]],
        })

    payload = {
        "generated_at": now.isoformat().replace("+00:00", "Z"),
        "window": {
            "days": days,
            "start": cutoff.date().isoformat(),
            "end": now.date().isoformat(),
        },
        "topics": [t.as_dict() for t in topics if any(c["topic"] == t.name for c in coverage)],
        "coverage": coverage,
        "dropped": dropped,
        "requests": statuses,
        "items": items,
    }
    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {
        "out_path": _rel(out),
        "window": payload["window"],
        "total_items": len(items),
        "coverage": coverage,
        "dropped": dropped,
        "next": "按主题调用 get_signals 阅读信号，然后写 insights.json，最后调用 build_weekly_report。",
    }


def _ts(iso: str | None) -> float:
    if not iso:
        return 0.0
    try:
        return datetime.fromisoformat(iso.replace("Z", "+00:00")).timestamp()
    except ValueError:
        return 0.0


def _load_signals(path: str | Path) -> dict[str, Any]:
    p = Path(path)
    if not p.is_file():
        raise FileNotFoundError(f"找不到 {p}，请先调用 fetch_industry_signals。")
    return json.loads(p.read_text(encoding="utf-8"))


def get_signals(
    *,
    topic: str | None = None,
    signals_path: str | Path = DEFAULT_OUTPUT / "raw_signals.json",
    limit: int = 40,
) -> dict[str, Any]:
    """返回精简信号列表（id/主题/来源/日期/标题/摘要），供智能体分析与引用。"""
    data = _load_signals(signals_path)
    rows = [it for it in data["items"] if not topic or it["topic"] == topic]
    limit = max(1, min(int(limit or 40), 80))
    return {
        "window": data["window"],
        "topic": topic or "全部",
        "total": len(rows),
        "returned": min(len(rows), limit),
        "items": [
            {
                "id": it["id"],
                "topic": it["topic"],
                "source": it["source"],
                "date": (it["published_at"] or "")[:10],
                "title": it["title"],
                **({"summary": it["summary"]} if it["summary"] else {}),
            }
            for it in rows[:limit]
        ],
    }


def search_signals(
    *,
    keyword: str,
    signals_path: str | Path = DEFAULT_OUTPUT / "raw_signals.json",
    limit: int = 20,
) -> dict[str, Any]:
    """客户雷达：按关键词（客户名、竞品名、产品名）在本周信号的标题、摘要、来源里搜索，不区分大小写。"""
    word = (keyword or "").strip()
    if not word:
        raise ValueError("keyword 不能为空，例如「宁德时代」「Kaeser」")
    data = _load_signals(signals_path)
    low = word.lower()
    hits = [
        it for it in data["items"]
        if low in f"{it['title']} {it['summary']} {it['source']}".lower()
    ]
    limit = max(1, min(int(limit or 20), 50))
    return {
        "keyword": word,
        "window": data["window"],
        "total": len(hits),
        "items": [
            {
                "id": it["id"],
                "topic": it["topic"],
                "source": it["source"],
                "date": (it["published_at"] or "")[:10],
                "title": it["title"],
                "url": it["url"],
            }
            for it in hits[:limit]
        ],
    }


# --------------------------------------------------------------------------- #
# 校验 + 兜底 + 渲染
# --------------------------------------------------------------------------- #

def _pick(value: Any, allowed: list[str], default: str) -> str:
    v = str(value or "").strip()
    return next((a for a in allowed if a in v), default)


def _validate_insights(raw: Any, by_id: dict[str, dict[str, Any]], topic_names: list[str]) -> tuple[dict[str, Any] | None, list[str]]:
    """把智能体写的 insights.json 规整成固定结构；引用必须是真实存在的信号 ID。"""
    warnings: list[str] = []
    if not isinstance(raw, dict) or not isinstance(raw.get("topics"), list):
        return None, ["insights.json 缺少 topics 数组"]

    topics_out = []
    for t in raw["topics"]:
        if not isinstance(t, dict):
            continue
        name = str(t.get("topic") or t.get("name") or "").strip()
        hotspots = []
        for h in t.get("hotspots") or []:
            if not isinstance(h, dict) or not str(h.get("title") or "").strip():
                continue
            refs = [str(r).strip() for r in (h.get("refs") or h.get("references") or []) if str(r).strip()]
            valid = [r for r in refs if r in by_id]
            bad = [r for r in refs if r not in by_id]
            if bad:
                warnings.append(f"「{h['title']}」引用了不存在的信号 {bad}，已忽略")
            if not valid:
                warnings.append(f"「{h['title']}」没有有效引用，已剔除（周报只保留有出处的结论）")
                continue
            hotspots.append({
                "title": str(h["title"]).strip(),
                "what_happened": str(h.get("what_happened") or "").strip(),
                "impact": str(h.get("impact") or "").strip(),
                "impact_area": _pick(h.get("impact_area"), IMPACT_AREAS, "市场"),
                "level": _pick(h.get("level"), LEVELS, "中"),
                "references": [_ref(by_id[r]) for r in valid],
            })
        if hotspots:
            topics_out.append({"name": name, "hotspots": hotspots})

    if not topics_out:
        return None, warnings + ["insights.json 里没有任何带有效引用的热点"]

    order = {n: i for i, n in enumerate(topic_names)}
    topics_out.sort(key=lambda t: order.get(t["name"], 99))
    summary = [str(s).strip() for s in raw.get("summary") or [] if str(s).strip()]
    actions = []
    for a in raw.get("actions") or []:
        if isinstance(a, dict) and str(a.get("action") or "").strip():
            actions.append({
                "owner": str(a.get("owner") or "业务团队").strip(),
                "action": str(a["action"]).strip(),
                "basis": str(a.get("basis") or "").strip(),
            })
    return {"summary": summary, "topics": topics_out, "actions": actions}, warnings


def _ref(it: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": it["id"],
        "title": it["title"],
        "url": it["url"],
        "source": it["source"],
        "published_at": it["published_at"],
    }


def _fallback_insights(signals: dict[str, Any], per_topic: int = 4) -> dict[str, Any]:
    """无 LLM 结果时的确定性兜底：每个主题按标题相似度归并，取信号最多的几组。"""
    topics_out = []
    for cov in signals["coverage"]:
        rows = [it for it in signals["items"] if it["topic"] == cov["topic"]]
        groups: list[list[dict[str, Any]]] = []
        for it in rows:
            key = _norm_title(it["title"])
            for g in groups:
                if SequenceMatcher(None, key, _norm_title(g[0]["title"])).ratio() > 0.55:
                    g.append(it)
                    break
            else:
                groups.append([it])
        groups.sort(key=len, reverse=True)
        hotspots = [
            {
                "title": g[0]["title"],
                "what_happened": f"{g[0]['source']} 等 {len(g)} 条报道。" if len(g) > 1 else f"来自 {g[0]['source']}。",
                "impact": "（兜底模式：未经智能体研判，请人工评估对业务的影响）",
                "impact_area": "市场",
                "level": "中" if len(g) > 1 else "低",
                "references": [_ref(x) for x in g[:3]],
            }
            for g in groups[:per_topic]
        ]
        if hotspots:
            topics_out.append({"name": cov["topic"], "hotspots": hotspots})
    return {
        "summary": [f"本周共采集 {len(signals['items'])} 条行业信号，以下为按主题归并的高频事件（未经智能体研判）。"],
        "topics": topics_out,
        "actions": [],
    }


def _week_label(end: str) -> str:
    d = datetime.fromisoformat(end)
    y, w, _ = d.isocalendar()
    return f"{y}-W{w:02d}"


def _render_markdown(report: dict[str, Any]) -> str:
    p = report["period"]
    lines = [
        f"# 行业洞察周报 · {p['week']}",
        "",
        f"> 时间窗：{p['start']} ~ {p['end']}（近 {p['days']} 天） · 生成时间：{report['generated_at'][:16].replace('T', ' ')} UTC"
        f" · 模式：{'智能体研判' if report['mode'] == 'llm' else '兜底（未经智能体研判）'}",
        "",
        "## 本周摘要",
        "",
    ]
    lines += [f"- {s}" for s in report["summary"]] or ["- （无）"]
    lines += ["", "## 本周动态", ""]
    for t in report["topics"]:
        lines += [f"### {t['name']}", ""]
        for h in t["hotspots"]:
            lines.append(f"**{h['title']}** · `{h['impact_area']}·{h['level']}`")
            lines.append("")
            if h["what_happened"]:
                lines.append(f"- 发生了什么：{h['what_happened']}")
            if h["impact"]:
                lines.append(f"- 对我们的影响：{h['impact']}")
            refs = "；".join(f"[{r['source']}]({r['url']})" for r in h["references"])
            lines.append(f"- 来源：{refs}")
            lines.append("")

    lines += ["## 对业务的影响", "", "| 影响方向 | 等级 | 事件 | 行业 |", "|---|---|---|---|"]
    rows = [(h, t["name"]) for t in report["topics"] for h in t["hotspots"]]
    rank = {a: i for i, a in enumerate(IMPACT_AREAS)}
    lv = {l: i for i, l in enumerate(LEVELS)}
    rows.sort(key=lambda x: (rank[x[0]["impact_area"]], lv[x[0]["level"]]))
    for h, name in rows:
        lines.append(f"| {h['impact_area']} | {h['level']} | {h['title']} | {name} |")

    lines += ["", "## 行动建议", ""]
    if report["actions"]:
        lines += ["| 负责团队 | 建议动作 | 依据 |", "|---|---|---|"]
        lines += [f"| {a['owner']} | {a['action']} | {a['basis']} |" for a in report["actions"]]
    else:
        lines.append("（兜底模式不生成行动建议，请由智能体研判后补充）")

    lines += ["", "## 数据覆盖与缺口", "", "| 行业 | 信号条数 | 成功请求 | 失败的源 |", "|---|---|---|---|"]
    for c in report["coverage"]:
        failed = "、".join(c["requests_failed"]) or "—"
        lines.append(f"| {c['topic']} | {c['items']} | {c['requests_ok']} | {failed} |")
    lines += [
        "",
        "---",
        "",
        "说明：每条结论都附原文链接，引用由工具按信号 ID 回填，模型不能自行编造链接；"
        "Google News 结果为聚合检索，请以原文为准。",
        "",
    ]
    return "\n".join(lines)


def build_weekly_report(
    *,
    insights_path: str | Path = DEFAULT_OUTPUT / "insights.json",
    signals_path: str | Path = DEFAULT_OUTPUT / "raw_signals.json",
    out_dir: str | Path = DEFAULT_OUTPUT,
    frontend_dir: str | Path | None = DEFAULT_FRONTEND,
) -> dict[str, Any]:
    """校验智能体写的 insights.json（不合格则兜底），渲染 report.md + report.json。"""
    signals = _load_signals(signals_path)
    by_id = {it["id"]: it for it in signals["items"]}
    topic_names = [c["topic"] for c in signals["coverage"]]

    warnings: list[str] = []
    insights = None
    ip = Path(insights_path)
    if ip.is_file():
        try:
            insights, warnings = _validate_insights(json.loads(ip.read_text(encoding="utf-8")), by_id, topic_names)
        except json.JSONDecodeError as exc:
            warnings = [f"insights.json 不是合法 JSON：{exc}"]
    else:
        warnings = [f"没有找到 {_rel(ip)}，使用兜底模式"]

    mode = "llm" if insights else "fallback"
    insights = insights or _fallback_insights(signals)
    w = signals["window"]
    report = {
        "title": f"行业洞察周报 · {_week_label(w['end'])}",
        "period": {"week": _week_label(w["end"]), **w},
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "mode": mode,
        **insights,
        "coverage": signals["coverage"],
    }

    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    md_path, json_path = out / "report.md", out / "report.json"
    md_path.write_text(_render_markdown(report), encoding="utf-8")
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    written = [_rel(md_path), _rel(json_path)]
    if frontend_dir:
        fd = Path(frontend_dir)
        fd.mkdir(parents=True, exist_ok=True)
        for src in (md_path, json_path):
            shutil.copyfile(src, fd / src.name)
            written.append(_rel(fd / src.name))

    return {
        "mode": mode,
        "title": report["title"],
        "topics": [{"name": t["name"], "hotspots": len(t["hotspots"])} for t in report["topics"]],
        "actions": len(report["actions"]),
        "warnings": warnings,
        "written": written,
    }
