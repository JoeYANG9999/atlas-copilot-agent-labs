# Lab-02 · 知识总结智能体 · Skills

> **业务场景**：工程师读完一篇技术文章、竞品产品页或展会报道，要给领导做一份几页的汇报。
> 读、提炼、排版往往要花半天，而且每个人做出来的格式都不一样。

实验时长：约 50 分钟。前置：Codespace 已就绪，并运行过 `bash .devcontainer/set-key.sh` 填好 Copilot 令牌。

## 智能体怎么干活

```text
链接 / 素材 ──▶ knowledge2ppt skill（团队汇报规范：结论 → 要点 → 建议）
                   │ 读全文 → 提炼观点和数据 → 写分页大纲 outline.md
                   ▼
                pptx skill（把大纲渲染成可编辑的 .pptx）
```

两个 Skill 都在仓库根目录 [.github/skills/](../.github/skills/)：

- [knowledge2ppt/SKILL.md](../.github/skills/knowledge2ppt/SKILL.md)：**你要改的**，写着团队的汇报规范；
- `pptx/`：通用的 PPT 生成能力（HTML → PPTX），不用改。

同一份 Skill 有两种用法：在 VS Code Chat 里直接用（第 1 步），或者通过 Copilot SDK 做成网页服务（第 4 步）。

## 第 1 步：在 Chat 里用 Skill（10 分钟）

1. 打开 Copilot Chat，切到 **Agent** 模式。
2. 输入（换成任意一篇你关心的文章）：
   ```text
   把这篇文章总结成 6 页汇报 PPT，风格用咨询风：url=https://semiengineering.com/
   ```
3. 观察：Copilot 自动选中 `knowledge2ppt` skill → 读网页 → 写 `outline.md` → 调 `pptx` skill → 生成 `.pptx`。
4. 在资源管理器里右键生成的 `.pptx` → **下载**，用 PowerPoint 打开，确认每页标题都是结论句、文字可编辑。

## 第 2 步：改 SKILL.md，把团队的汇报规范写成技能（15 分钟）

打开 `knowledge2ppt/SKILL.md`，找到「团队汇报规范」这一段，按你们团队的真实习惯改，例如：

- 第 2 页改成「一页纸摘要」：背景 / 结论 / 需要的支持；
- 每页右上角写「仅供内部讨论」；
- 建议页必须写预计投入和时间表；
- 竞品类素材必须加一页「对我们的影响」。

改完再跑一次第 1 步的提示词，对比前后两份 PPT。

> 💡 **试一试 · 让 Copilot 帮你改规范**：
> `#file:.github/skills/knowledge2ppt/SKILL.md 我们给销售总监汇报时习惯先讲客户机会再讲竞品，帮我改「团队汇报规范」`

## 第 3 步：让 Copilot 给网页加「公司品牌风」（10 分钟）

新开 Chat 会话，把配色换成你们公司的：

```text
给 Lab-02 网页加一种 PPT 风格「公司品牌风」：白底，主色深蓝 #003A70，强调色亮黄 #FFC20E，标题加粗，每页底部一条深蓝细条。只改 Lab-02-Knowledge-Summary/lib/styles.ts 和风格预览的 CSS，改完跑 npm run typecheck。
```

**期望结果**：改了 2 个文件，`npm run typecheck` 通过，点 **Keep**。下一步在网页上就能选「公司品牌风」。
卡住了可以拿参考答案：`git restore --source origin/answer/lab02 -- Lab-02-Knowledge-Summary/lib/styles.ts Lab-02-Knowledge-Summary/app/globals.css`

> 模型会按风格描述排版，但颜色不一定严格照搬。想要严格的品牌色，在风格描述里写「必须使用且只使用以下色值」。

## 第 4 步：用 Copilot SDK 把它做成网页服务（20 分钟）

1. 启动服务：
   ```bash
   cd Lab-02-Knowledge-Summary
   npm run dev
   ```
   Codespace 弹出端口 3000 的提示时，点 **在浏览器中打开**。
