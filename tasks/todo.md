# atlas-copilot-agent-labs · 改造计划

来源：阿特拉斯中国 · 「两个智能体解决什么」实验详解页（2026-10-16 确认）。
基线代码：`ITD-NextDimension/github-sdk` 的 Lab-01（gh-aw + MCP 脚本）与 Lab-03（Skills + Copilot SDK）。

## 已定决策

- 仓库：`atlascopco-Lab/atlas-copilot-agent-labs`，2026-10-16 由 ITD-NextDimension 转移过来；~~学员直接在本仓库开 Codespace，不 fork~~ → 2026-10-17 改为**仓库公开、学员各自 fork**（见文末「fork 模式」）。
- Lab-01 学员路线：Codespace 内 VS Code Agent 模式 + 标准 MCP 服务器 + `prompt.md`；gh-aw 每周定时出周报由讲师仓库演示，两边共用同一个 MCP 服务器。
- Lab-03（Copilot Studio）：指南 + OpenAPI 2.0 连接器 + 异步 API；Codespace 3000 端口设 Public 供 Studio 调用；讲师提供演示租户账号。
- 数据源：行业媒体 RSS + Google News RSS 关键词兜底，先实测再定，缺口如实标注。

## 任务

### 0. 骨架
- [x] 新建本地仓库，拷入 Lab-01 / Lab-03 基线
- [x] `.devcontainer/`（onCreate 装依赖 + Playwright，postCreate 轻量初始化，set-key.sh）
- [x] 根 `.gitignore` 放行 `.vscode/mcp.json`

### 1. Lab-01 行业洞察智能体 · MCP
- [x] 数据源连通性实测（新能源汽车 / 锂电 / 半导体 / 压缩空气与真空竞品 / 节能降碳政策）→ `focus.md` + `input/sources.json`
- [x] 重写工具为 `industry_tools.py`（时间窗 7 天、按行业打标、引用校验）
- [x] 标准 MCP 服务器（stdio）+ `.vscode/mcp.json`
- [x] `.github/prompts/industry-insight.prompt.md`，含学员可改的「关注行业」区块
- [x] 周报结构：摘要 → 分行业 → 竞品新品 → 政策 → 对阿特拉斯业务的影响 → 行动建议；输出 report.md + report.json
- [x] gh-aw `industry-insight.md`：每周定时 + 白名单与数据源对齐 + 传路径不传内联 JSON；`gh aw compile`
- [x] 本地兜底流水线跑通

### 2. Lab-02 知识总结智能体 · Skills + SDK
- [x] `knowledge2ppt` Skill：结论 → 要点 → 建议，含学员可改的「团队汇报规范」区块
- [x] 修 `lib/copilot.ts` 里的 skill 名
- [x] 异步 API：`POST /api/jobs`、`GET /api/jobs/{id}`、进度页、下载；`x-api-key`
- [x] `/api/insight/latest` + `/insight` 页面（读 Lab-01 周报）
- [x] typecheck + build；真实生成 .pptx（企业开启 Copilot CLI 策略后，SDK 与 Studio 两条路都生成成功）

### 3. Lab-03 串起来 · Copilot Studio
- [x] `openapi.yaml`（Swagger 2.0）
- [x] Studio 分步指南（建智能体、导入连接器、工具描述、对话示例）
- [x] 端口 Public、空闲超时、DLP、超时处理注意事项

### 4. 文档
- [x] README、`docs/codespaces.md`（学员）、`INSTRUCTOR.md`（讲师）、prerequirement

### 5. 发布
- [ ] 建私有仓库并推送，开 Codespaces prebuild，真实触发一次 gh-aw

## Review

- 实测数据源（2026-10-16）：近 7 天 154 条信号，5 个行业均有覆盖、0 个失败源；竞品类噪音较多，靠 focus.md 排除词 + 智能体研判过滤。
- 设计取舍：行业关注清单写在 `focus.md`（一份 Markdown 同时驱动抓取和研判）；周报引用只能用信号 ID，由工具回填链接，模型编不出来源；
  Lab-02 接周报时由服务端把周报写进会话目录当素材，不让 Copilot 回抓自己的公网地址。
- 已验证：Lab-01 单测 3/3、MCP stdio 调用、`gh aw compile` 0 错误；Lab-02 typecheck/build、401 鉴权、行业模糊匹配、任务失败回报；
  `openapi.yaml` 通过 Swagger 2.0 校验；`set-key.sh` 沙盒测试。
