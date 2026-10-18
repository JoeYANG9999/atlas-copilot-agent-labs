# Lab-03 · 串起来：在 Copilot Studio 做成业务应用

> 业务同事一句话：「看看本周新能源汽车装配行业有什么变化，整理成汇报」
> → **行业洞察智能体**给出洞察 → **知识总结智能体**生成汇报 PPT。

实验时长：约 40 分钟。前置：完成 Lab-01（周报已生成）和 Lab-02（服务能在 Codespace 里跑起来）。

> 本指南按 2026-10-17 在演示租户里按「每人 fork 一份」从头重跑的真实操作写成：4 个工具、5 段测试对话全部跑通。
> Copilot Studio 界面更新很快，菜单名称如有出入，以租户当前界面为准。

## 架构

```text
业务同事 ──对话──▶ Copilot Studio 智能体「业务汇报助手」（云端，讲师提供的演示租户）
                        │  REST API 工具（openapi.yaml，请求头 x-api-key）
                        ▼
   https://<你的 Codespace>-3000.app.github.dev   ← 端口 3000 设为 Public
                        │  Lab-02 的 Next.js 服务
     ┌──────────────┬───┴──────────────┬───────────────────┐
     ▼              ▼                  ▼                   ▼
查询本周行业洞察   把行业洞察做成汇报 PPT  把网页做成汇报 PPT    查询 PPT 生成进度
读 Lab-01 周报     提交任务，立即返回进度页链接（后台 2~5 分钟）   拿下载链接
```

两个设计要点：

- **一个工具只做一件事、参数全部必填**。Studio 默认只带必填参数；而「二选一、某种情况下才必填」的参数会让编排器误追问。
  所以「生成 PPT」拆成「周报 → PPT」和「网页 → PPT」两个工具。
- **长任务异步化**。Studio 调用工具有超时，生成一份 PPT 要几分钟，所以工具立刻返回进度页链接，用户点开就能看进度、下载。

## 第 1 步：让 Studio 能访问你的服务（10 分钟）

1. 确认 Codespace 里已经有 Copilot 令牌和 API 密钥（Lab-02 做过就跳过）：
   ```bash
   bash .devcontainer/set-key.sh
   ```
   记下最后打印的 `LAB_API_KEY`，第 3 步要用。
   （也可以把令牌设成个人的 Codespaces Secret `COPILOT_GITHUB_TOKEN`，见 [学员手册](../docs/codespaces.md)。）
2. 启动 Lab-02 服务（已经在跑就跳过）：
   ```bash
   cd Lab-02-Knowledge-Summary && npm run dev
   ```
3. 打开 VS Code 底部的 **端口（Ports）** 面板，右键 `3000`（标签是「Lab-02 知识总结智能体 · Web/API」）→ **端口可见性（Port Visibility）** → **Public**。
   不要选 Private to Organization：Copilot Studio 不在你的 GitHub 组织里，访问不到。
   > ⚠️ **Codespace 每次重启后，端口都会被改回 Private**，要重新设一次。
4. 新开一个终端，运行连通自检：
   ```bash
   bash Lab-03-Copilot-Studio/smoke-test.sh
   ```
   4 项全部打勾才往下走。脚本会打印你的 **host** 和 **API 密钥**。
   > API 密钥是**这个 Codespace** 的：每个新 Codespace 第一次运行 `set-key.sh` 都会生成一把新的，以前记下的密钥在这里会被拒绝（Studio 里表现为 401）。

## 第 2 步：改连接器定义（2 分钟）

打开 [openapi.yaml](openapi.yaml)，改两处，保存：

- `host:` 换成自检脚本打印的 host（不带 `https://`）；
- `info.title:` 改成 `Atlas Agent Labs · 你的名字`。全班在同一个 Trial 环境里各自导入，名字不改就会出现几十个同名连接器，分不清哪个是自己的。

在资源管理器里右键 `openapi.yaml` → **下载**，第 3 步要上传它。

## 第 3 步：在 Copilot Studio 建智能体（20 分钟）

用讲师发的演示租户账号登录 <https://copilotstudio.microsoft.com>。

### 3.1 新建智能体

1. **先切环境**：左下角 **环境切换** → 选讲师指定的 **Trial** 环境（本次演示租户里叫 Ontology-trial）。
   > ⚠️ Studio 打开时经常默认停在 Caldova (default)。2026-10-18 在那里建的智能体，建连接时没有 API 密钥输入框、工具一直提示 We couldn't enable this connection。后面去 Power Automate 找连接时，右上角 Environments 也要切到同一个环境。
