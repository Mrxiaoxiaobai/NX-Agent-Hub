# CAD-Agent-Hub · NX 建模能力清单

> 最后真机核验：**2026-11-09** ｜ 技能 `nx-mcp-bridge-modeling` **v3.1.0** ｜ 桥 **v0.20.1** ｜ **Siemens NX 2007**
>
> 本文件是「仓库内容 = 本机真实能力」的对照表。能力有变化时，同步更新本文件与
> `skills/nx-mcp-bridge-modeling/SKILL.md`，避免文档停留在旧结论。

## 1. 当前状态（真机实测，不是推断）

| 项目 | 实测结果 |
|---|---|
| 桥链路 | `mcp__siemens-nx__ping` → `ok:true`, `transport=dotnet-remoting`, `python=3.8.12` |
| 端点 | `http://127.0.0.1:48161/NXOpenSession`（.NET Remoting / HTTP，非裸 JSON 套接字） |
| NX 应用 | `UG_APP_MODELING`，工作零件 `_model1` |
| MCP 服务器 | `MCP/UG/server.py`（`FastMCP("siemens-nx")`，**生产入口**） |
| 旧入口 | `MCP/UG/mcp_server.py`（slim，48160 TCP，**不要用作连接器入口**） |
| 连接器 | `~/.workbuddy/mcp.json` → `siemens-nx`；绝对路径钉死 + `cwd` + UTF-8 |
| 成果落点 | `D:\三维建模结果`（`NX_MCP_WORKSPACE`，由 `nx_ready.py` 启动 NX 时注入，目录自动创建） |
| 过程可见 | 用户直接看 NX 窗口实时生长；**默认不截图**（2026-11-09 用户明确取消每步截图） |

## 2. 链路

```
WorkBuddy 连接器 siemens-nx
  → stdio 启动 MCP/UG/server.py
  → nx_bridge_client.py（remoting 传输）
  → NXRemoteClient.exe → http://127.0.0.1:48161/NXOpenSession
  → NX 进程内 NXMcPRemotingServer.dll → NXOpen
```

`run_python` 在 **NX 进程内**执行真实 NXOpen（CPython 3.8，非 IronPython，对象非代理）。
代码末尾给 `result = ...` 即可回传数据。

## 3. ✅ 已真机验证「可用」

### 3.1 建模 / 造型
- 长方体 `CreateBlockFeatureBuilder`、草图 `create_parametric_sketch`、拉伸 `CreateExtrudeBuilder`。
- **圆/圆柱免草图**：`work.Curves.CreateArc(center, xDir, yDir, r, 0.0, 2π)` → 拉伸。
- **任意精确椭球**：`CreateSphereBuilder` + `CreateScaleBuilder` 非均匀缩放（Y 因子填 `ky/2`，球心做反算补偿）。
- 布尔 `CreateBooleanBuilder`（Unite/Subtract/Intersect）——不相交会静默失败，必须每步校验体数。
- 装配：零件直接建在最终位姿、零移动；`NewDisplay('name', NXOpen.Part.Units.Millimeters)`（**2 参数**）。
- 视图：`Orient(Trimetric)` → `Rotate((0,0,0),(0,0,1), 67.5)` → `Fit()`。
- 上色 `ufs.Obj.SetColor / SetTranslucency`；色板 159 中灰 / 216 黑 / 150 深粉红 / 91 浅蓝。
- 存盘 `work.Save(NXOpen.BasePart.SaveComponents.TrueValue, NXOpen.BasePart.CloseAfterSave.FalseValue)`（**必须两参数**）。

### 3.2 特征编辑（2026-11-09 新增，本轮重点）
| 操作 | 可靠路径 |
|---|---|
| 删倒角/倒圆特征 | `uf.Obj.DeleteObject(f.Tag)`（`import NXOpen.UF` 必须显式）；实测 3 个 BLEND 一次删净，特征 16→13 |
| 批量倒角 | `mcp__siemens-nx__chamfer_edges(edge_indices, distance=2.0, body_index=0, feature_name)`；一次 38 条边成功 |
| 倒圆 | `mcp__siemens-nx__fillet_edges(...)`（同族专用工具） |
| 开圆孔 | `mcp__siemens-nx__create_cylindrical_hole(origin, diameter, depth, direction, target_body_index, feature_name)`；5mm 通孔成功 |
| 拓扑定位 | `b.GetFaces()/b.GetEdges()/f.GetEdges()/e.GetVertices()`；顶点是 **Point3d**，直接 `.X/.Y/.Z` |
| 改后验证 | `Counter(f.FeatureType ...)` + 面/边数（倒角+开孔后 16 面→79 面、42 边→174 边） |

**铁律：倒角 / 倒圆 / 开孔一律走连接器专用工具，不在 `run_python` 里手搓 builder。**

### 3.3 查询 / 验证
- `list(work.Bodies)`（唯一可靠的体计数）、`work.Features.GetFeatures()`。
- `ufs.ModlGeneral.AskBoundingBox(tag)` → 6 个数 min/max。
- 就绪判据只认 `python nx_ready.py --status` → `RESULT: READY`。

## 4. ❌ 已真机验证「不可用」（别再重试）

