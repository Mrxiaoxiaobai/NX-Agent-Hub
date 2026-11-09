# 架构：本机 NX2007 实时建模链路

> 本文对应上游 `NX_MCP` 的 `docs/architecture.md`，但**描述的是本机实现**。
> 上游是「Python sidecar + 带 token 的回环 JSON-RPC + C# GUI / Python batch 桥（NX2206 / NX2506）」；
> 本机是「FastMCP server + .NET Remoting + NX 进程内 NXOpen（NX2007）」。
> 协议、对象模型、恢复机制都不同，**结论不能互相套用**。

## 1. 进程边界

```
WorkBuddy 连接器 (siemens-nx, stdio)
  └─ MCP/UG/server.py            FastMCP("siemens-nx")   82 个专用工具 + run_python
      └─ nx_bridge_client.py     remoting 传输层
          └─ NXRemoteClient.exe  .NET 客户端
              └─ http://127.0.0.1:48161/NXOpenSession
                  └─ NX 进程内 NXMcPRemotingServer.dll
                      └─ NXOpen (CPython 3.8, 进程内真实对象，非代理)
```

| 层 | 拥有什么 | 不拥有什么 |
| --- | --- | --- |
| `server.py`（NX 外） | stdio、工具 schema、参数校验、结果封装 | **不 import NXOpen**，不持有 NX 对象 |
| `NXRemoteClient.exe` | .NET Remoting 编组、请求转发 | 不执行建模逻辑 |
| NX 进程内 DLL | 当前 NX 会话、工作零件、所有 NXOpen 调用 | 不做 MCP 协议协商 |
| NX 界面 | 用户实时看到的模型生长 | 不受 journal 模态框锁死 |

`run_python` 的代码在 **NX 进程内**执行，拿到的是真实 NXOpen 对象（不是 ID 代理）：
`import NXOpen.UF` 必须显式；所有数值参数必须是 `float`；代码末尾赋 `result = ...` 即可回传数据。

## 2. 启动与就绪

用户会话里必须有一个开着 NX 的进程（沙箱拉起的 NX 会随工具调用结束被回收，桥随之中断）。
`nx_ready.py` 是唯一就绪判据：

- 判据 = TCP 连上 `127.0.0.1:48161` **且** `%TEMP%\nx_mcp_remoting_server.log` 最近事件仍是 `Ready on`
  （只连端口会假阳性：日志里若已打印 `Server stopped`，必须判未就绪）。
- `READY` → 直接建模；`NOT_READY` → 不带 `--status` 重跑（自动拉起 NX 并等桥上线）；
  `NX_RUNNING_NO_BRIDGE` → 走离线 journal 兜底，不再开第二个 NX。
- 启动 NX 时**显式注入** `UGII_USER_DIR`（指向 `MCP/UG/nx_user`），NX 才会自动加载桥 DLL；
  同时注入 `NX_MCP_WORKSPACE` 等变量——NX 读的是**自己进程**的环境变量，写进 `mcp.json` 不够。

## 3. 工具面与执行模型

- 82 个专用工具覆盖建模、装配、CAM、制图、机床仿真；`run_python` 是兜底，可直接写任意 NXOpen。
- **倒角 / 倒圆 / 开孔必须用专用工具**（`chamfer_edges` / `fillet_edges` /
  `create_cylindrical_hole`）；`run_python` 里对应的 builder 在本绑定缺类型，已实测走不通。
- NXOpen 只在 NX 主线程串行执行 → **一次只发一个建模操作**，不要并发。
- 建模结果落 `NX_MCP_WORKSPACE`（`D:\三维建模结果`）；保存必须两参数：
  `work.Save(BasePart.SaveComponents.TrueValue, BasePart.CloseAfterSave.FalseValue)`。

## 4. 对象与操作生命周期（与上游差异最大的一节）

| 主题 | 上游 `NX_MCP` | 本机实现 |
| --- | --- | --- |
| 对象引用 | 会话内不透明 `object.id`，失效即拒绝 | **真实 NXOpen 对象 / tag**，无注册表 |
| tag 稳定性 | ID 在 part 关闭后失效 | ⚠️ **tag 会重编号**，同一实体两次读可能不同 → 绝不跨脚本缓存 tag |
| 长期跟踪 | 由桥维护注册表 | `body.SetName('NAME')` 后按名字找；临时识别用 bbox / 体积 |
| 撤销 / 回滚 | 每个 mutation 有 undo mark，失败自动回滚 | **没有等价机制**；失败靠删除重建 + 回查体数 |
| 恢复状态 | `execution_state = not_started / unknown`、`NX_ROLLBACK_FAILED` | 无状态字段；靠「改后回查」判断到底有没有生效 |

由此得出本机恢复契约（对应上游 §"Recovery and stopping conditions"）：

1. **改前查询**：`list(work.Bodies)`、`work.Features.GetFeatures()`、包围盒，确认工作零件身份、体数与单位。
2. **改后验证**：每次布尔 / 倒角 / 开孔 / 新建体之后立刻回查体数、特征类型计数、面/边数、包围盒。
   布尔 Unite **可能静默失败**：不相交时不报错、工具体不被吸收，甚至吃掉 target 主体。
   **判定标准 = `work.Bodies` 个数确实变化**，不是「工具返回 ok」。
3. **失败不重放**：超时、断连、返回异常时，先重新查询模型状态再决定；绝不原样重发同一个 mutation。
4. **丢弃缓存引用**：任何失败 / 删除 / 重建之后，重新取 bodies 与 faces，不再用旧 tag。
5. **出错不循环**：同一个错误不重复尝试；改路线（专用工具 / 删除重建 / 建成目标姿态）而不是重试。

## 5. 单位与坐标系

- 零件用 `Part.Units.Millimeters` 显式创建；几何坐标、拉伸距离均以 **mm** 为单位。
- `ufs.ModlGeneral.AskBoundingBox(tag)` 返回工作零件绝对坐标系下的 6 个数
  `minx,miny,minz,maxx,maxy,maxz`，与当前视图 / WCS 无关。
- NX `Front` 视图从 **+Y** 看 → 朝观众的面放 **-Y** 侧；轴测用 `Orient(Trimetric)` +
  `Rotate((0,0,0),(0,0,1),67.5)` + `Fit()`。
- 面法向在本绑定取不到（B 曲面 `AskFaceData` 返零）→ 判顶面/侧面用「面的边顶点坐标」拓扑法。

## 6. 安全与认证边界

本机桥**没有**上游那套 token / 描述符 ACL / 双桥所有权协议；它只监听 `127.0.0.1:48161`，
依赖 Windows 本机用户隔离。详见 [SECURITY.md](../SECURITY.md)。
`NX_MCP_ALLOW_EXECUTE=1` 等价于把 NX 会话的进程内执行权交给 MCP 客户端，勿做端口转发。

## 7. 不提供的能力（别照上游文档找）

没有 `nx_status.units` / `nx_undo` / `nx_list_bodies` 这类型化工具，没有 undo mark、没有
`readOnlyHint`/`destructiveHint` 注解、没有双桥契约一致性测试、没有 `nx_measure_*`。
要查询就 `run_python`；要撤销就删除重建。上游的 `nx_*` 工具名在本仓库**不存在**。
