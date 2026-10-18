#!/usr/bin/env bash
# =============================================================================
# Lab-03 连通自检：在 Copilot Studio 里建连接器之前，先确认公网地址能用。
#
#   bash Lab-03-Copilot-Studio/smoke-test.sh
#
# 前提：Lab-02 服务已在 3000 端口运行（npm run dev），且端口 3000 已设为 Public。
# 不会生成 PPT（不消耗 Copilot 额度），只检查连通性、鉴权和周报接口。
# =============================================================================
set -uo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
ENV_FILE="$REPO_ROOT/Lab-02-Knowledge-Summary/.env"

if [[ -z "${CODESPACE_NAME:-}" || -z "${GITHUB_CODESPACES_PORT_FORWARDING_DOMAIN:-}" ]]; then
  echo "✘ 这不是 Codespace 环境，拼不出公网地址。本地运行请自行设置 PUBLIC_BASE_URL。"
  exit 1
fi

HOST="${CODESPACE_NAME}-3000.${GITHUB_CODESPACES_PORT_FORWARDING_DOMAIN}"
BASE="https://${HOST}"
KEY="$(sed -nE 's/^[[:space:]]*LAB_API_KEY=[[:space:]]*//p' "$ENV_FILE" 2>/dev/null | tail -1)"

# 值的前后留空格：终端里双击时中文全角标点不算分隔符，挨着会把「填：」一起选中
echo "openapi.yaml 里的 host 填： ${HOST} （title 记得改成「Atlas Agent Labs · 你的账号」，如 user01）"
echo "连接器的 API 密钥填： ${KEY:-（未设置，请先运行 bash .devcontainer/set-key.sh）}"
echo

pass=0; fail=0
check() {  # check <说明> <期望状态码> <curl 参数...>
  local name="$1" want="$2"; shift 2
  local got
  got="$(curl -s -o /dev/null -w '%{http_code}' --max-time 20 "$@")"
  if [[ "$got" == "$want" ]]; then
    echo "✔ ${name}（HTTP ${got}）"; pass=$((pass + 1))
  else
    echo "✘ ${name}：期望 HTTP ${want}，实际 ${got}"; fail=$((fail + 1))
  fi
}

check "本机服务在运行" 200 "http://localhost:3000/"
check "公网地址可访问（端口 3000 已设为 Public）" 200 "${BASE}/"
if [[ -n "$KEY" ]]; then
  check "不带密钥会被拒绝" 401 "${BASE}/api/insight/latest"
  check "带密钥能读到周报" 200 -H "x-api-key: ${KEY}" "${BASE}/api/insight/latest?topic=%E6%96%B0%E8%83%BD%E6%BA%90%E6%B1%BD%E8%BD%A6"
fi

echo
if (( fail > 0 )); then
  echo "有 ${fail} 项没通过。公网地址返回 302/401：端口还是 Private，到「端口」面板右键 3000 → 端口可见性 → Public。"
  exit 1
fi
echo "全部通过（${pass} 项），可以去 Copilot Studio 建连接器了。"
