# 分层验收清单

> 对应上游 `NX_MCP` 的 `docs/real-nx-validation.md` / `RELEASE.md`。
> 上游要跑 20 轮 batch + GUI 重启 + self-hosted runner；本仓库按单机单人规模取三层，
> **但保留同一个核心原则：不同层级的证据不能互相冒充**。

## 证据分级（最重要）

| 层级 | 能证明什么 | **不能**证明什么 |
| --- | --- | --- |
| L0 静态自检 | 仓库文件齐全、副本一致、JSON 可解析、链接有效、版本号统一 | 任何 NX 行为 |
| L1 桥自检 | 链路连通、`run_python` 能在 NX 进程内执行、工作零件存在 | 建模结果正确 |
| L2 真机建模验收 | 某个 API / 工具在本机 NX2007 上真的生效 | 别的 API 也生效 |
| 文档 / `NXOpen.xml` | 接口在文档里存在 | 在本绑定能用（已多次证伪） |

**`工具返回 ok`、`server.py` 导入成功、CI 全绿、文档写了 ✅ —— 都不是建模正确的证据。**
唯一证据是 L2 的「改后回查」：`list(work.Bodies)` 体数、特征类型计数、面/边数、包围盒。

## L0 — 静态自检（无需 NX，CI 跑这一层）

```
python scripts/validate_repo.py
python -m unittest discover -s tests -v
```

通过判据：所有检查项 `OK`，退出码 0。检查项见 `scripts/validate_repo.py`：
关键文件存在、技能四处副本 md5 一致、连接器模板 JSON 可解析且占位符齐全、
`CAPABILITIES.md` 与技能版本号一致、README 文档链接指向真实文件、无令牌泄漏。

## L1 — 桥自检（需要用户会话里开着 NX）

```
python nx_ready.py --status        # 期望 RESULT: READY
mcp__siemens-nx__ping              # 期望 ok:true, transport=dotnet-remoting, python=3.8.x
```

再跑技能 §16.3 的配置自检：读 `~/.workbuddy/mcp.json` 的 env → 逐个检查 7 个绝对路径存在 →
用同一 env + cwd 实例化 `NXBridgeClient()` → 用 `stdin=DEVNULL` 启动 `server.py` 无导入错误。

> ⚠️ `MCP/UG/diagnose.py` 用 HTTP GET 探 Remoting 端口会**误报未就绪**，不要当判据。

## L2 — 真机建模验收（改能力 / 改配方后必跑）

每次只验一项，在可丢弃零件上做。通过的判据是「改后回查的数值符合预期」，不是没报错。

| 场景 | 最小验收动作 | 通过判据 |
| --- | --- | --- |
| 新建体 | 建长方体 → 回查体数与 `AskBoundingBox` | 体数 +1；bbox 三向尺寸等于输入 mm 值 |
| 布尔 Unite | 两真相交体合并 → 回查体数 | **体数确实 -1**；否则视为静默失败，删除重建 |
| 批量倒角 | `chamfer_edges(edge_indices, distance=2.0)` → 回查面/边数 | 面/边数增加，无残留旧 BLEND 特征 |
| 开孔 | `create_cylindrical_hole(...)` → 回查特征计数 | 出现 HOLE 特征，且 bbox 未被意外改动 |
| 椭球 | 球 + 非均匀缩放 → 比对 bbox | 6 个数逐位吻合目标半轴（注意 Y 形状因子是设定值的 2 倍） |
| 存盘 | `work.Save(两参数)` → 检查磁盘 | `D:\三维建模结果\<名字>.prt` 非空，重新载入体数不变 |
| 装配 | 全部件建在最终位姿 | 跑完 `len(list(work.Bodies))` 等于设计体数，防静默失败 |

**验收前记录**：NX 版本（NX2007）、桥版本 v0.20.1、技能版本、`nx_ready.py --status` 输出、
工作零件名、验收日期。**验收后记录**：实际回查到的数值，写进 `CAPABILITIES.md` 与 `CHANGELOG.md`。

## 已知真机结论（2026-11-09 定稿，作为回归基线）

- ✅ 可用：`CreateArc` 免草图圆件、球+缩放椭球、`Orient`+`Rotate` 视角、UF 删特征、
  专用工具倒角/倒圆/开孔、拓扑法顶点识别、`AskBoundingBox`。
- ❌ 不可用：移动 / 旋转实体（`CreateMoveObjectBuilder` 工厂不存在、`MoveBodyBuilder.BodyToMove`
  只读、`UF TransformEntities` no-op）、`work.Features.DeleteFeature`、`CreateEdgeBlendBuilder`、
  `uf.Modl.BlendEdge`、面法向判顶面、`inspect_body_topology`（报 0 bodies）。

这些结论写进 `CAPABILITIES.md` §3 / §4，没有新的 L2 证据不要翻转。

## 三方一致性（交付前最后一关）

```
python scripts/validate_repo.py
python sync_github.py <TOKEN> --check
python sync_github.py <TOKEN>
# 再逐文件 GET 回读，与本地逐字节比对
```

本机 Git 走代理报 CONNECT tunnel 502 → 同步一律走 GitHub Contents API，不用 `git push`。
L0 可以在任何机器跑；L1 / L2 **只能在这台装着 NX2007 的机器上跑**，CI 故意不跑它们。