- 未验证：真实生成 .pptx —— 讲师账号 Copilot Business 席位调用 `models.list` 返回 403「not authorized to use this Copilot feature」，
  需在席位所属组织/企业开启 Copilot CLI 策略后复测；devcontainer 需在真实 Codespace 里构建一次；Copilot Studio 导入连接器需在演示租户里走一遍。
- 过程中的失误：`git mv -k` 在未跟踪文件上静默跳过却返回 0，串联的 `rm -rf` 删掉了刚拷入的 pptx skill；已从源仓库恢复并逐文件比对一致。

## Lab-03 实测计划（2026-10-16）

目标：按学员视角把 Lab-03 真实走通一遍 —— Studio 里一句话「看看本周新能源汽车装配行业有什么变化，整理成汇报」→ 返回洞察 + PPT 进度页 → 下载到 PPT；
走完后把 README 改成与真实界面一致。

分工：🤖 = Claude 做；👤 = 必须由用户做（登录/凭据/同意条款）

### A. 服务端（Codespace）
- [x] 👤 设 Codespaces 用户 Secret `COPILOT_GITHUB_TOKEN`（`gh secret set ... --user --app codespaces`），学员也可用这条路代替 set-key.sh
- [x] 🤖 建测试 Codespace（空闲超时 120 分钟），生成 `LAB_API_KEY`，`npm run dev` 后台常驻
- [x] 🤖 端口 3000 设 Public（`gh codespace ports visibility 3000:public`），跑 `smoke-test.sh` 全绿
- [x] 🤖 公网 curl 走一遍 `CreatePresentationJob` → 进度页 → 下载，确认从 Studio 视角可用

### B. Copilot Studio（演示租户，Chrome）
- [x] 👤 在 Chrome 登录 copilotstudio.microsoft.com，确认环境与授权
- [x] 🤖 新建智能体「业务汇报助手」，粘贴 README 里的智能体指令，确认生成式编排开启
- [x] 🤖 工具 → 新建 → REST API，上传填好 host 的 openapi.yaml；三个操作加为工具
- [x] 👤 建连接时粘贴 `LAB_API_KEY`（凭据由用户输入）
- [x] 🤖 测试窗格跑 4 段对话：洞察 / 洞察→PPT / 一句话串起来 / 网页→PPT；核对每次调用的参数与回复

### C. 收尾
- [x] 🤖 按真实界面改 Lab-03 README（菜单名、截图位置、坑），必要时调 openapi 描述或智能体指令
- [ ] 🤖 删除测试 Codespace；Studio 智能体保留给讲师演示（或按用户要求删除）

风险：租户 DLP 拦自定义连接器；组织策略不允许 Public 端口；Studio 连接器超时；REST API 工具界面与文档不一致。

### Lab-03 实测结论（2026-10-16，演示租户 Ontology-trial 环境）

- 5 段测试对话全部通过：洞察 / 洞察→PPT / 查进度 / 网页→PPT / 一句话串起来；Studio 发起的 3 个任务都生成了 PPT。
- 实测改动：openapi 每个字段补描述（否则向导卡住）；生成 PPT 拆成「周报→PPT」「网页→PPT」两个工具、参数全部必填
  （Studio 默认不带可选参数，条件必填会被误追问）；指令避开 `/`（会触发插入菜单吞字）；工具名直接用 openapi 的 summary。
- 待确认：pages/style 改为必填后未在 Studio 重新导入验证（Swagger 校验通过）；回答里的 cite 标记已在指令中禁止，未复测。

## 实操手册（2026-10-17 启动）

目标：按教学设计 v2 出一份品牌风格 HTML 单页实操手册，每一步都有真实截图和「复盘三问」。

### A. v2 落地（参考答案放在 answer/* 分支，main 保持题目状态）
- [x] 热身：周报网页「只看高影响」开关 → `answer/warmup`
- [x] Lab-01：MCP 工具「客户雷达」`search_signals` + 单测 → `answer/lab01`
- [x] Lab-02：网页新增「公司品牌风」 → `answer/lab02`
- [x] ~~gh-aw 学员分支~~ → 改为每人在自己 fork 上手动触发（2026-10-17）；`student/manual-demo` 已删除
- [x] 各 Lab README 与 v2 对齐（题目、提示词、复盘三问）

