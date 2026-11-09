# 安全边界

本仓库的 NX 桥是**单人、单机、本地回环**的自动化工具，不是网络服务。
请按这个前提理解下面的边界，不要把部署范围扩大。

## 信任边界

- 桥只监听 `127.0.0.1:48161/NXOpenSession`（.NET Remoting / HTTP），不对外暴露，不做远程访问。
  上游 `NX_MCP` 的「带 token 的回环 JSON-RPC + 描述符 ACL」是更严格的模型；本机端口
  **没有等价的鉴权层**，因此必须依赖 Windows 本机用户隔离，不要做端口转发或绑到 `0.0.0.0`。
- `NX_MCP_ALLOW_EXECUTE=1` 意味着 `run_python` 可以在 **NX 进程内执行任意 Python/NXOpen**。
  这等于把本机 NX 会话的完整控制权交给 MCP 客户端。只在自己信任的会话里启用。
- 建模产物限制在 `NX_MCP_WORKSPACE`（本机 `D:\三维建模结果`）。不要用共享目录或网络盘。
- NX 进程只加载 `UGII_USER_DIR` 下已编译好的 `NXMcPRemotingServer.dll`；
  不要加载来源不明的 DLL，NX 要求 `dotnet_author` 或 `SignDotNet.exe` 签名。

## 凭据与仓库内容

- GitHub PAT **只在命令行传入** `sync_github.py`，不写入任何仓库文件、不落盘、不进 CHANGELOG。
  推送完成后可在 GitHub → Settings → Developer settings 撤销。
- `~/.workbuddy/mcp.json` 含本机绝对路径，属于本机配置；仓库里只保留带
  `<REPO>` / `<NXROOT>` 占位符的 `MCP/UG/config/siemens-nx.mcp.json.example`。
- 不提交 `.prt`、`.step`、截图、日志、会话描述文件、令牌或任何客户 CAD 数据。

## 报告问题

在本仓库开 issue 即可；若涉及可执行的桥漏洞或凭据暴露，请私信维护者而不要在公开 issue 贴
环境细节、绝对路径、令牌或客户模型。报告请附：技能版本、`nx_ready.py --status` 结果、
`mcp__siemens-nx__ping` 输出、NX 版本、复现步骤（用可丢弃的临时零件）。

## 支持范围

维护中的能力面 = `CAPABILITIES.md` 所列 + 技能 v3.2.0。上游 `NX_MCP` 的 16 个定型工具、
34 个 legacy 工具与 `nx_measure_*` 提案**不在本仓库支持范围内**，相关结论不要互相套用。
