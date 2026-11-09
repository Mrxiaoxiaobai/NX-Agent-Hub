# 贡献与改动纪律

本仓库是**本机真实可用的 NX2007 建模工作副本**，不是实验场。任何改动都要能回答：
「真机跑过吗？跑完仓库、本机、线上还一致吗？」

## 三类改动，准入条件不同

| 类别 | 例子 | 准入条件 |
| --- | --- | --- |
| 能力变更 | 新增工具、改 `server.py`、换桥 DLL | 必须有 NX2007 真机成功记录 + 失败重试记录；按 `docs/validation.md` 跑完对应层；同步更新 `CAPABILITIES.md` |
| 配方变更 | 技能里增删 NXOpen 写法 | 逐条真机验证；**只增补/修正，不精简重写**；改完跑逐行 diff |
| 文档 / 脚本变更 | README、CI、自检脚本、模板 | `python scripts/validate_repo.py` 全绿；文档不得出现未经真机验证的 ✅ 结论 |

## 硬规则

1. **不凭文档下结论**。`NXOpen.xml` 存在的 API ≠ 本绑定可用。写进 `CAPABILITIES.md` §4「不可用」的项，
   没有新的真机证据就不要翻转结论。
2. **成功返回 ≠ 模型正确**。布尔、倒角、开孔都可能静默失败（不相交时甚至吃掉主体），
   每一步之后必须回查体数 / 特征数 / 包围盒。
3. **对象引用不跨脚本缓存**。body tag 会重编号；要长期跟踪用 `body.SetName()` 按名字找。
4. **倒角 / 倒圆 / 开孔一律走连接器专用工具**：`chamfer_edges` / `fillet_edges` /
   `create_cylindrical_hole`。`run_python` 里手搓 builder 的路线已实测走不通。
5. **别引入上游桥**。上游 `NX_MCP` 是 NX2506 Python batch / NX2206 C# GUI；
   本机是 `server.py` → `NXRemoteClient.exe` → `127.0.0.1:48161` → 进程内 NXOpen。
   详见 `docs/nx-mcp-comparison.md`。
6. **默认不截图**、**用户只发一句话**，这两条属于交付约定，不要用「更工程化的流程」覆盖。

## 三方同步清单

改完按顺序做完，缺一不可：

- [ ] 本机生效技能 `~/.workbuddy/skills/nx-mcp-bridge-modeling/SKILL.md` 已更新
- [ ] 四处技能副本 md5 一致（生效副本 + `CAD-Agent-Hub` + `github_publish` + `github_sync`）
- [ ] `github_sync/`（推送副本）与 `CAD-Agent-Hub/`（运行副本）内容一致
- [ ] `.github/workflows/validate.yml` 与 `ci/validate.yml` 逐字节一致（L0 会检查）
- [ ] `python scripts/validate_repo.py` 全绿
- [ ] `python sync_github.py <TOKEN>` 推送成功，并逐文件回读比对
- [ ] `CHANGELOG.md` 记一笔，`CAPABILITIES.md` 的版本号同步

## 提交内容边界

**可提交**：源码、测试、Schema、可移植配置示例（占位符路径）、文档。
**不提交**：本机绝对路径写死的配置、`.prt` / `.step` 成果、截图、日志、`.venv`、
`NXRemoteClient.exe` 生成的运行产物、任何令牌或 `bridge.json` 类凭据。

上游 `NX_MCP` 的 PR 模板、pre-commit、发布门禁体系值得借鉴；本仓库按自身规模取了
「静态自检 + 分层验收 + CHANGELOG」这一层，不复制需要 NX2506/self-hosted runner 的部分。
