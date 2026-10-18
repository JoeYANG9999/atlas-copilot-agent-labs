# 讲师手册 · 阿特拉斯中国 Copilot 智能体工作坊

## 课程结构（半天约 3.5 小时）

时长与[实操手册](docs/manual/index.html)一致：

| 环节 | 内容 | 时长 |
|---|---|---|
| 01 | 开场：讲开场 PPT（讲师自备，8 页带讲者备注：要想的事、两件工具、业务场景、技术架构、工作方法、路线图），不演示 app；第一分钟先让学员打开 Codespace，讲完一起信任文件夹、跑 `set-key.sh` | 20 分钟 |
| 02 | 热身 · Vibe coding：读懂项目、`/explain`、一句话给周报网页加开关、自定义指令 | 25 分钟 |
| 03 | Lab-01 行业洞察智能体 · MCP + gh-aw：Prompt 文件 + MCP 工具、改 focus.md、加「客户雷达」工具、推到学员自己的 fork 手动跑 gh-aw | 45 分钟 |
| — | 休息与答疑（放在 Lab-01 第 4 步触发 gh-aw 之后，回来正好看 PR） | 30 分钟 |
| 04 | Lab-02 知识总结智能体 · Skills + SDK：Chat 里用 Skill（实测约 20 分钟，建议讲师演示、学员边看边等）、改 SKILL.md、加「公司品牌风」、用 Copilot SDK 跑网页服务 | 45 分钟 |
| 05 | Lab-03 Copilot Studio 串起来（开始时发课堂账号卡片） | 45 分钟 |

## T-7 天 · 只有你能推动的事

