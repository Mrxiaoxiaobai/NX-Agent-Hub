# 与上游 `NX_MCP` 的定位对照

> 本仓库账号下有两个和 NX 相关的仓库，容易混。本文明确「谁是教材、谁是干活工具」，
> 以及 3.2.0 到底向上游借鉴了什么、刻意没借鉴什么。

## 两个仓库

| 项 | `Mrxiaoxiaobai/NX_MCP` | `Mrxiaoxiaobai/NX-Agent-Hub`（本仓库） |
| --- | --- | --- |
| 来源 | fork of `DreamEnding/NX_MCP`，官方参考标准 | fork of `Cai-aa/CAD-Agent-Hub`，2026-11-09 改名 |
| 分支 / HEAD | `master`，`4a7c8811`，与上游同步 | `main`，v3.2.0（技能版本） |
| 定位 | **方法论教材 / 契约规范** | **本机日常建模主路径** |
| NX 版本 | NX2506 Python batch、NX2206 C# GUI | **NX2007** |
| 架构 | Python sidecar → 带 token 的回环 JSON-RPC → C# GUI / batch 桥 | `server.py` → `.NET Remoting :48161` → NX 进程内 NXOpen |
| 工具面 | 16 个定型 `nx_*`（默认暴露）；34 个 legacy 隐藏；`nx_measure_*` 仍为提案 | 82 个专用工具 + `run_python` 兜底 |
| 特征编辑 | blend / chamfer / hole 在 legacy 中，默认隐藏且未验证 | `chamfer_edges` / `fillet_edges` / `create_cylindrical_hole` **真机可用** |
| 文档 | 官方技能 75 行 + `docs/` + `tests/` + CI + 发布门禁 + CHANGELOG | 763+ 行真机配方 + `CAPABILITIES.md` + 3.2.0 补齐的工程规范 |
| 验证方式 | 20 轮 batch 验收、GUI 重启、self-hosted runner、JUnit 证据 | 单机 L0/L1/L2 三层验收 + 改后数值回查 |

## 为什么不能互换

- **桥不同**：上游 `NxMcpGuiBridge.dll` 面向 NX2206/NX2506，本机 `NXMcPRemotingServer.dll`
  面向 NX2007 且走 .NET Remoting，**没有**上游的 token / 描述符 / 双桥所有权协议。
- **对象模型不同**：上游用会话内不透明 `object.id` + 注册表；本机是真实 NXOpen 对象 / tag，
  且 **tag 会重编号**。上游的「撤销 / 回滚 / undo mark」在本机没有等价机制。
- **工具名不同**：`nx_status` / `nx_list_bodies` / `nx_undo` 等在本仓库**不存在**。
- **结论不能套用**：上游「移动实体可用」「GUI 桥需签名」等结论均不适用于 NX2007 绑定。

> 一句话：**上游教方法，本仓库干实活。** 不要用上游的 C# GUI 桥替换本机 DLL。

## 3.2.0 借鉴了什么

| 上游做法 | 本仓库落地 |
| --- | --- |
| `CLAUDE.md` 仓库约定 | `AGENTS.md`（含「接活第一步」「三方一致」） |
| `CONTRIBUTING.md` / `SECURITY.md` | 同名的轻量版，按 NX2007 回环边界重写 |
| `CHANGELOG.md` / `RELEASE.md` | `CHANGELOG.md` + `docs/validation.md` 的分层验收 |
| `docs/architecture.md`（对象生命周期 / 恢复契约） | 同名文档，但改写为本机真实链路与「无 undo mark」的恢复方式 |
| `docs/inspection-contract.md` | 同名文档，改为「已验证的查询契约 + 已知不可靠项 + 明确不做的提案」 |
| `docs/real-nx-validation.md`（证据分级） | `docs/validation.md`：文档声明 ≠ CI 通过 ≠ 真机正确 |
| `tests/` + `.github/workflows/ci.yml` | `scripts/validate_repo.py` + `tests/` + 零 NX 依赖的 `validate.yml` |
| 技能 75 行「改前查询 / 改后验证 / 恢复」 | 技能 §17 已吸收；3.2.0 增补 §20 映射到本机具体工具 |

## 刻意没借鉴什么

- 上游 16 个定型工具 / 34 个 legacy / `nx_measure_*` 提案 —— 本机工具面已够用，不引入没验证过的 API。
- 20 轮 batch 验收、GUI 重启测试、self-hosted runner、JUnit 证据与发布门禁 —— 需要 NX2506/2206
  与专用 runner，本机只有一台 NX2007；用 L0/L1/L2 三层单机验收替代。
- pre-commit / mypy / pytest-cov 覆盖率门槛 —— 本仓库以脚本与文档为主，零依赖静态自检更贴合。
- 上游 `NxMcpGuiBridge.dll` 与签名流程 —— 见上「不能互换」。

## 上游副本位置

本机参考副本在 `E:\workbuddy-成果\2026-09-15-12-10-47\NX_MCP_ref`（HEAD `4a7c8811`），
只读参考；**不要**把它的文件拷进 `CAD-Agent-Hub/MCP/UG/` 覆盖运行代码。