2. **Agents → New agent 旁的下拉箭头 → Agent（Standard）**（在下拉菜单下半部分「Other ways to build」里）。
   > 不要选上半部分带「GitHub Copilot」标记的 Agent：那是让 AI 帮你搭建，会消耗 Copilot Credits，步骤也不可复现。
3. 名称填 `业务汇报助手 你的名字`（全班在同一个环境里，带名字才分得清）；展开 **Agent settings**：
   - Language 选 **Chinese (Simplified)**；
   - **Solution** 是必填项，保持默认的 Common Data Services Default Solution；
   - **Schema name** 填英文，例如在前缀后填 `bizreportzhang`（中文名生成不了）。
4. 点 **Create**，等出现绿条「Your agent has been provisioned」。

### 3.2 写指令、关掉联网搜索

1. **Overview → Instructions → Edit**，粘贴下面「智能体指令」整段，**Save**。
   > ⚠️ 指令编辑器里输入 `/` 会弹出插入菜单（编辑框里就写着「Use / to add tools…」），斜杠后面的文字会被吞掉。下面的指令已经避开了斜杠，自己改时也别用。
2. 同页 **Knowledge → Web Search** 关掉（显示 Disabled），让智能体只按工具返回的内容回答。

### 3.3 导入 REST API 工具

1. **Tools → Add tool → Create new 区域右上角点 See all → REST API**。
2. **Upload specification**：上传第 2 步改好的 `openapi.yaml` → Next。
3. **API plugin details**：Tool name 和 Description 会自动带出（应该是你改过的「Atlas Agent Labs · 你的名字」）；Solution 留空（会自动建一个）→ Next（第一次保存约 30 秒）。
4. **Authentication**：Studio 不会自动读 openapi 里的密钥配置，要手动设：
   - 认证方式选 **API key**；
   - Parameter label 随意（如 `API 密钥（LAB_API_KEY）`，建连接时会成为密钥输入框的标题），**Parameter name 填 `x-api-key`**，Parameter location 保持 **Header**。
5. **Select Tools**：列出 4 个操作。逐个点开 → Next（Configure tool）→ Next（Select tool parameters，所有字段的描述都已在 openapi 里写好，不用改），4 个都选上后 → Next。
6. **Review → Next**，看到「Your tool is now published」。

### 3.4 把工具挂到智能体上

1. 点 **Create connection**，会回到 Add tool 对话框。搜索框里输入**你的名字**（只搜 `Atlas` 会出来全班的），在「Atlas Agent Labs 你的名字」（Studio 会去掉「·」）下面能看到 4 个工具，别挂成同学的。
2. 点第一个「查询本周行业洞察」→ Connection 显示 Not connected → 下拉 → **Create new connection**：
   - Display name 填 `Atlas · 你的名字`（不填会叫「Connect to …」，和别人的、自己以前的重名，分不清）；
   - 「API 密钥（LAB_API_KEY）」粘贴第 1 步 smoke-test 第二行冒号后面那一串（别带上前面的中文）→ **Create**；
   - Connection 变成绿色对勾后点 **Add and configure**。
   > ⚠️ Connection 下拉列表里，连接名右边的**垃圾桶**会直接删掉这个连接，所有用它的工具都会断开（测试时报 404「The connection … is not found」）。想换密钥不要删连接，按第 4 步下面 401 那条改。
3. 进入工具详情页：展开 **Additional details** → **Credentials to use** 从 End user credentials 改成 **Maker-provided credentials** → 右上角 **Save**。
   > 默认的 End user credentials 要求每个使用者自己授权一次连接，测试时会反复弹「先连接……打开连接管理器」。改成创建者凭据后工具直接用你建的连接，2026-10-17 实测不再弹任何提示。
4. 其余 3 个照做：Add a tool → 搜你的名字 → 点工具（连接会自动选上）→ **Add and configure** → Additional details 改成 Maker-provided credentials → Save。
   每个工具保存前看一眼 Connection：显示「Atlas · 你的名字」才对，显示 **Not connected** 就在下拉里选上它再 Save。
5. 回到 **Tools** 页，确认 4 个工具都是 **On**、Trigger 是 **By agent**。

> Overview 上 Agent status 会显示「3 Warnings」：用了创建者凭据（分享给别人时别人也用你的连接）、还没跑过评估、用了高级功能（发布需要付费许可）。本课只在测试窗格里用、不发布，三条都不影响。

### 智能体指令