2. 在页面里选素材来源：
   - **网页链接**：贴一篇文章地址；
   - **本周行业洞察周报**：直接用 Lab-01 生成的周报，可以只选一个行业。
3. 点「开始生成 PPT」，页面会实时显示 Copilot SDK 的事件流，完成后出现下载链接。

**代码导读**（让 Copilot 带你读）：

| 文件 | 作用 |
|---|---|
| `lib/copilot.ts` | 创建 Copilot SDK 会话，挂载 `.github/skills`，把素材和规范拼成提示词 |
| `lib/generate.ts` | 一次生成的完整流程：准备素材 → 调 SDK → 等 .pptx 落盘 |
| `app/api/generate/stream/route.ts` | 网页用：SSE 实时推送事件 |
| `app/api/jobs/` | 给外部系统用：提交任务立即返回任务号，后台排队生成（Lab-03 的 Copilot Studio 调这个） |
| `app/api/insight/latest/route.ts` | 读 Lab-01 的周报 `report.json` |

> 💡 **试一试 · @workspace**：
> `@workspace 网页上点「开始生成」之后，请求经过了哪些文件？Copilot SDK 是在哪里加载 skill 的？`

## 对外 API（Lab-03 会用到）

| 接口 | 说明 |
|---|---|
| `GET /api/insight/latest?topic=新能源汽车` | 最新一期行业洞察，可按行业筛选；`topic=全部` 返回整份 |
| `POST /api/jobs/insight` | 把周报做成 PPT：`{"topic":"锂电","pages":6,"style":"consulting"}`，立即返回 `jobId` 和进度页链接 |
| `POST /api/jobs/webpage` | 把网页做成 PPT：`{"url":"https://...","pages":6,"style":"consulting"}` |
| `POST /api/jobs` | 通用版（用 `sourceType` 区分，curl 调试用） |
| `GET /api/jobs/{jobId}` | 查进度，成功后返回 `downloadUrl` |
| `/jobs/{jobId}` | 进度页（网页），完成后可直接下载 |

`.env` 里设置了 `LAB_API_KEY` 时，上表的 `/api/insight/latest` 和 `/api/jobs…` 接口都要带请求头 `x-api-key`。
网页本身不检查密钥：首页（以及它用的 `/api/generate/stream`）、`/insight`、进度页和下载链接都能直接打开，首页还能直接生成 PPT、花你的 Copilot 额度，所以端口设成 Public 期间别把地址外传，用完改回 Private。本机调试示例：

```bash
KEY=$(sed -n 's/^LAB_API_KEY=//p' Lab-02-Knowledge-Summary/.env)
curl -s -X POST localhost:3000/api/jobs/insight -H "x-api-key: $KEY" -H 'content-type: application/json' \
  -d '{"topic":"新能源汽车","pages":4}'
```

## 遇到问题

| 现象 | 处理 |
|---|---|
| 「无法列出模型，请确认环境变量已配置」 | 令牌没填或无效：重新运行 `bash .devcontainer/set-key.sh`，然后重启 `npm run dev`；令牌正确仍报错，多半是组织没开 Copilot CLI 策略，找讲师 |
| 网页生成失败，日志里 `Tool failed: unexpected user permission response` | fork 里是 2026-10-18 修复之前的代码（Copilot CLI 1.0.43 起「同意执行」的回复要写 `approve-once`）：GitHub 上你的 fork → **Sync fork** → **Update branch**（别点 Discard commits），Codespace 里 `git pull`，再在 `Lab-02-Knowledge-Summary` 里 `npm ci && npm run dev`（npm ci 按锁文件装上对应版本的 Copilot CLI） |
| 生成到一半报找不到 `playwright` / `pptxgenjs` | 终端运行 `echo $NODE_PATH`，应指向 `Lab-02-Knowledge-Summary/node_modules`；不对就重建 Codespace |
| 报 Chromium 缺失 | `cd Lab-02-Knowledge-Summary && npx playwright install --with-deps chromium` |
| 「还没有行业洞察周报」 | 先完成 Lab-01，或确认 `Lab-01-Industry-Insight/frontend/report.json` 存在 |
