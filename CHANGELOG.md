# 更新日志

本仓库版本号跟随 `skills/nx-mcp-bridge-modeling/SKILL.md` 的技能版本。
**唯一权威能力事实**是 [CAPABILITIES.md](CAPABILITIES.md)；本文件只记录「什么时候、因为什么、改了什么」，
不替代能力清单。格式参照上游 `NX_MCP` 的 CHANGELOG，但内容与结论全部以本机 NX2007 真机为准。

## [3.2.0] — 2026-11-09

参照 `Mrxiaoxiaobai/NX_MCP`（fork of `DreamEnding/NX_MCP`）的工程化体系做结构性对齐，
**不改任何已真机验证的建模代码**；只补规范、验收与自检，让「仓库内容 = 本机真实能力」可复验。

### Added

- `AGENTS.md`：给 AI 智能体与维护者的仓库约定（对应上游 `CLAUDE.md`）。
- `CONTRIBUTING.md`：能力变更 / 文档变更的准入纪律与三方同步流程。
- `SECURITY.md`：本机回环、进程内执行、令牌与工作区边界。
- `docs/architecture.md`：本机真实链路、进程边界、对象与操作生命周期、失败恢复契约。
- `docs/validation.md`：分层验收清单（静态自检 / 桥自检 / 真机建模），明确「文档声明 ≠ 真机验证」。
- `docs/inspection-contract.md`：查询契约，区分可靠查询手段与已实测不可靠手段。
- `docs/nx-mcp-comparison.md`：两个 NX 仓库的定位对照、借鉴边界与不可互换的原因。
- `scripts/validate_repo.py`：零依赖静态一致性自检；`tests/test_repo_consistency.py` 的 unittest 包装。
- `.github/workflows/validate.yml`：无需 Siemens NX 的托管 CI，只跑静态自检。
- 技能新增 §20：把上游「改前查询 → 对象引用 → 改后验证 → 失败恢复」契约映射到本机具体工具。

### Changed

- `README.md` / `README.zh-CN.md`：加入能力矩阵与验证边界、文档导航、上游定位说明。
- `CAPABILITIES.md`：版本升至 v3.2.0，补工程规范章节与新增文件对照。
- `MCP/UG/config/siemens-nx.mcp.json.example`：注释指向新的架构与验收文档。
- `sync_github.py`：同步清单扩展到全部新增文件，支持 `NX_AGENT_HUB_WORKSPACE` 覆盖工作区路径。

### 明确不做

- 不引入上游 C# GUI 桥（`NxMcpGuiBridge.dll` / NX2206 / NX2506）——本机桥是 `.NET Remoting`，协议与生命周期不同。
- 不启用上游 34 个 legacy 工具、不引入 `nx_measure_*` 提案 API。
- 不重写 `MCP/UG/server.py` 的 82 个专用工具与 `run_python`。

## [3.1.0] — 2026-11-09

对比 586 行线上原版与 143 行重建版后的技能清理：

- 统一 Windows 路径写法；移除 §4.1 / §4.2 两段真机不可用的 MoveBuilder 死代码（35 行）。
- 修正 §4.4「移动实体可用」的反向结论；能力矩阵孔行改为「仅 journal 路径」。
- 新增 §19 三方对照表与「绝不精简重写」纪律。
- 校验：586 行原版逐行保留 534 行（91.1%，删掉的均为死代码），40 个关键配方关键词零丢失，
  四处技能副本 md5 一致。

## [3.0.0] — 2026-11-09

合并 586 行 v1.4.1 真机配方库 + 上游 NX_MCP 方法论 + 特征编辑定稿 + 最终连接器配置；
统一「移动实体不可用」「默认不截图」等历史矛盾结论。

## [1.4.1] — 2026-09-18

586 行真机配方基线：椭球（球 + 非均匀缩放）、视角配方、色板、能力矩阵、STEP 洗白、截图脚本。