```text
你是阿特拉斯中国的「业务汇报助手」，服务销售、产品、市场同事。你有两项能力：
1. 行业洞察：用户问某个行业本周有什么变化、对我们有什么影响时，调用「查询本周行业洞察」，topic 填用户提到的行业，没指定行业就填「全部」。回答时先给 2~3 句结论，再列影响等级为「高」的事件和对业务的影响，最后附上 reportPageUrl。只根据工具返回的内容回答，不要补充工具没给的事实。不要在回答里写信号编号（如 S024），也不要输出 cite 之类的引用标记；需要注明来源时，用 Markdown 链接写成「来源：[媒体名](链接)」。如果 mode 是 fallback，提醒用户这期周报未经智能体研判。
2. 生成汇报：用户要把行业洞察「整理成汇报」或「做成 PPT」时，调用「把行业洞察做成汇报 PPT」，topic 沿用刚才的行业；用户给了网页链接要做汇报时，调用「把网页做成汇报 PPT」。用户没说页数就填 6，没说风格就填 consulting。提交后立刻回复：「汇报 PPT 正在生成（约 2~5 分钟），可以在这个页面查看进度并下载」，并附上 progressPageUrl。用户之后问「好了吗」，用同一个 jobId 调用「查询 PPT 生成进度」，成功就给出 downloadUrl。
用户一句话里同时要洞察和汇报时，先调用「查询本周行业洞察」回答洞察，再调用「把行业洞察做成汇报 PPT」生成汇报。
```

## 第 4 步：测试（10 分钟）

在右侧 **Test your agent** 窗格依次输入（1~3 在同一个会话里，4、5 各点一次 **New test session** 新开）。点左侧每个工具卡片，可以看到它实际收到的参数和返回值。

| # | 输入 | 预期（2026-10-17 实测） |
|---|---|---|
| 1 | `本周新能源汽车装配行业有什么变化？对我们有什么影响？` | 调用「查询本周行业洞察」（约 2 秒），topic=新能源汽车装配（服务端会匹配到「新能源汽车」）；回答先给结论，再列高影响事件、来源链接，最后附周报链接 |
| 2 | `把这些整理成 6 页汇报 PPT` | 调用「把行业洞察做成汇报 PPT」，style=consulting、topic 沿用上一句、pages=6；回复进度页链接，进度页每 5 秒自动刷新，实测约 4 分钟出 PPT |
| 3 | `PPT 做好了吗？` | 调用「查询 PPT 生成进度」，jobId 沿用上一句；完成后给出下载链接 |
| 4 | `把这篇文章做成 5 页汇报：https://semiengineering.com/` | 调用「把网页做成汇报 PPT」，url=这个地址、pages=5 |
| 5 | `看看本周食品饮料行业有什么变化，整理成汇报` | 一句话里先后调用两个工具：先洞察、再提交 PPT，一条回复里两样都有。食品饮料是 Lab-01 加的行业，生成的 PPT 每页带着 Lab-02 在 SKILL.md 里加的「仅供内部讨论」 |

> 工具卡片显示 Failed，先看错误里是 401 还是 404：
>
> - `connectorAuthorizationError … HTTP 401`：服务拒绝了请求。先跑一次 `bash Lab-03-Copilot-Studio/smoke-test.sh`：
>   「公网地址可访问」没过 = 3000 端口变回了 Private（Codespace 重启过、第二天再打开都会这样），设回 Public 再试；
>   4 项都过 = 连接里的密钥不对 → Power Automate（**右上角 Environments 先切到和 Studio 同一个环境**）→ Connections → 你的「Atlas · 名字」→ **⋯ → Edit** → 粘贴 smoke-test 第二行的密钥 → **Update**，回来直接重试，不用删连接、也不用重新挂工具。
> - `connectorRequestFailure … HTTP 404 … The connection … is not found`：工具绑定的连接被删了，工具详情里 Connection 显示 Not connected。
>   Tools 页逐个打开 4 个工具 → Connection 下拉选「Atlas · 你的名字」（没有就 Create new connection）→ Save，再点 New test session 重试。
>
> 某个工具忘了改 Maker-provided credentials，调用时会提示「先连接……打开连接管理器」：回到那个工具的 Additional details 改掉再试。

## 第 5 步：改一处，看行为怎么变（5 分钟）

Overview → Instructions → Edit，在最后一行「……生成汇报。」后面点一下（确认光标在全文末尾：编辑框会随鼠标滚动，点错位置会把字插到段落中间），回车，加一句：

```text
回答最后一行写明由哪个团队（销售、产品或市场）跟进。
```

