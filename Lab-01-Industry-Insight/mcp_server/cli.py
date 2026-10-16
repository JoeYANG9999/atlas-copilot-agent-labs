"""gh-aw mcp-scripts 的调用入口：python cli.py <工具名> [JSON 参数]。

和 server.py 调的是同一套 industry_tools 函数，只是换成命令行形式，
方便在 .github/workflows/industry-insight.md 的 mcp-scripts 里调用。
"""

from __future__ import annotations

import json
import sys

import industry_tools as tools

COMMANDS = {
    "read_focus": tools.read_focus,
    "fetch_industry_signals": tools.fetch_industry_signals,
    "get_signals": tools.get_signals,
    "search_signals": tools.search_signals,
    "build_weekly_report": tools.build_weekly_report,
}


def main() -> int:
    if len(sys.argv) < 2 or sys.argv[1] not in COMMANDS:
        print(f"用法：python cli.py <{'|'.join(COMMANDS)}> [JSON 参数]", file=sys.stderr)
        return 2
    raw = sys.argv[2] if len(sys.argv) > 2 else "{}"
    args = {k: v for k, v in json.loads(raw or "{}").items() if v not in (None, "")}
    result = COMMANDS[sys.argv[1]](**args)
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