### B. 真实走一遍并截图（Codespace + Chrome；敏感信息打码）
- [x] 开场：仓库页 → 创建 Codespace → 环境就绪 → set-key
- [x] 热身：@workspace / /explain / Agent 模式改网页 / 自定义指令
- [x] Lab-01：/industry-insight → 改 focus.md → 客户雷达 → 推分支 + Actions 触发 → Issue 结果
- [x] Lab-02：Chat 用 Skill → 改 SKILL.md → 品牌风 → 网页生成 PPT
- [x] Lab-03：端口 Public → smoke-test → Studio 建智能体 / 挂工具 / 测试（54/55 取自 Activity 页 10-16 的实测会话）；「改一处」未截图

### C. 写手册
- [x] docs/manual/index.html + docs/manual/img/，每步：做什么 → 截图 → 应该看到 → 复盘三问；附排障表

## Review 后调整：fork 模式（2026-10-17）

决定：仓库公开；每人 fork、用自己的 PAT / Codespaces / Actions / Copilot 额度；Lab-03 每人导入自己的连接器（title 带名字）。

- [x] 实操手册：课前准备（fork + 两处 Secret + 启用 Actions）、开场 0.1、Lab-01 第 4 步（推 fork、在 fork 上跑 gh-aw）、
      Lab-03 第 2 步（改 host + title、自己导入）、排障新增 5 行、新增「卡住了怎么办」、课后清理 6 项、截图来源说明
- [x] README（fork 开始步骤、手册链接、参考答案表、v2 练习）、Lab-01/02/03 README、docs/codespaces.md、prerequirement.md、INSTRUCTOR.md
- [x] openapi.yaml 头注释、smoke-test 提示改 title；deploy-pages 只在课程仓库运行，并发布手册到 `/manual/`
- [ ] 👤 仓库设为 Public；按需开 Pages（Source = GitHub Actions）
- [ ] 👤 按 fork 流程手动走一遍，补拍 fork / Actions secret / 自己导入连接器的截图（目前沿用旧图）
- [ ] 👤 决定是否删除 Codespace `manual-shots-jjx4746j4pj2p47`（仍在运行，3000 端口 Public）

## fork 实跑（2026-10-17，tarrywang/atlas-copilot-agent-labs，Codespace fork-e2e）