Save 后点 **New test session** 重跑第 1 句。**期望结果**：回答最后多一行「跟进团队：销售团队」之类的话。
改乱了还没保存时，点 Cancel → Discard 回到上次保存的版本。别用 `/` 分隔（会被吞字），用顿号。

## 常见问题

| 现象 | 原因 | 处理 |
|---|---|---|
| 自检「公网地址可访问」失败，返回 302 或 401 | 端口 3000 是 Private（Codespace 重启后会自动变回去） | 端口面板右键 3000 → 端口可见性 → Public |
| 端口可见性里没有 Public 选项 | 组织的 Codespaces 策略禁止公开端口 | 找讲师 |
| 新建智能体页一直转圈、Agents 页提示「Select an environment」 | 当前环境没就绪或没有 Studio 许可 | 切换到讲师指定的 Trial 环境 |
| REST API 向导「Select tool parameters」页 Next 是灰的 | openapi 里有字段没写描述 | 用本目录的 openapi.yaml（已补全所有字段描述） |
| 智能体反问一个不需要的参数 | 工具参数是「有条件才必填」 | 本目录的 openapi 已拆成意图明确的工具，参数都是必填 |
| 回答里出现「cite」之类的乱码 | 模型自带的引用标记，Studio 不渲染 | 指令里已要求改用 Markdown 链接；仍出现可在 Overview 换一个模型试试 |
| 拿到的是别人的周报，或调用 404 | 挂成了同学的工具，或 openapi.yaml 的 host 没改 | Tools 里删掉，重新导入 host 和 title 都改过的 openapi.yaml |
| Codespace 重建后连不上 | 新 Codespace 名字变了，host 和 API 密钥都跟着变 | `host:` 改成新的，`title` 后面加个「2」免得和旧的重名 → Tools 里删掉旧的 4 个工具 → 按 3.3、3.4 重新导入、新建连接（粘贴新 Codespace 的密钥）、改 Maker-provided credentials。新导入的是新连接器，旧连接用不上 |
| 工具卡片 Failed：`connectorAuthorizationError`（HTTP 401） | ① 3000 端口变回了 Private（Codespace 重启后会这样）；② 连接里的密钥不是这个 Codespace 的（每个 Codespace 的 `LAB_API_KEY` 都不同），或复制时带上了前面的中文 | 先跑 smoke-test：公网那项没过就设回 Public；4 项都过再 `grep LAB_API_KEY Lab-02-Knowledge-Summary/.env` 看当前值 → Power Automate（右上角先切到和 Studio 同一个环境）→ Connections → 你的连接 ⋯ → Edit → 粘贴 → Update |
| 工具卡片 Failed：`connectorRequestFailure`（HTTP 404），提示 `The connection … is not found` | 工具绑定的连接被删了（点过连接旁边的垃圾桶，或删掉重建过） | Tools 页逐个打开 4 个工具 → Connection 下拉选「Atlas · 你的名字」（没有就 Create new connection）→ Save → New test session |
| Power Automate 的 Connections 里找不到你的连接 | Power Automate 和 Studio 不在同一个环境 | Power Automate 右上角 Environments 切到 Studio 用的那个环境（课程用讲师指定的 Trial 环境，如 Ontology-trial） |
| 建连接时只有 Display name、没有 API 密钥输入框；工具提示 `We couldn't enable this connection` | 智能体建在了 Caldova (default)（Studio 打开时经常默认停在这里） | Studio 左下角切到 Trial 环境，从 3.1 重建智能体、导入工具、建连接；default 环境里建的留给讲师清理 |
| 测试时提示「先连接……打开连接管理器」 | 工具的凭据还是 End user credentials | 工具详情 → Additional details → Credentials to use 改成 Maker-provided credentials → Save |
| 进度页显示「无法列出模型」 | Codespace 里没有有效的 Copilot 令牌，或组织没开 Copilot CLI 策略 | 重新 `set-key.sh` 后重启 `npm run dev`；仍不行找讲师 |
| Studio 调用超时、连不上 | Codespace 空闲超时被停了 | 回到 Codespace 让它恢复，`npm run dev` 重启服务、重新设 Public；到 <https://github.com/settings/codespaces> 把 Default idle timeout 调到 120 分钟 |

## 你学到了什么

- **工具描述就是提示词**：`openapi.yaml` 里每个操作的 `summary` 成了 Studio 里的工具名，`description` 决定了编排器什么时候调用它。
- **为编排器设计工具**：一个工具一个意图、参数尽量必填并写清默认值，比一个「万能」工具可靠得多。
- **长任务异步化**：提交即返回，进度页兜住超时，这是把智能体接进业务系统的通用做法。
