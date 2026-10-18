# 学员手册 · 用 Codespaces 跑完这门课

全程在浏览器里完成，本机不用装任何软件。带截图的完整版见 [实操手册](manual/index.html)。每一步都写了**期望结果**，对不上就看本页最后的「遇到问题」或举手找讲师。

## 0. 课前（建议上课前一天做完）

每人用**自己的 fork、自己的 Codespace、自己的 Copilot 令牌**，费用和额度都记在自己账号上。

- [ ] 有 GitHub 账号和 **Copilot Business / Enterprise** 席位
- [ ] Fork 课程仓库：右上角 **Fork** → Owner 选自己 → **取消勾选**「Copy the `main` branch only」（卡住时要用 `answer/*` 参考答案分支）
- [ ] 按下面「准备 Copilot 令牌」生成好 Fine-grained PAT，并存成两处 Secret（见第 6、7 步）
- [ ] 你的 fork → **Actions** 页签 → 点「I understand my workflows, go ahead and enable them」；
      再点左侧 **Industry Insight Weekly**（标着 Disabled）→ 黄条上的 **Enable workflow**，看到 **Run workflow** 按钮才算好；
      Settings → Actions → General → Workflow permissions 勾选 **Allow GitHub Actions to create and approve pull requests** → Save
- [ ] 按第 1 节在你的 fork 上建好 Codespace（第一次要现装依赖，3~8 分钟）
- Copilot Studio 账号不用提前准备：Lab-03 开始时讲师发账号卡片（`user01` 这类课堂账号）

### 准备 Copilot 令牌（Fine-grained PAT）

1. 打开 <https://github.com/settings/personal-access-tokens> → **Generate new token**。
2. Token name 写 `copilot-agent-labs`，Expiration 选 7 天。
3. **Resource owner 选你自己的账号**（不要选组织，组织往往需要管理员审批）。
4. Permissions → **Account permissions** → **Copilot Requests** 选 **Read**。其他都不用勾。
5. 生成后复制 `github_pat_...` 开头的令牌（只显示一次）。
6. 存成个人 Codespaces secret：<https://github.com/settings/codespaces> → **New secret**，Name `COPILOT_GITHUB_TOKEN`，
   Value 粘贴令牌，Repository access 选**你 fork 的仓库**。Codespace 启动时自动注入，令牌不落盘。
7. 存成 fork 的 Actions secret（Lab-01 云端版用）：你的 fork → Settings → Secrets and variables → **Actions** →
   New repository secret，Name 同样是 `COPILOT_GITHUB_TOKEN`，Value 同一个令牌。

## 1. 创建 Codespace（5 分钟）

1. 打开**你自己的 fork**（`<你的用户名>/atlas-copilot-agent-labs`），点 **Code → Codespaces → Create codespace on main**。
   fork 没有预构建，第一次要现装 Python / Node 依赖和浏览器，约 3~8 分钟。
2. 等待浏览器里出现 VS Code，弹出「Do you trust the authors…」时点 **Trust Folder & Continue**。

**期望结果**：左下角显示 `Codespaces: …`，终端提示符停在 `/workspaces/atlas-copilot-agent-labs (main)`。
安装过程和「环境就绪」的提示写在创建日志里（命令面板 `Codespaces: View Creation Log`），终端里看不到是正常的。

3. 在终端运行：
   ```bash
   bash .devcontainer/set-key.sh
   ```
   已经设了 Codespaces secret 就在提示粘贴令牌时**直接回车**；否则粘贴令牌后回车（输入不会显示）。
   **期望结果**：打印一串 `LAB_API_KEY`（Lab-03 要用，先不用记）。

   > Codespace 建好之后才加的 Codespaces secret，要**重启 Codespace** 才生效。

4. 把空闲超时调长，免得 Lab-03 时 Codespace 自己停掉：打开 <https://github.com/settings/codespaces> →
   **Default idle timeout** 改成 **120** 分钟。

## 2. Lab-01 · 行业洞察智能体（45 分钟）

按 [Lab-01 README](../Lab-01-Industry-Insight/README.md) 操作。核心几件事：

1. Copilot Chat → **Agent** 模式 → 输入 `/industry-insight`。
   **期望结果**：智能体依次调用 `read_focus`、`fetch_industry_signals`、`get_signals`、`build_weekly_report`，最后汇报「几个行业、几个热点」。
2. 预览周报：
   ```bash
   python -m http.server 8080 --directory Lab-01-Industry-Insight/frontend
   ```
   **期望结果**：网页标题「行业洞察周报 · 20xx-Wxx」，页头写「模式：智能体研判」。
3. 改 `Lab-01-Industry-Insight/focus.md`，加一个你关注的行业，再跑一次。
4. 让 Copilot 加一个 MCP 工具「客户雷达」`search_signals`，重启 MCP 服务器后用它查客户动态。
5. `git push` 到你的 fork，在 fork 的 **Actions → Industry Insight Weekly → Run workflow** 手动跑云端版，结果是你 fork 里的一个 PR（合并后 fork 比 Codespace 里的新，推送前要先同步，见「6. 课后清理」第 2 步）。

## 3. Lab-02 · 知识总结智能体（45 分钟）

按 [Lab-02 README](../Lab-02-Knowledge-Summary/README.md) 操作。核心几件事：

