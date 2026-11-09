# AGENTS.md — 本仓库的工作约定

> 适用对象：在本仓库干活的 AI 智能体与维护者。对应上游 `NX_MCP` 的 `CLAUDE.md`，
> 但**只描述本机 NX2007 + .NET Remoting 实现**，不要把上游 NX2506 / C# GUI 桥的结论搬过来用。

## 权威来源（冲突时按此顺序）

1. **真机事实**：`CAPABILITIES.md` —— 哪些能用、哪些实测不能用，以它为准。
2. **建模配方**：`skills/nx-mcp-bridge-modeling/SKILL.md` —— 763+ 行真机验证过的 NXOpen 写法。
3. **链路与恢复契约**：`docs/architecture.md`。
4. **验收口径**：`docs/validation.md`、`docs/inspection-contract.md`。
5. 其余 README / 注释只是索引，**不是能力证据**。

## 每次接 NX 建模任务的第一步（不可跳过）

```
python nx_ready.py --status
```

- `READY` → 直接建模。
- `NOT_READY` → 去掉 `--status` 重跑（会自动拉起 NX 并等桥上线）。
- `NX_RUNNING_NO_BRIDGE` → 切离线 journal 兜底，**绝不再开第二个 NX**。

改连接器配置后需在 WorkBuddy 里对 `siemens-nx` 点一次「信任」，必要时重启 WorkBuddy。

## 改动纪律（上游方法论的落地版）

1. **不发明工具**：先 `mcp__siemens-nx__ping` 看真实工具面，不假设实验性工具存在。
2. **文档有 ≠ 实机能用**：任何 API 只有真机跑通才写 ✅；`NXOpen.xml` 里存在但没跑过的一律标 🟡 待验证。
   历史教训：`CreateMoveObjectBuilder`、`MoveBodyBuilder.BodyToMove`、`UF TransformEntities` 文档都有，实机全不可用。
3. **改前查询**：先确认工作零件、体数、特征与单位；用工具返回的对象引用，不猜显示名。
4. **一次一个操作**：NXOpen 在主线程串行执行，不要并发发建模指令。
5. **改后验证做实**：每步布尔 / 倒角 / 开孔后回查 `list(work.Bodies)`、特征计数、包围盒；
   工具返回成功 **不等于** 模型正确。没真跑到的验证要如实写「未能验证」。
6. **失败恢复**：丢弃所有缓存引用（**body tag 会重编号**），重新查询；执行状态未知的超时/断连
   **不自动重放**；出错不循环重试。
7. **不精简重写技能**：技能只能在原版上「增补 + 修正」，改完跑逐行 diff，确认有效配方零丢失。
8. **三方一致**：本机生效技能 / 本地仓库副本 / GitHub 线上仓库必须逐字节一致。

## 交付约定

- 用户只发一句话，其余全自动；不给选择题、不让用户敲命令、不报路径与 API 术语。
- 模型统一存 `D:\三维建模结果\<名字>.prt`；汇报用 ✅ 清单 + 一句话结论。
- **默认不截图**（2026-11-09 用户明确取消每步截图）；只在用户要求或需自证造型时截。
- 过程可见 = 用户直接看 NX 窗口实时生长，不靠截图流。

## 同步流程

```
python scripts/validate_repo.py          # 本地静态自检，必须全绿
python sync_github.py <TOKEN> --check   # 列出待同步文件
python sync_github.py <TOKEN>           # 推送到 Mrxiaoxiaobai/NX-Agent-Hub main
```

脚本推送前会强制跑 L0 自检，内容未变的文件按 blob sha 跳过。
**已知例外**：PAT 没有 Workflows 权限，`.github/workflows/validate.yml` 无法自动写入；
等价内容已同步到 `ci/validate.yml`，脚本每次会再试一次，补权限后重跑即自动启用 CI，无需手改文件。

本机 Git 走代理会报 CONNECT tunnel 502，因此**一律走 GitHub Contents API，不用 git push**。
PAT 只在命令行传入，不落盘、不写进仓库文件。

## 环境坑

- Git Bash 缺 `rm/cat/grep/head/dirname` → 用 Python 做文件操作。
- PowerShell 工具 stdout 在本机读不到 → 要输出就用 Python 执行。
- 中文路径写 bat 需 GBK + `chcp 936`；Python 侧 subprocess 传中文路径正常。
- 启动 NX 必须显式注入 `UGII_USER_DIR`（NX 进程读的是自己的环境变量），别指望从 MCP 侧继承。