1. **仓库设为 Public，学员各自 fork**（2026-10-17 决定）。每人在自己的 fork 上开 Codespace、跑 gh-aw，
   Codespaces / Actions / Copilot 额度都记在学员自己账号上，互不影响；学员也不需要本仓库的写权限。
   - fork 时提醒**取消勾选**「Copy the `main` branch only」，`answer/*` 参考答案分支才会带过去；
   - `answer/*` 每个分支只比 main 多一个提交（学员用 `git show origin/answer/…` 看答案）。改过 main 之后，在发通知前把三个分支 rebase 到最新 main 再 `git push --force-with-lease`；
   - 学员课前要做：fork → 生成 Fine-grained PAT（Account → Copilot Requests: Read，7 天过期）→
     存成个人 Codespaces secret 和 fork 的 Actions secret（都叫 `COPILOT_GITHUB_TOKEN`）→ fork 的 Actions 页签启用工作流，
     再单独 Enable 一次 Industry Insight Weekly（fork 上定时工作流默认 Disabled，不启用就没有 Run workflow）→
     fork 的 Settings → Actions → General 勾选「Allow GitHub Actions to create and approve pull requests」→ 建一次 Codespace。
     步骤见 [实操手册 · 课前准备](docs/manual/index.html#prep)；
   - 如果学员是 Enterprise Managed Users（EMU）账号，不能 fork 到个人名下，要改回「组织内建仓库」的方式，T-7 先确认。
2. **Codespaces 计费与策略**：学员 fork 在个人账号下，按**个人账号**计费和策略：
   - 个人账号每月免费 120 核时 + 15 GB 存储；4 核机器（`hostRequirements.cpus = 4`）课前建一次加上课半天约 15~20 核时，在免费额度内；
   - 个人账号默认允许端口设为 Public（Lab-03 必需）；
   - 课后提醒删除 Codespace（停止后仍按存储计费）。
3. **没有预构建**：预构建只对本仓库生效，fork 吃不到，每人第一次开 Codespace 要现装 Python / Node 依赖和 Chromium（3~8 分钟）。
   所以要求学员 **T-1 天**建好 Codespace，上课直接打开。
4. **Copilot 策略**（学员 Copilot 席位所在的组织或企业。学员用阿特拉斯的席位时，席位由企业 `atlascopco-Lab` 管理，
   只能由阿特拉斯的企业管理员改；每人可在 <https://github.com/settings/copilot/features> 自查以下各项是否为 Enabled）：
   - **Copilot Agent Mode in IDE Chat** 和 **MCP servers in Copilot**（Lab-01；2026-10-16 已在企业 AI Controls → MCP 设为 Enabled everywhere）；
   - **Copilot CLI**（Lab-02 的 Copilot SDK 依赖它；2026-10-16 已在企业 AI Controls → Copilot → Features & clients 设为 Enabled everywhere，SDK 实测生成 PPT 成功）。没开时 SDK 调 `models.list` 返回 403
     「not authorized to use this Copilot feature」，页面显示「无法列出模型」；
   - 确认允许学员创建 Fine-grained PAT 且不需审批（学员把 Resource owner 选为个人账号）。
5. **Copilot Studio 演示租户**：
   - **课堂账号**：每位学员一个，`user01`、`user02`……（显示名同账号）。账号、域名和初始密码只记在讲师自留的账号表里，
     **不要写进本仓库**（仓库是公开的）；打印的账号卡片 Lab-03 开始时发。
     - 要由租户管理员来建（用户管理员 + 许可证管理员角色）。讲师的演示账号不一定有权限，2026-10-18 实测没有。
     - 顺序：① Entra 管理中心 → 用户 → 所有用户 → 批量操作 → 批量创建（微软 2026-10 改过模板，用现下载的）；
       ② M365 管理中心给这批账号分配 Copilot Studio 许可（试用许可即可，本课只在测试窗格里用、不发布）；
       ③ Power Platform 管理中心 → 环境 → Ontology-trial → 设置 → 用户 + 权限 → 用户 → 添加用户，逐个勾 **Environment Maker**
       （非默认环境不会自动给，没有它建不了智能体；环境设了安全组的，先把账号加进安全组）。
     - 先只配一个账号，按下面「完整走一遍」走通再配其余的。只有 Environment Maker 能不能导入 REST API 工具，微软文档没写清，必须实测。
     - 首次登录多半要求改密码；租户开着安全默认值的话，还要用手机装 Microsoft Authenticator 注册（2024-07 起不能跳过）。课前确认，并提前通知学员带手机。
     - 测试窗格也消耗租户的 Copilot Credits，几十人一起测之前看一眼余量。
   - Power Platform 管理中心的 **DLP 策略允许自定义连接器**访问 `*.app.github.dev`；
   - 确认学员用哪个环境：2026-10-16 实测演示租户的 Default 环境新建智能体会一直转圈，**Trial 环境（Ontology-trial）正常**；
     Studio 打开时默认停在 Caldova (default)，课前通知和 Lab-03 开始时都要提醒学员先切到 Ontology-trial；课后清理两个环境都要查；
   - **完整走一遍**：自己用一个课堂账号把 Lab-03 从头做一遍（[Lab-03 README](Lab-03-Copilot-Studio/README.md) 已按 2026-10-18 重跑更新，含所有坑）；
   - 学员的 4 个工具都要改成 **Maker-provided credentials**（工具详情 → Additional details → Credentials to use），否则测试时会反复弹「先连接……打开连接管理器」。Agent status 因此会多一条「使用作者凭据」的提醒，本课不发布智能体，可以忽略；
   - 每个学员导入一次 REST API 工具，租户里就会多出：1 个 Solution（「<title> Solution」）、1 个自定义连接器、1 个 AIPlugin + 4 个 AIPluginOperation、1 个连接。课后清理见下文「课后」。
6. **网络**：场地网络要能访问 `github.com`、`*.github.dev`、`*.githubcopilot.com`、`news.google.com`、
   `copilotstudio.microsoft.com`、`*.powerplatform.com`。企业网络做 SSL 解密的，提前备热点。

## T-2 天 · 预检

- 用一个学员账号从零开一次 Codespace、用一个课堂账号登录 Studio，跑通三个 Lab，记下每步耗时。
- 手动触发一次 gh-aw 周报：`gh workflow run industry-insight.lock.yml`，合并 PR，确认 Pages 上的周报是本周的。
  这份周报是学员 Lab-02 / Lab-03 的兜底素材（学员自己没跑出来 Lab-01 时也能继续）。
- 用一个学员账号走一遍 fork 流程：fork（不只复制 main）→ 两处 Secret → 启用 Actions → 在 fork 上手动触发 gh-aw，确认 fork 里出现周报 PR。
- 学员回执（T-1）：fork 地址、Codespace 已建好、Actions 已启用（Studio 账号上课才发，不在回执里）。

## gh-aw 每周定时（本仓库定时 + 学员在各自 fork 上手动跑）

- 工作流源文件：`.github/workflows/industry-insight.md`；改完必须 `gh aw compile industry-insight` 再提交 `.lock.yml`。
- 本仓库需要 Secret `COPILOT_GITHUB_TOKEN`（讲师的 Fine-grained PAT，Copilot Requests 权限）；每个学员的 fork 用学员自己的同名 Secret。
- fork 上定时工作流默认 Disabled，学员课前在 Actions 里点 Enable workflow（启用后每周一也会在学员 fork 上定时跑）；课上在 Lab-01 第 4 步用 Run workflow 手动跑，结果是学员 fork 里的 PR。
- 仓库 Settings → Actions → General：勾选 **Allow GitHub Actions to create and approve pull requests**。
  atlascopco-Lab 企业在 Policies → Actions 里锁住了这一项（2026-10-16），没放开时 gh-aw 会把周报推到分支并建一个 Issue，
  由人点 Issue 里的「Create the pull request」链接建 PR，合并即可。学员的个人 fork 不受这条企业策略限制，自己勾选即可。
- 模型固定为 `claude-sonnet-5.5`（frontmatter `engine.model`）。gh-aw 默认的 `claude-sonnet-4.6` 不在企业开放的模型里；
  gh-aw 太旧时会报「model is retired or unsupported」，先 `gh extension upgrade gh-aw` 再编译（2026-10-16 用 v0.92.0 跑通）。
- 仓库 Settings → Pages → Source 选 **GitHub Actions**。仓库公开后 Pages 也是公开的，发布 Lab-01 周报（根路径）和学员实操手册（`/manual/`）。
  `deploy-pages.yml` 只在本仓库运行，学员 fork 推送 frontend 改动时会跳过。周报里有面向阿特拉斯的业务分析，公开前请确认可以对外。
- 网络白名单：`focus.md` 加了新的行业媒体 RSS 时，要把域名同步加到 `network.allowed` 再编译。

## 当天 · 每个环节下课前的硬指标

| 环节 | 全员达到才往下讲 |
|---|---|
| 01 开场 | `set-key.sh` 打印出 `LAB_API_KEY` |
| 02 热身 | 周报网页打开「只看高影响」后只剩「·高」的热点 |
| 03 Lab-01 | 周报网页页头显示「模式：智能体研判」；休息回来时 fork 里有周报 PR |
| 04 Lab-02 | Chat 生成的 PPT 每页标题都是结论句；网页上用「本周行业洞察周报」生成出 PPT 并能下载 |
| 05 Lab-03 | `smoke-test.sh` 全部通过，Studio 测试窗格能返回进度页链接 |

## 现场排障速查

| 现象 | 原因 | 处理 |
|---|---|---|
| Codespace 开了很久还在装依赖 | fork 没有预构建，第一次要现装 3~8 分钟 | 等它装完；以后打开同一个 Codespace 就快了。所以要求 T-1 建好 |
| 学员 fork 的 Actions 里看不到 Industry Insight Weekly | fork 上工作流默认停用 | fork → Actions 页签 → I understand my workflows, go ahead and enable them |
| 有 Industry Insight Weekly 但没有 Run workflow | 定时工作流在 fork 上要单独启用 | 点进去 → 黄条上的 Enable workflow |
| 学员 gh-aw 报 401 | 学员 fork 没设 Actions secret 或令牌过期 | fork → Settings → Secrets and variables → Actions → `COPILOT_GITHUB_TOKEN` |
| 学员 `git restore --source origin/answer/...` 报 invalid reference | fork 时只复制了 main | `git remote add upstream <本仓库地址> && git fetch upstream`，改用 `upstream/answer/...` |
| Studio 里一堆同名「Atlas Agent Labs」 | 学员没改 openapi.yaml 的 title | 让学员把 title 改成「Atlas Agent Labs · 账号」（如 `Atlas Agent Labs · user01`）重新导入，删掉自己旧的那个 |
| 导入 REST API 后在 Add tool 里找不到自己的工具，以为没建成、又导入一遍 | 新版 Add tool 默认停在 Connector 筛选，REST API 工具不显示 | 点搜索框下面的 **REST API** 筛选；多导入的那份课后按「课后」清理（2026-10-19 实测） |
| 首页找不到 Agent（Standard） | 新版首页三张大卡片都是 GitHub Copilot 搭建方式 | 首页最下面 **Other ways to build → Agent（Standard）** |
| 学员在 Studio 里建不了智能体（没有新建按钮，或提示没权限） | 账号在 Ontology-trial 里没有 Environment Maker（非默认环境不会自动给） | 租户管理员：Power Platform 管理中心 → 环境 → Ontology-trial → 设置 → 用户 + 权限 → 用户 → 选中学员 → 管理安全角色 → 勾 Environment Maker |
| 首次登录要求改密码，或要求注册 Microsoft Authenticator | 正常的首次登录流程（批量建的账号多半强制改密码；租户开着安全默认值时必须注册多重验证） | 让学员按提示完成、记住新密码；忘了密码由租户管理员在 M365 管理中心重置 |
| Studio 工具卡片 `connectorAuthorizationError`（HTTP 401） | ① 3000 端口变回了 Private（Codespace 重启后）；② 连接里的密钥不是学员当前 Codespace 的（每个 Codespace 的 LAB_API_KEY 都不同，课前建过、重建过的最容易错），或复制时少了一位（密钥应是 32 位）、带上了「填：」 | 先让学员跑 smoke-test：公网那项没过就设回 Public；都过再用 `sed -n 's/^LAB_API_KEY=//p' Lab-02-Knowledge-Summary/.env` 打印纯密钥 → Power Automate（右上角切到和 Studio 同一个环境）→ 左侧 More → Connections → 学员的连接 ⋯ → Edit → 粘贴密钥 → Update，不用删连接（2026-10-18 遇到过少复制一位） |
| Studio 工具卡片 `connectorRequestFailure`（HTTP 404）`The connection … is not found` | 工具绑定的连接被删了（学员点了连接下拉里的垃圾桶，或删掉重建过），工具详情 Connection 显示 Not connected | 4 个工具逐个打开 → Connection 下拉选学员的「Atlas · 账号」（没有就 Create new connection）→ Save → New test session（2026-10-18 讲师重跑时遇到） |
| Studio 工具卡片 `connectorRequestFailure`（HTTP 404），不带 `The connection … is not found` | 连接器的 host 不对：学员没改 openapi.yaml 的 host，或漏抄了 Codespace 名字后面的随机字符 | Power Automate（右上角切到和 Studio 同一个环境）→ 左侧 More → Discover all → Data → Custom connectors → 学员连接器的铅笔（编辑）→ 1. General → Host 改成 smoke-test 第一行打印的完整 host → Update connector，不用重新导入（2026-10-18 讲师重跑时遇到并实测） |
| 学员在 Power Automate 里找不到自己的连接 | Power Automate 和 Studio 不在同一个环境（演示租户有 Caldova (default) 和 Ontology-trial 两个） | Power Automate 右上角 Environments 切到 Studio 左下角显示的那个环境 |
| 建连接没有 API 密钥输入框（只有 Display name）、连接旁有红色「!」、工具提示 `We couldn't enable this connection` | 学员导入 REST API 时 Authentication 的 Parameter label 空着，建连接就不显示密钥框；Power Automate 里这个连接的状态是 `Parameter value missing` | Power Automate（右上角切到和 Studio 同一个环境）→ 左侧 More → Discover all → Data → Custom connectors → 学员连接器的铅笔（编辑）→ 2. Security → API Key 下点 Edit → 填 Parameter label → Update connector；已经建了的连接：左侧 More → Connections → ⋯ → Edit → 粘贴密钥 → Update，变成 Connected；还没建的回 Studio 重新建连接就有密钥框。不用重新导入（2026-10-18 讲师重跑时遇到并实测） |
| Lab-02 网页生成报 `Tool failed: unexpected user permission response` | 学员 fork 早于 2026-10-18 的修复（Copilot CLI 1.0.43 起权限回复要写 `approve-once`） | 学员 fork → Sync fork → Update branch，Codespace 里 `git pull`，再在 Lab-02 目录 `npm ci && npm run dev`（按锁文件装对 CLI 版本） |
| 测试时反复弹「先连接……打开连接管理器」 | 工具还是 End user credentials | 工具详情 → Additional details → Credentials to use 改成 Maker-provided credentials → Save |
| Chat 没有 Agent 模式 / 工具图标 | Copilot 策略没开 Agent 或 MCP | 管理员开策略；临时让学员看讲师屏幕 |
| 「无法列出模型」且令牌正确 | Copilot CLI 策略没开 | 管理员开策略；临时用讲师 Codespace 演示 |
| 端口可见性没有 Public | 组织 Codespaces 策略限制 | 组织 Settings → Codespaces → 端口可见性放开 Public |
| Studio 调用超时，或工具报 `connectorRequestFailure`（HTTP 404） | 学员 Codespace 空闲 30 分钟被自动停了，停了以后公网地址一律 404（`gh codespace list` 显示 Shutdown） | 回 Codespace 恢复 → 重启 `npm run dev` → 3000 设回 Public → smoke-test；让学员把空闲超时调到 120 分钟（2026-10-18 讲师重跑时遇到） |
| 工具报 `connectorPowerFxError … '<' is an invalid start of a value` | 3000 端口是 Private：GitHub 把请求 302 到 github.dev 登录页，Studio 拿到网页去解析 JSON | 端口设回 Public（Codespace 每次重启都会变回 Private），再跑 smoke-test（2026-10-18 遇到） |
| 回答 `Content was filtered`（ContentFiltered） | Studio 内容安全过滤拦下了这一轮（2026-10-18：智能体反问风格、学员回答 geek 后出现，原因没查到） | New test session，把要求一句话说全再问；指令里已加「不要反问」，测试句已带上风格 |
| Power Automate 里有好几个同名连接 | 学员重新导入过 REST API 工具，多出一个连接器（名字带 v2 之类），每个连接器有自己的连接 | 看连接名下面的连接器名认准；工具的 Connection 下拉只列所属连接器的连接；多出来的连接器和连接课后统一清理 |
| 生成 PPT 很慢 | 多个学员同时生成、或机器 2 核 | 每个 Codespace 一次只跑一个任务（其余排队）；改 4 核 |

## 课后

- 提醒学员按 [实操手册 · 课后清理](docs/manual/index.html#after) 做：端口改回 Private、推送改动、删除 Codespace、删除 PAT 和两处 Secret、删 Studio 里自己的智能体和工具。
- 讲师：清理 Studio 演示租户（2026-10-17 实测顺序，**只在 Power Automate 里删自定义连接器删不干净，刷新后会自己回来**）。
  **Ontology-trial 和 Caldova (default) 两个环境都要按下面走一遍**（Studio 默认停在 default，总有学员建错环境）：
  1. 学员没删的智能体：Copilot Studio → Agents → ⋯ → Delete（会提示数据永久删除）；
  2. Copilot Studio → 左侧 ⋯ → **Solutions** → 打开 **Default Solution** → **Objects**，按类型筛选后多选删除（Delete from this environment）：先 **AIPluginOperation**（工具操作），再 **AIPlugin**（工具），最后 **Custom connectors**；名字都带「Atlas Agent Labs」。
     删连接器提示 Object dependencies exist（View Dependencies 里是 `…bizreport….shared_…` 这样的 Connection Reference）= 还有智能体在用它，先回第 1 步删掉那个智能体，Connection Reference 会跟着消失（2026-10-18 实测）；
  3. [Power Automate](https://make.powerautomate.com) → Connections：删掉「Atlas · …」「Connect to Atlas Agent Labs …」等连接；
  4. Solutions 列表里删掉导入时自动生成的「Atlas Agent Labs … Solution」（只是空容器）；
  5. Connection references 里的 Content Conversion、Dataverse 是 SYSTEM 托管的，不要动。
- 讲师：课堂账号请租户管理员删除（M365 管理中心 → 活跃用户 → 勾选后删除），或者阻止登录、重置密码留到下次用；收回、销毁打印的账号表和卡片。
- 讲师：按需更新或删除本仓库的 `COPILOT_GITHUB_TOKEN`。
- 学员想继续用：fork 留着即可，课前启用的定时工作流每周一会自动跑，换一个长期令牌即可；不想要就在 fork 的 Actions → Industry Insight Weekly → ⋯ → Disable workflow。