1. 在 Chat 里让 Copilot 把一篇文章总结成 6 页汇报 PPT，下载用 PowerPoint 打开。
2. 改 `.github/skills/knowledge2ppt/SKILL.md` 的「团队汇报规范」，再生成一次对比。
3. 让 Copilot 给网页加一种 PPT 风格「公司品牌风」。
4. 启动网页服务：
   ```bash
   cd Lab-02-Knowledge-Summary && npm run dev
   ```
   **期望结果**：浏览器打开端口 3000，页面标题「知识总结智能体 · 一键出汇报 PPT」；选「本周行业洞察周报」能生成 PPT。

> 下载 Codespace 里的文件：资源管理器里右键文件 → **下载**。

## 4. Lab-03 · Copilot Studio 串起来（45 分钟）

按 [Lab-03 README](../Lab-03-Copilot-Studio/README.md) 操作。关键是把端口 3000 设为 **Public**、跑自检，再把 `openapi.yaml` 的 `host` 和 `title`（`Atlas Agent Labs · 你的账号`，如 `Atlas Agent Labs · user01`）改成你自己的，导入 Studio：

```bash
bash Lab-03-Copilot-Studio/smoke-test.sh
```

**期望结果**：最后一行「全部通过（4 项），可以去 Copilot Studio 建连接器了」。

在 Studio 里建连接时粘贴的，必须是**这个 Codespace** 的 API 密钥（smoke-test 第二行打印的那个）。每个新 Codespace 都会生成新的密钥，用以前记下的会报 401。
4 个工具都要在 Additional details 里把 Credentials to use 改成 **Maker-provided credentials**，否则测试时会反复弹「先连接……」。

## 5. 卡住了怎么办

超过 5 分钟没进展，就从参考答案分支拿需要的文件，先跟上（只覆盖这几个文件，你别处的改动不受影响）：

| 卡在哪 | 命令 |
|---|---|
| 热身「只看高影响」开关 | `git restore --source origin/answer/warmup -- Lab-01-Industry-Insight/frontend/index.html Lab-01-Industry-Insight/frontend/main.js Lab-01-Industry-Insight/frontend/styles.css` |
| Lab-01 客户雷达 | `git restore --source origin/answer/lab01 -- Lab-01-Industry-Insight/mcp_server Lab-01-Industry-Insight/tests`（之后重启 MCP 服务器） |
| Lab-02 公司品牌风 | `git restore --source origin/answer/lab02 -- Lab-02-Knowledge-Summary/lib/styles.ts Lab-02-Knowledge-Summary/app/globals.css` |

报 `invalid reference` 说明 fork 时只复制了 main，先运行
`git remote add upstream https://github.com/atlascopco-Lab/atlas-copilot-agent-labs.git && git fetch upstream`，再把命令里的 `origin/` 换成 `upstream/`。

## 6. 课后清理

1. 端口面板把 3000 改回 **Private**。
2. 保存改动，依次运行：
   ```bash
   git restore Lab-01-Industry-Insight/frontend/report.md Lab-01-Industry-Insight/frontend/report.json
   git pull
   git add -A && git commit -m "课堂练习" && git push
   ```
   第 1 行丢掉本地生成的周报（周报经 gh-aw 的 PR 审核后才进主干）；第 2 行把你在 GitHub 上合并的 PR 同步下来，不然推送会被拒绝。
   改动就留在你的 fork 里（生成的 PPT 不会提交，要的话右键下载）。
3. 删除 Codespace：<https://github.com/codespaces> → 你的 Codespace → **Delete**（停止后仍按存储计费）。
4. 删除令牌和 Secret：<https://github.com/settings/personal-access-tokens> 删 PAT；
   <https://github.com/settings/codespaces> 删 `COPILOT_GITHUB_TOKEN`；fork 的 Settings → Secrets and variables → Actions 删同名 Secret。
5. Copilot Studio：Agents 里删掉你建的「业务汇报助手 你的账号」；Power Automate → Connections 里删掉你的「Atlas · 你的账号」连接。导入时自动生成的连接器和工具定义由讲师课后统一清理。
6. fork 可以留着课后继续改；课前启用的 Industry Insight Weekly 每周一会自动跑，删了令牌或不想要就在 fork 的
   Actions → Industry Insight Weekly → **⋯** → **Disable workflow**。fork 不要了就 Settings → 最下面 **Delete this repository**。

## 遇到问题

| 现象 | 处理 |
|---|---|
| Codespace 一直在装依赖，很久不好 | fork 没有预构建，第一次要 3~8 分钟，等它装完；以后打开同一个 Codespace 就快了 |
| fork 的 Actions 里没有 Industry Insight Weekly | fork 上工作流默认停用：Actions 页签点「I understand my workflows, go ahead and enable them」 |
| 有 Industry Insight Weekly 但没有 Run workflow 按钮 | 定时工作流在 fork 上要单独启用：点进去 → **Enable workflow** |
| gh-aw 报 401 | fork 的 Actions secret `COPILOT_GITHUB_TOKEN` 没设或令牌过期 |
| Codespace 打不开 / 白屏 | 公司网络访问不了 `*.github.dev`，换讲师提供的热点 |
| Chat 里没有 Agent 模式或工具图标 | 组织的 Copilot 策略没开 Agent / MCP，找讲师 |
| 「无法列出模型」 | 重新 `bash .devcontainer/set-key.sh`；令牌正确仍报错就是组织没开 Copilot CLI 策略，找讲师 |
| 各 Lab 的专项问题 | 见各 Lab README 最后的「遇到问题」 |