- [x] fork（含 answer/*）、Codespaces secret 范围加 fork、启用 Actions + 允许建 PR、Codespace 建好（显示 paid for by atlascopco-Lab）
- [x] 热身问答；`git restore` 参考答案（warmup、lab02）验证可用
- [x] Lab-01：/industry-insight（llm 模式）→ focus.md 加食品饮料 → Copilot 写客户雷达（4 测试过）→ Restart 5 tools → 重跑周报含食品饮料 → CATL 雷达查询带链接 → push 到 fork
- [x] Lab-02：SKILL.md 加保密标识 → 品牌风（用参考答案）→ 网页按食品饮料 + 品牌风生成 6 页 PPT，每页有「仅供内部讨论」
- [x] Lab-03：smoke-test 4 项过；新建「业务汇报助手 Tarry」（新版多了必填 Solution）；导入 host+title 改过的 openapi，工具组显示「Atlas Agent Labs Tarry」
- [ ] 👤 Studio 建连接需粘贴 LAB_API_KEY，然后跑 4 句测试
- [ ] 👤 设 fork 的 Actions secret 后跑 gh-aw，确认 fork 出现 PR
- [x] 发现：answer/lab02 的品牌色（#0B3C5D/#1C8AD6）与手册提示词（#003A70/#FFC20E）不一致 → 10-17 改 answer/lab02 与提示词一致
- [x] 发现：连接对话框只显示 Display name，没看到 API key 输入框 → 10-17 重跑时有密钥输入框，未复现

## 从头重跑（2026-10-17 晚，分支 docs/rerun-1017）

前置：Studio（Ontology-trial）已清空（智能体、连接器、AIPlugin、连接、Solution）；旧 fork 与 Codespace 已删；PAT 与 Codespaces secret 保留。
分工：🤖 = Claude 按手册操作并截图；👤 = 令牌 / API 密钥相关，Claude 停下来给步骤，等用户做完。文档边跑边改，截图换新。

- [x] 课前：🤖 fork（不只复制 main）→ 🤖 启用 Actions + 允许建 PR → 👤 Codespaces secret 加上新 fork、fork 的 Actions secret
- [x] 开场：🤖 建 Codespace → 信任文件夹 → 界面就绪 → set-key（回车跳过）
- [x] 热身 1~4
- [x] Lab-01 1~4（fork 上手动跑 gh-aw 成功，出 Draft PR #1，含食品饮料 3 个热点）
- [x] Lab-02 1~4
- [x] Lab-03：端口 Public + smoke → 改 openapi → Studio 新建智能体 → 指令 → 关 Web Search → 导入 REST API →
      👤 建连接粘贴 LAB_API_KEY → 挂 4 个工具（Maker-provided credentials）→ 测试 5 句全过 → 改一处
- [x] 文档：手册 / Lab-03 README / codespaces.md / INSTRUCTOR.md 按实测改；截图全换新；讲师手册补 Default Solution 清理流程

### 重跑结论（2026-10-17 晚）

- 新发现并已写进文档：
  1. fork 上定时工作流要单独 Enable，否则没有 Run workflow；启用后每周一会在 fork 上定时跑（课后清理提醒 Disable）。
  2. 首次打开 Codespace 直接弹信任对话框；首建约 3 分钟。
  3. Agent 改网页要请求运行命令十来次（约 6 分钟）；自定义指令第一次没被遵守，追问一句才补注释。
  4. gh-aw 在 fork 上出 Draft PR；fork 默认关 Issues，失败时看运行日志。
  5. Chat 里出 6 页 PPT 实测约 20 分钟（多次撞 html2pptx 版式规则后自修）；Codespace 无 LibreOffice，缩略图失败改用浏览器预览。
  6. 网页生成品牌风 PPT：6 页都有「仅供内部讨论」，但颜色用了相近深蓝、无黄色、细条在顶部。
  7. Studio：New agent 有必填 Solution；导入向导「Create connection」回到 Add tool 对话框；按名字搜工具；新建连接要起显示名；
     **工具改 Maker-provided credentials 后不再弹连接授权**；Agent status 多出 3 条可忽略的提醒。
  8. **Studio 401（connectorAuthorizationError）= 连接里的密钥不是当前 Codespace 的**：用临时日志确认 Studio 带了 32 位 x-api-key 但首尾不匹配；
     Power Automate → Connections → Edit 更新即可，不用重建。
  9. 指令编辑器点击位置会随滚动错位，插到段落中间；未保存时 Cancel → Discard 可恢复。手册示例去掉了「/」。
- 已验证：5 句 Studio 测试全过（洞察 1.6~1.8 秒、提交 PPT 1.2~1.5 秒、查进度 2.3 秒、网页→PPT 2.1 秒），Studio 发起的 PPT 约 4 分钟生成，每页都有 SKILL.md 加的保密标识。
- 过程中的失误：给 api.ts 加调试日志时 shell 转义把 `\n` 变成真换行，导致语法错误约 1 分钟；已从备份恢复，改用 base64 传补丁；
  调试结束后 api.ts 已恢复（git diff 无变化），临时日志已删除。在 VS Code 里用 `code -g` 打开文件后焦点会跳到编辑器，接着打字会写进文件（已 Revert + 手动修复并 node --check 通过）。
- 收尾（10-17 晚）：PR #7 rebase 合并进 main；answer/warmup、lab01、lab02 rebase 到最新 main（各只比 main 多一个提交）并 force push；answer/lab02 品牌色改成与提示词一致（白底、#003A70、#FFC20E、底部深蓝细条）；手册「看答案」改用 `git show origin/answer/…`。
- 遗留：Pages 没开，Deploy GitHub Pages 每次推送都失败（Create Pages site failed，Resource not accessible by integration），需要在仓库 Settings → Pages 选 GitHub Actions。
- [x] 👤 删除测试资源（用户要自己从头再跑）：Studio 智能体「业务汇报助手 Tarry」、Codespace super-space-spoon、fork tarrywang/atlas-copilot-agent-labs；🤖 之后清理 Studio 连接「Atlas · Tarry」、连接器与 AIPlugin、自动生成的 Solution
      （10-17 晚已清：Default Solution 里删 4 个 AIPluginOperation → AIPlugin → 自定义连接器后，连接随之消失；再删「Atlas Agent Labs · Tarry Solution」。
      复查：Agents 0、Custom connectors 0、Connections 0、Solutions 只剩两个内置，Connection references 只剩 SYSTEM 的 Content Conversion / Dataverse）
- [x] 依赖漏洞（PR #8）：Dependabot 实际有 54 个未关告警（2 critical / 29 high / 21 medium / 2 low；之前记的「21 个」不对），全在 Lab-02 的 package-lock.json。
      next / eslint-config-next 15.5.12 → 15.5.28，sharp → ^0.35.5；overrides 固定 @github/copilot 1.0.43、postcss ^8.5.23、image-size ^2.0.3。
      **@github/copilot 不能放开到最新**：1.0.64 起去掉了 index.js，SDK 0.2.2 会报「Copilot CLI not found」（直接 npm audit fix 就会装上 1.0.98）。
      验证：新锁文件对 54 个告警的受影响版本范围逐条比对 0 命中；npm audit --omit=dev 为 0（剩 braces 5 条，开发依赖、上游无修复）；
      npm ci / typecheck / lint / build、next start 冒烟、html2pptx 出单页 PPTX、SDK 拉起 CLI 1.0.43 握手都通过。
- [ ] 👤 手动全程重跑时确认 Lab-02 带令牌生成 PPT 正常（Copilot CLI 从 1.0.27 升到 1.0.43，这一步没测）

## 手册终审（2026-10-17 晚，只看文档、不实跑）

- [x] 对照仓库核对手册里的引用：main.js 行号、report.json 字段、focus.md 的行业、4 个 MCP 工具和 3 个测试、工作流配置、SKILL.md 段落与输出目录、
      Lab-02 页面文案、skillDirectories、4 核机器与端口、smoke-test 输出、openapi 的 host / title / 4 个操作、68 张图、页内锚点；set-key.sh 重跑不换密钥；.env 和 output/ 都被忽略
- [x] 修 · 课后推送陷阱：Lab-01 生成的 frontend/report.md、report.json 不提交，gh-aw 的 PR 改的也是这两个文件，合并 PR 后课后 `git push` 被拒、`git pull` 冲突
      → 课后清理第 2 步改成「restore 两个周报 → git pull → 提交推送」，排障加「已经 commit 了」的恢复命令；Lab-01 第 4 步、Lab-01 README、docs/codespaces.md 同步
- [x] 修 · Lab-03 测试补「把网页做成汇报 PPT」一句（与 Lab-03 README 一致，共 5 句；4 个工具都测到）
- [x] 修 · 排障：「只有分支 + Issue」与 fork 关 Issues 矛盾；Actions 启用行补 Enable workflow；401 写法统一；新增「预览页打不开」「git push 被拒」两行；
      Codespace 重建行改成删掉重导 + 新建连接（原「编辑工具重新上传」没实测过，且新连接器用不上旧连接）；空闲超时写明设置位置；「无法列出模型」注明重跑 set-key 不换密钥
- [x] 修 · 热身参考答案只恢复 index.html / main.js / styles.css（原来恢复整个 frontend 会连周报一起覆盖）；页眉 v1.1、页脚 v1.2 统一为 v1.3；
      focus.md 加行业的说法；时长注明含休息 30 分钟，INSTRUCTOR.md 和 docs/codespaces.md 的环节与时长对齐手册
- 未改：docs/teaching-design.html 里还有 fork 之前的说法（student/<名字> 分支、Issue + 分支、讲师演示 gh-aw），它是课程设计稿，留着不动
- [ ] 👤 手动全程重跑时顺带确认：课后清理第 2 步三行命令、Lab-03 第 4 句网页→PPT

## 用户手动重跑反馈（2026-10-18）

### 踩坑清单（症状 → 原因 → 处理，都已写进手册 / Lab README / INSTRUCTOR）

1. Lab-02 网页生成 PPT 报 `Tool failed: unexpected user permission response` → PR #8 把 Copilot CLI 升到 1.0.43 后，权限回复只认 `approve-once` 等新写法，
   lib/copilot.ts 和 SDK 0.2.2 自带的 approveAll 还返回 `{ kind: "approved" }` → 代码改成 `approve-once`（PR #10）；旧 fork 要 Sync fork、`git pull`、`npm ci`。
   复现方法：SDK 的 BYOK provider 指向本地假 OpenAI 服务，让假模型发起 bash 调用（不用令牌、不耗额度）。
2. Studio 打开时默认停在 Caldova (default)；Power Automate 停在另一个环境时「找不到连接」→ 先切到 Ontology-trial，Power Automate 右上角切到同一个环境。
3. 建连接的对话框只有 Display name、没有 API 密钥框；连接状态 `Parameter value missing`，Studio 里连接旁红色「!」，工具提示 `We couldn't enable this connection`
   → 导入向导 Authentication 那步 **Parameter label 空着** → Power Automate 编辑连接器 → 2. Security → 补 label → Update connector，再到连接 ⋯ → Edit 补填密钥。
   （一开始误判成「在 default 环境里建」导致，文档写错过一次，已更正：对比 v1 连接器 label 空 → 没有密钥框，v2 填了 → 有密钥框）
4. 工具报 `connectorRequestFailure` 404 + `The connection … is not found` → 连接被删了（Studio 连接下拉里的垃圾桶会直接删）→ 4 个工具逐个重选连接 → Save。
5. 工具报 `connectorRequestFailure` 404（不带上面那句）→ 连接器 host 少抄了 Codespace 名字后面的随机串（形如 `xxx-space-system-3000`，应为 `xxx-space-system-<随机串>-3000`）
   → Power Automate 编辑连接器 → 1. General → Host 改对 → Update connector，不用重新导入。
6. 同样的 404 → Codespace 空闲 30 分钟自动 Shutdown，公网地址一律 404（`gh codespace list` 可查）→ 打开 Codespace、重启 `npm run dev`、3000 设回 Public。
7. 工具报 `connectorPowerFxError … '<' is an invalid start of a value` → 3000 端口是 Private，GitHub 把请求 302 到 github.dev 登录页，Studio 拿网页去解析 JSON → 设 Public。
8. 工具报 401 `connectorAuthorizationError` → 端口 Private 或密钥不对；这次是密钥少复制了一位（31 位，应为 32 位）→ 用 `sed -n 's/^LAB_API_KEY=//p' Lab-02-Knowledge-Summary/.env` 打印纯密钥再复制。
   另：smoke-test 原来输出「密钥填：<key>」，双击会把中文一起选中 → 脚本已在值前后加空格（PR #10）。
9. 删连接器提示 Object dependencies exist（依赖是智能体的 Connection Reference）→ 先删智能体，引用会跟着消失。
10. 重新导入 REST API 工具会多出一个连接器（名字带 v2），两个连接器下的连接同名（都叫 tarry v2）分不清 → 看连接名下面的连接器名；多余的课后清理。
11. 工具的 Connection 下拉选了但保存的还是旧连接、凭据还是 End user credentials → 每个工具 Save 前看一眼 Connection 和 Credentials to use。
12. 智能体没按指令默认用 consulting，反问风格；回答 geek 后 `Content was filtered`（ContentFiltered）→ 指令加「不要反问」，测试句带上风格；ContentFiltered 的具体触发原因没查到（Activity 列表有延迟，没看到那一轮）。

### 状态

- [x] PR #10：Lab-02 权限回复修复、smoke-test 加空格；手册 v1.4 加复制按钮、「先看全局」、architecture.html（Mermaid 12.1.0 本地 vendored）、字体不阻塞渲染、改正「所有接口都要密钥」的说法
- [x] 本次文档更正：上面 2~12 写进手册排障表、第 5 步失败说明、Lab-03 README、INSTRUCTOR 现场排障；Power Automate 菜单路径写明（More → Connections；More → Discover all → Data → Custom connectors）；
      「Codespace 重建后」改成就地改 host 和密钥，不用重新导入；智能体指令加「不要反问」，第 4 句测试带上风格
- [x] 🤖 清理 Caldova (default) 的测试资源：连接、4 个 AIPluginOperation、AIPlugin 先删；连接器第一次删被拒（旧智能体的 Connection Reference）→ 用户删掉智能体后再删连接器和两个自动 Solution。复查全空
- [x] 用户在 Ontology-trial 重建后：给连接器补 label、连接补密钥（Connected）、改对 host、Codespace 重新起来并设 Public、密钥补全 → 第 5 句在 Activity 里核对过通过；第 4 句遇到反问 + ContentFiltered；1~3 句用户说已改好，未逐条核对
- [ ] 👤 Ontology-trial 里的测试资源（智能体、两个连接器、连接）课后按讲师手册清理
- 待定：首页生成接口 /api/generate/stream 不查密钥，端口公开时任何人都能花学员的额度；加检查要给网页加输入密钥的地方，先只在文档里提醒
- 未验证：Codespace 自带的令牌能否推送 `.github/workflows/` 下的文件（手册写了兜底：报 refusing to allow … workflow 就在本机做）
