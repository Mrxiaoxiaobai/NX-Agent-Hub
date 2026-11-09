# 查询 / 检查契约

> 对应上游 `NX_MCP` 的 `docs/inspection-contract.md`。上游把「status/units」列为已实现、
> 「measure_*」列为**提案**；本仓库反过来：**查询手段已在真机定型，测量类 API 明确不做**。
> 这里记录的是「用什么查才可信」，不是新的工具接口。

## 1. 唯一可靠的查询入口

`run_python` 在 NX 进程内执行，所有查询都基于真实 NXOpen 对象：

```python
import NXOpen, NXOpen.UF
work = NXOpen.Session.GetSession().Parts.Work
uf   = NXOpen.UF.UFSession.GetUFSession()

bodies   = list(work.Bodies)                 # ← 唯一可靠的体计数
features = list(work.Features.GetFeatures()) # ← 特征类型计数 Counter(f.FeatureType)
bbox     = uf.ModlGeneral.AskBoundingBox(tag)   # 6 个数 minx..maxz
```

| 查询 | 契约 | 备注 |
| --- | --- | --- |
| 体计数 | `len(list(work.Bodies))` | 每次 mutation 后必查；专用工具的 `body_index` 以此为准 |
| 特征 | `work.Features.GetFeatures()` → `FeatureType` | 删 BLEND、确认 HOLE / CHAMFER 是否生成 |
| 包围盒 | `AskBoundingBox(tag)` → `[minx,miny,minz,maxx,maxy,maxz]` | **工作零件绝对坐标系**，与 WCS / 视图无关；长度单位 mm |
| 面 / 边 | `b.GetFaces()` / `b.GetEdges()` / `f.GetEdges()` | 判断倒角是否落地（面数、边数应增加） |
| 顶点 | `e.GetVertices()` → `Point3d`，直接 `.X/.Y/.Z` | 拓扑法定位顶面 / 侧面 / 目标边 |
| 颜色 | `uf.Obj.AskColor(tag, h, s, v)` | `h` 是 **0~360 度**，s/v 是 0~1 |

**单位**：零件以 `Part.Units.Millimeters` 显式创建，坐标与距离一律 mm。
**tag 语义不稳定**（会重编号）：查询结果只在**同一次 `run_python` 调用内**有效，
跨调用要用 `body.SetName()` 按名字找，或用 bbox / 体积重新识别。

## 2. 已实测不可靠的查询（别用）

| 手段 | 实测结果 | 替代方案 |
| --- | --- | --- |
| `mcp__siemens-nx__inspect_body_topology` | 报 `0 bodies`，与进程内 `list(work.Bodies)` 矛盾 | `run_python` 直接查 |
| `Face.GetSurface()` / `Face.AskFaceData()` | 方法不存在；`uf.Modl.AskFaceData(tag)` 对 B 曲面返回零法向 | 「面的边顶点坐标」拓扑法 |
| `MCP/UG/diagnose.py` 的 HTTP GET 探测 | 对 .NET Remoting 端口误报「桥未就绪」 | `nx_ready.py --status` + `ping` |
| 工具返回 `ok:true` | 只说明调用没抛异常，**不说明几何变了** | 改后回查体数 / 特征 / bbox |
| 单看截图 | 看不出内部体数、布尔是否静默失败 | 数值回查为主，截图按需 |

## 3. 改后验证的判据（硬门槛）

1. **布尔 Unite**：`work.Bodies` 个数必须真的 -1。不相交时不报错、工具体不被吸收，
   甚至可能吃掉 target 主体 → 不满足就删除重建，别重试同一个 union。
2. **倒角 / 倒圆**：面数、边数增加；`CHAMFER` / `BLEND` 特征出现；旧的 BLEND 已被删除。
3. **开孔**：`HOLE` 特征出现；bbox 未被意外改动。
4. **装配收尾**：`len(list(work.Bodies))` 等于设计体数，防静默失败。
5. **存盘**：磁盘 `.prt` 非空；重新载入后体数不变。

## 4. 明确不实现的提案

上游 `docs/inspection-contract.md` 提出的 `nx_get_bounding_box` / `nx_measure_volume` /
`nx_measure_distance` 类型化工具，本仓库**不做**：

- 本机已有 `AskBoundingBox` + `run_python`，够用且已真机验证；
- 新增类型化测量工具需要双桥契约一致性测试与真机数值验收，超出本仓库规模；
- 体积 / 最小距离若确有需要，应在 `run_python` 里用 NXOpen 查询并**单独做 L2 验收**，
  不伪装成「已支持的工具」。

同理，上游 `nx_status.units` 由 `BasePart.PartUnits` 读取的做法，本机以「显式 mm 建零件」替代，
不引入新的状态字段。
