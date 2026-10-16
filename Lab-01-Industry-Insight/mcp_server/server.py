"""行业洞察 MCP 服务器（stdio）。

VS Code 通过仓库根目录的 .vscode/mcp.json 启动它；Copilot Agent 模式就能调用
下面五个工具 —— 这就是「给智能体装上手去取数据」。

手动调试：python Lab-01-Industry-Insight/mcp_server/server.py（会等待 stdio 输入）。
"""

from __future__ import annotations

import json
from typing import Any

from mcp.server import MCPServer

import industry_tools as tools

server = MCPServer(
    name="industry-insight",
    instructions=(
        "行业洞察工具。标准流程：read_focus 看关注清单 → fetch_industry_signals 抓取近 N 天信号 → "
        "按主题 get_signals 阅读 → 把研判结果作为 insights 参数传给 build_weekly_report 生成周报。"
    ),
)


@server.tool()
def read_focus() -> dict[str, Any]:
    """读取 focus.md（行业关注清单），返回每个行业的搜索词、排除词、关注点和对应的媒体源数量。"""
    return tools.read_focus()


@server.tool()
def fetch_industry_signals(days: int = 7, max_items_per_source: int = 8) -> dict[str, Any]:
    """按 focus.md 抓取行业媒体 RSS 与 Google News，过滤、去重后写入 output/raw_signals.json。

    返回每个行业的信号条数和抓取失败的源（缺口如实记录）。days 为时间窗（1~30 天）。
    """
    return tools.fetch_industry_signals(days=days, max_items_per_source=max_items_per_source)


@server.tool()
def get_signals(topic: str | None = None, limit: int = 40) -> dict[str, Any]:
    """读取已抓取的信号（精简版：id/行业/来源/日期/标题/摘要）。

    topic 填 focus.md 里的行业标题（如「锂电」），留空返回全部。写洞察时用 id（如 S012）引用出处。
    """
    return tools.get_signals(topic=topic, limit=limit)


@server.tool()
def search_signals(keyword: str, limit: int = 20) -> dict[str, Any]:
    """客户雷达：按客户名、竞品名或产品名搜索本周抓到的信号，返回标题、来源、日期和原文链接。

    用户问「某家公司 / 某个竞品本周有什么动静」时调用，例如 keyword 填「宁德时代」「Kaeser」。
    需要先调用过 fetch_industry_signals。
    """
    return tools.search_signals(keyword=keyword, limit=limit)


@server.tool()
def build_weekly_report(insights: dict[str, Any] | None = None) -> dict[str, Any]:
    """保存研判结果并生成周报（report.md + report.json，同步到 frontend/）。

    insights 结构：{"summary": [..], "topics": [{"topic": 行业, "hotspots": [{"title", "what_happened",
    "impact", "impact_area": 销售机会|产品|市场|风险, "level": 高|中|低, "refs": ["S012"]}]}],
    "actions": [{"owner", "action", "basis"}]}。传入后会先写到 output/insights.json；不传则读已有文件。
    引用必须是真实的信号 id，工具会回填原文链接；不合格时自动走兜底模式，
    返回 mode（llm / fallback）和 warnings，请根据 warnings 修正后重新调用。
    """
    if insights is not None:
        path = tools.DEFAULT_OUTPUT / "insights.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(insights, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return tools.build_weekly_report()


if __name__ == "__main__":
    server.run()