- **移动/旋转实体**：`CreateMoveObjectBuilder` 实机工厂不存在、`MoveBodyBuilder.BodyToMove` 只读、`UF TransformEntities` 对 body no-op。→ 删除重建或建成目标姿态。
- `work.Features.DeleteFeature([f])` 不存在（只有 `SuppressFeatures`）。
- `run_python` 里 `CreateEdgeBlendBuilder`：`AddChain` 不存在、`AddChainset(collector, radius)` 需要的 `EdgeMultipleSeed` / `CollectionManager` 本绑定里完全没有。
- `uf.Modl.BlendEdge(...)`：第 6 参是输出 `unsigned int` tag，本绑定无 `NXOpen.Tag` 类型。
- `Face.GetSurface()` / `Face.AskFaceData()` 不存在；`uf.Modl.AskFaceData(tag)` 对 B‑曲面返回零法向 → **不能用面法向判顶面**，改用「面边顶点坐标」拓扑法。
- `mcp__siemens-nx__inspect_body_topology` 报 `0 bodies`，与进程内 `list(work.Bodies)` 不一致。
- `MCP/UG/diagnose.py` 用 HTTP GET 探测 Remoting 端口，会误报「桥未就绪」。

## 5. 连接器配置要点（`~/.workbuddy/mcp.json`）

模板见 `MCP/UG/config/siemens-nx.mcp.json.example`。2026-11-09 补齐的关键项：

1. `cwd` 固定为 `MCP/UG`，避免相对路径解析漂移。
2. `NX_MCP_CLIENT_EXE` / `NX_MCP_REMOTE_OPS` / `NX_MCP_NXOPEN_DLL` 三个依赖用绝对路径钉死。
3. `NX_MCP_WORKSPACE` 与 `nx_ready.py::nx_env()` 保持一致（**NX 侧**读的是 NX 进程环境变量，光写 mcp.json 无效）。
4. `PYTHONUTF8=1` / `PYTHONIOENCODING=utf-8` / `PYTHONPATH` 防中文路径乱码、保证模块导入。
5. 保留 `UGII_BASE_DIR` / `UGII_USER_DIR` / `NX_MCP_TRANSPORT=remoting` / `NX_MCP_REMOTING_PORT=48161` / `NX_MCP_ALLOW_EXECUTE=1`。

> 改完 `mcp.json` 不会自动生效：需在 WorkBuddy 连接器管理里对 `siemens-nx` 点一次「信任 / Trust」，必要时重启 WorkBuddy。

## 6. 文件对照（仓库 ↔ 本机）

| 仓库路径 | 本机位置 / 用途 |
|---|---|
| `skills/nx-mcp-bridge-modeling/SKILL.md` | `~/.workbuddy/skills/nx-mcp-bridge-modeling/SKILL.md`（v3.1.0，生效技能） |
| `skills/nx-journal-automation/SKILL.md` | 离线 journal 兜底（仅桥不可用时） |
| `MCP/UG/workbuddy_scripts/nx_ready.py` | 工作区根目录 `nx_ready.py`（一键就绪 + 注入环境变量） |
| `MCP/UG/workbuddy_scripts/nx_shot3.py` | 工作区根目录 `nx_shot3.py`（**按需**截图，非默认） |
| `MCP/UG/config/siemens-nx.mcp.json.example` | `~/.workbuddy/mcp.json` 的模板 |
| `CAPABILITIES.md` | 本文件，能力对照表 |

上游参考：`Mrxiaoxiaobai/NX_MCP`（fork of `DreamEnding/NX_MCP`）—— 官方建模方法论来源；
本机部署是面向 NX2007 适配的工作副本，**不要**用上游 C# GUI 桥替换本机 `NXMcPRemotingServer.dll`。

## 6.1 v3.1.0 二次优化（2026-11-09）

对比 586 行线上原版 / 143 行重建版后，对技能做了清理：

1. **统一 Windows 路径写法**：修正 `D://三维建模结果`、`D:/`、`C:/`、`E:/` 混用斜杠；JSON 模板内保持合法 `\`。
2. **移除 §4.1 / §4.2 死代码**：两段被误标「可用」但真机不可用的 MoveBuilder 示例（35 行）删除，只留结论。
3. **修正 §4.4 反向结论**：原写「移动实体存在且可用」→ 改为真机定稿「一律不可用」。
4. **能力矩阵孔行**：旧 HoleBuilder 状态由 ✅ 改为「仅 journal 路径」，桥接路径明确指向 `create_cylindrical_hole`。
5. **新增 §19 三方对照表 + 纪律**：技能只能「原版上增补 + 修正」，绝不精简重写；同步后必跑逐行 diff（保留率 > 95%）。

校验结果：586 行原版 **534/586 行逐行保留（91.1%，删掉的 35 行是死代码）**、40 个关键配方关键词零丢失、四处技能副本 md5 一致。

## 7. 交付约定

- 用户只发一句话，其余全自动；不给选择题、不让用户敲命令。
- 汇报用 **✅ 清单 + 一句话结论**，不复述 API / 路径术语。
- 模型统一存 `D:\三维建模结果\<名字>.prt`。
- **默认不截图**；仅用户明确要求或需自证造型时才截。
- 硬前提：**用户本机开着 NX**（桌面 `nx_start.bat`）。AI 沙箱拉起的 NX 会随工具调用结束被回收，桥随之中断。
