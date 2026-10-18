# 培训前准备

本课全程用 **GitHub Codespaces**（浏览器里的 VS Code），学员电脑**不需要安装任何软件**，只需要现代浏览器和能上网。

## 学员

| 项目 | 要求 | 用于 |
|---|---|---|
| 浏览器 | 最新版 Edge / Chrome | 全部 |
| GitHub 账号 | 有 **Copilot Business / Enterprise** 席位；个人账号能 fork 公开仓库（不是 EMU 账号） | 全部 |
| 自己的 fork | Fork 课程仓库到个人账号，**不要只复制 main**；启用 fork 的 Actions，并允许 Actions 建 PR | 全部、Lab-01 云端版 |
| Fine-grained PAT | Resource owner 选个人账号，权限 **Account → Copilot Requests = Read**；存成个人 Codespaces secret 和 fork 的 Actions secret `COPILOT_GITHUB_TOKEN`（步骤见 [docs/codespaces.md](docs/codespaces.md)） | Lab-01 云端版、Lab-02、Lab-03 |
| 已建好的 Codespace | 在自己的 fork 上建一次（没有预构建，第一次 5~8 分钟），用个人账号的免费额度 | 全部 |
| Copilot Studio 账号 | 不用提前准备：Lab-03 开始时讲师发课堂账号卡片（`user01` 这类）；首次登录可能要求改密码，或用手机装 Microsoft Authenticator 验证，请带手机 | Lab-03 |

## 网络（需放通）

- `github.com`、`api.github.com`、`*.githubusercontent.com`
- `*.github.dev`、`*.app.github.dev`（Codespaces 编辑器与端口转发）
- `*.githubcopilot.com`（Copilot 模型与 Agent 调用）
- `news.google.com` 及行业媒体网站（Lab-01 抓取在 Codespace 里进行，走 GitHub 的网络，一般不受公司网络影响）
- `copilotstudio.microsoft.com`、`*.powerplatform.com`、`login.microsoftonline.com`（Lab-03）

## 组织与租户（讲师 / 管理员）

见 [INSTRUCTOR.md](INSTRUCTOR.md) 的「T-7 天」：仓库公开与学员 fork、个人账号的 Codespaces 计费、Copilot 的 Agent / MCP / CLI 策略、
Copilot Studio 授权与 DLP。

## Codespace 里已经装好的东西（无需学员操作）

Python 3.12 + 虚拟环境 `.venv`（httpx、feedparser、mcp、pytest、markitdown）· Node.js 24 · Lab-02 的 npm 依赖
（Next.js、Copilot SDK、pptxgenjs、playwright、sharp）· Playwright Chromium · GitHub CLI + gh-aw 扩展 ·
VS Code 扩展 GitHub Copilot / Copilot Chat / Python。
