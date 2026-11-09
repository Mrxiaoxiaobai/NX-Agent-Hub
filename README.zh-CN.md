# CAD Agent Hub

面向 Windows 的 CAD/CAE 智能体项目集合，包含 MCP Server、桌面应用桥接、工程 Skill 和可复现的参数化建模示例。

English documentation: [README.md](README.md)

## 包含内容

| 路径 | 用途 |
| --- | --- |
| [`MCP/CATIA`](MCP/CATIA) | CATIA V5 建模与原生 Analysis MCP Server |
| [`MCP/Solidworks`](MCP/Solidworks) | 有状态的 SolidWorks 建模 MCP Server |
| [`MCP/UG`](MCP/UG) | Siemens NX/UG MCP Server 与 NX 内桥接程序 |
| [`fusion_electronics_write_bridge`](fusion_electronics_write_bridge) | Fusion Electronics 本地写入桥 |
| [`skills/ansys-structural-workbench`](skills/ansys-structural-workbench) | 带质量门禁的 ANSYS Workbench 结构分析 Skill |
| [`models`](models) | 可复现的 build123d/cadpy 建模源码示例 |
| [`fusion_starship_v3_builder.py`](fusion_starship_v3_builder.py) | Autodesk Fusion 参数化建模示例 |

每个 MCP 子目录都提供独立的安装和验证说明。这些集成需要相应的商业 CAD 软件，并且通常要求 MCP 与 CAD 软件在同一 Windows 用户和同一权限级别下运行。

## 仓库边界

本仓库只保留源码、测试、Schema、可移植配置示例和文档。不会上传本机工作区、求解任务、缓存、日志、依赖副本、截图或生成的 CAD 二进制文件。文档中的 `C:\path\to\CAD-Agent-Hub` 等示例路径需要替换为实际克隆路径。

## 验证原则

连接真实 CAD 会话前，请先执行各 MCP 项目文档中的单元测试。COM/API 调用成功不等于模型、网格、工程图或仿真结果正确，仍需在原生软件中检查模型树、参数和生成产物。NX 路径另见[分层验收清单](docs/validation.md)。

## NX 建模能力与验证边界（v3.2.0，2026-11-09 核验）

本仓库是本机 **Siemens NX2007 建模的日常主路径**；账号下的 `Mrxiaoxiaobai/NX_MCP`
（fork of `DreamEnding/NX_MCP`）是**方法论教材**。上游的 NX2506 Python batch / NX2206 C# GUI 桥
与本机的 `.NET Remoting` 桥**不能互换**，详见[两库对照](docs/nx-mcp-comparison.md)。

| 领域 | 结论 | 依据 |
| --- | --- | --- |
| 桥链路（`ping` → Remoting `:48161` → 进程内 NXOpen） | ✅ NX2007 真机 | [能力清单](CAPABILITIES.md) §1、技能 §16 |
| 建模：长方体 / 免草图圆柱 / 精确椭球 / 装配 / 视角 / 上色 / 存盘 | ✅ 真机配方 | [建模技能](skills/nx-mcp-bridge-modeling/SKILL.md) §3–§8 |
| 特征编辑：倒角 / 倒圆 / 圆孔 | ✅ **只走专用工具** | [能力清单](CAPABILITIES.md) §3.2、技能 §15 |
| 移动/旋转实体、脚本内 blend builder、面法向判顶面 | ❌ 本绑定实测**不可用** | [能力清单](CAPABILITIES.md) §4 |
| 上游定型 `nx_*` 工具、`nx_measure_*` 提案 | ➖ 本仓库不提供 | [两库对照](docs/nx-mcp-comparison.md) |
| L0 静态自检（文件 / 副本 / 版本 / 模板 / 链接 / 令牌） | ✅ 无需 NX | `scripts/validate_repo.py`、CI |
| L1 桥自检、L2 真机建模验收 | ⚠️ 只能在本机 NX2007 跑，CI 故意不跑 | [验收清单](docs/validation.md) |

**「默认可用」「静态自检通过」「真机验收」是三种不同的结论，不能互相冒充。**
工具返回 `ok:true`、CI 全绿、或 `NXOpen.xml` 里有该 API，都**不能**证明原生 CAD 行为正确；
唯一算数的证据是改后回查（体数 / 特征数 / 包围盒），见[查询契约](docs/inspection-contract.md)。

```
python scripts/validate_repo.py            # L0，零第三方依赖
python -m unittest discover -s tests -v   # 同一套检查的 unittest 包装
```

## 文档导航

| 文档 | 内容 |
| --- | --- |
| [能力清单](CAPABILITIES.md) | 唯一权威的「可用 / 不可用」对照表 |
| [建模技能](skills/nx-mcp-bridge-modeling/SKILL.md) | 820+ 行真机 NXOpen 配方（v3.2.0） |
| [架构](docs/architecture.md) | 进程边界、对象与操作生命周期、失败恢复契约 |
| [验收](docs/validation.md) | L0 / L1 / L2 分层清单与证据分级 |
| [查询契约](docs/inspection-contract.md) | 可靠查询、已实测不可靠项、明确不做的提案 |
| [两库对照](docs/nx-mcp-comparison.md) | 向上游借鉴了什么、刻意没借鉴什么 |
| [智能体约定](AGENTS.md) | 给 AI 与维护者的仓库规则 |
| [更新日志](CHANGELOG.md) · [贡献纪律](CONTRIBUTING.md) · [安全边界](SECURITY.md) | 版本历史、改动准入、信任边界 |

[English README](README.md) 与本页对应。
