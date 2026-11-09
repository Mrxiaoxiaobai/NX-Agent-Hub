# -*- coding: utf-8 -*-
r"""
把「当前 NX 建模能力」同步到 GitHub `Mrxiaoxiaobai/NX-Agent-Hub` 的 main 分支。

两条写入通道，任选其一：
    python sync_github.py --connector       # 走 WorkBuddy GitHub 连接器（需要集成对该仓库有写权限）
    python sync_github.py <TOKEN>           # 走 classic/fine-grained PAT（Contents: write）
    python sync_github.py <TOKEN> --check  # 只验证 token、列出待同步文件
    GITHUB_TOKEN=xxx python sync_github.py # 或用环境变量传 token

PAT 需要 classic PAT 的 `repo` 权限（或 fine-grained PAT 对该仓库的 Contents: write）。

背景：本机 Git 走代理会报 CONNECT tunnel 502，因此一律走 GitHub API / MCP 连接器，不用 git push。
2026-11-09 实测：GitHub 连接器读正常，但写返回
  `403 Resource not accessible by integration`
（GitHub App 未获该仓库 contents:write 授权）。补授权后 `--connector` 即可直接用。

v3.2.0：同步清单扩展到工程规范文档、静态自检脚本与 CI（见 FILES）。
内容未变的文件会按 git blob sha 自动跳过，避免无谓提交。
CI 工作流 `.github/workflows/validate.yml` 需要额外的 Workflows 权限；缺权限时
自动降级为只同步等价的 `ci/validate.yml` 并打印 WARN，不阻断同步（见 OPTIONAL_WORKFLOWS）。
推送前后建议跑 `python scripts/validate_repo.py`（L0 全绿）并逐文件回读比对。
工作区定位：环境变量 `NX_AGENT_HUB_WORKSPACE` 优先，否则从脚本所在位置自动推断；
不写死本机绝对路径，因此这份脚本可直接放进仓库。
"""
import base64
import io
import json
import os
import subprocess
import sys
import urllib.error
import urllib.request

# 注：仓库于 2026-11-09 改名为 NX-Agent-Hub；旧名由 GitHub 自动重定向，仍可访问。
OWNER, REPO, BRANCH = "Mrxiaoxiaobai", "NX-Agent-Hub", "main"


def _workspace():
    """定位本机工作区：env 优先 → 从脚本位置推断 → 当前目录。"""
    env = os.environ.get("NX_AGENT_HUB_WORKSPACE")
    if env:
        return env
    here = os.path.dirname(os.path.abspath(__file__))
    candidates = [
        os.path.dirname(os.path.dirname(here)),  # <WS>/github_sync/scripts/
        here,                                    # <WS>/ 或 <WS>/scripts/
        os.path.dirname(here),                   # <WS>/scripts/
    ]
    for c in candidates:
        if os.path.isdir(os.path.join(c, "github_sync")):
            return c
    return os.getcwd()


WS = _workspace()
PAYLOAD = os.environ.get("NX_AGENT_HUB_PAYLOAD") or os.path.join(WS, "github_sync")

FILES = [
    # 核心能力与生效内容
    "skills/nx-mcp-bridge-modeling/SKILL.md",
    "MCP/UG/workbuddy_scripts/nx_ready.py",
    "MCP/UG/config/siemens-nx.mcp.json.example",
    "CAPABILITIES.md",
    "README.md",
    "README.zh-CN.md",
    # v3.2.0 参照上游 NX_MCP 补齐的工程规范
    "CHANGELOG.md",
    "AGENTS.md",
    "CONTRIBUTING.md",
    "SECURITY.md",
    "docs/architecture.md",
    "docs/validation.md",
    "docs/inspection-contract.md",
    "docs/nx-mcp-comparison.md",
    # 静态自检、测试、CI 与同步脚本自身
    "scripts/validate_repo.py",
    "scripts/sync_github.py",
    "tests/test_repo_consistency.py",
    "ci/validate.yml",
]
# GitHub 对 .github/workflows/* 的写入要求 classic PAT 的 `workflow` scope，
# 或 fine-grained PAT 的「Workflows: write」。当前令牌没有该权限：Contents API
# 返回 404 混淆响应，Git Data API 建 tree 同样被拒。因此 workflow 作为**可选增强**
# 单独尝试：成功则线上 CI 自动生效；不成功则 ci/validate.yml 已保证内容同步，
# 不阻断整个同步流程（也不再把「内容一致」误报为失败）。
OPTIONAL_WORKFLOWS = [
    (".github/workflows/validate.yml", "ci/validate.yml"),
]
MSG = "feat: align with NX_MCP engineering practices (v3.2.0 docs, validation, static checks, CI template)"


def request(token, method, url, data=None):
    body = json.dumps(data).encode("utf-8") if data is not None else None
    req = urllib.request.Request(url, data=body, method=method)
    req.add_header("Authorization", "Bearer " + token)
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("Content-Type", "application/json")
    req.add_header("User-Agent", "workbuddy-nx-capability-sync")
    try:
        with urllib.request.urlopen(req, timeout=45) as resp:
            raw = resp.read().decode("utf-8", "replace")
            return resp.status, json.loads(raw) if raw else {}
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode("utf-8", "replace") or "{}")
    except Exception as e:
        return -1, {"message": repr(e)}


def read_files():
    out = []
    for rel in FILES:
        p = os.path.join(PAYLOAD, rel.replace("/", os.sep))
        if not os.path.isfile(p):
            raise RuntimeError("本地文件缺失: " + p)
        out.append((rel, io.open(p, encoding="utf-8", newline="").read()))
    return out


def blob_sha(raw):
    """计算本地内容的 git blob sha，用于跳过内容未变的文件、避免无谓提交。"""
    import hashlib
    h = hashlib.sha1()
    h.update(b"blob %d\0" % len(raw))
    h.update(raw)
    return h.hexdigest()


def sync_via_pat(token, check_only=False):
    code, info = request(token, "GET", "https://api.github.com/user")
    if code != 200:
        print("ERROR: token 无效或已过期 (HTTP %s): %s" % (code, info.get("message")))
        print("       请到 https://github.com/settings/tokens 生成带 repo 权限的新 PAT。")
        return 1
    print("TOKEN OK: login=%s" % info.get("login"))
    items = read_files()
    print("待同步 %d 个文件（payload=%s）:" % (len(items), PAYLOAD))
    for rel, content in items:
        print("  %-58s %6d bytes" % (rel, len(content.encode("utf-8"))))
    if check_only:
        print("--check 模式，未写入。")
        return 0

    failed = []
    for rel, content in items:
        raw = content.encode("utf-8")
        api_path = "https://api.github.com/repos/%s/%s/contents/%s" % (OWNER, REPO, rel)
        code, cur = request(token, "GET", api_path + "?ref=" + BRANCH)
        sha = cur.get("sha") if code == 200 else None
        if code not in (200, 404):
            print("  FAIL %-52s GET HTTP %s %s" % (rel, code, cur.get("message")))
            failed.append(rel)
            continue
        if sha == blob_sha(raw):
            print("  SAME %-52s 内容未变，跳过" % rel)
            continue
        data = {
            "message": MSG,
            "content": base64.b64encode(raw).decode("ascii"),
            "branch": BRANCH,
        }
        if sha:
            data["sha"] = sha
        code, res = request(token, "PUT", api_path, data)
        if code in (200, 201):
            commit = (res.get("commit") or {}).get("sha", "")[:8]
            print("  OK   %-52s %s commit=%s" % (rel, "updated" if sha else "created", commit))
        else:
            print("  FAIL %-52s PUT HTTP %s %s" % (rel, code, res.get("message")))
            failed.append(rel)

    # 可选增强：把同一份 CI 配置写进 .github/workflows/ 让 GitHub Actions 真正跑起来。
    # 缺 Workflows 权限时不算同步失败，ci/validate.yml 已保证内容一致。
    for target, source in OPTIONAL_WORKFLOWS:
        src = os.path.join(PAYLOAD, source.replace("/", os.sep))
        if not os.path.isfile(src):
            continue
        raw = io.open(src, "rb").read()
        api_path = "https://api.github.com/repos/%s/%s/contents/%s" % (OWNER, REPO, target)
        code, cur = request(token, "GET", api_path + "?ref=" + BRANCH)
        sha = cur.get("sha") if code == 200 else None
        if sha == blob_sha(raw):
            print("  SAME %-52s CI 已启用" % target)
            continue
        data = {"message": MSG, "content": base64.b64encode(raw).decode("ascii"),
                "branch": BRANCH}
        if sha:
            data["sha"] = sha
        code, res = request(token, "PUT", api_path, data)
        if code in (200, 201):
            print("  OK   %-52s CI 已启用" % target)
        elif code in (403, 404):
            print("  WARN %-52s 令牌缺 Workflows 权限，CI 未自动启用" % target)
            print("       内容已同步到 %s；在 GitHub 网页端把该文件复制到 %s 即可启用，" % (source, target))
            print("       或给 PAT 补 Workflows 权限后重跑本脚本（会自动补上，无需手动改文件）。")
        else:
            print("  WARN %-52s PUT HTTP %s %s" % (target, code, res.get("message")))
    print("=" * 60)
    if failed:
        print("同步未完成，失败 %d 个: %s" % (len(failed), ", ".join(failed)))
        return 1
    print("全部同步完成：https://github.com/%s/%s" % (OWNER, REPO))
    return 0


# ---------------- WorkBuddy GitHub 连接器通道 ----------------

def _mcp_call(url, headers, payload, sid=None, timeout=240):
    h = dict(headers)
    h["Content-Type"] = "application/json"
    h["Accept"] = "application/json, text/event-stream"
    if sid:
        h["Mcp-Session-Id"] = sid
    req = urllib.request.Request(
        url, data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers=h, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.headers.get("Mcp-Session-Id"), r.status, r.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return e.headers.get("Mcp-Session-Id"), e.code, e.read().decode("utf-8", "replace")


def _unwrap(raw):
    txt = "\n".join(l[5:].strip() for l in raw.splitlines() if l.startswith("data:")) if "data:" in raw else raw
    for chunk in txt.split("\n"):
        chunk = chunk.strip()
        if chunk:
            try:
                return json.loads(chunk)
            except Exception:
                pass
    return {"raw": txt[:400]}


def sync_via_connector(check_only=False):
    cfg_raw = os.environ.get("CODEBUDDY_MCP_CONFIG", "")
    if not cfg_raw:
        print("ERROR: 找不到 CODEBUDDY_MCP_CONFIG，GitHub 连接器未在当前会话挂上。")
        return 2
    try:
        cfg = json.loads(cfg_raw)["mcpServers"]["github"]
    except Exception as e:
        print("ERROR: 解析连接器配置失败:", e)
        return 2
    url, headers = cfg["url"], dict(cfg["headers"])
    items = read_files()
    print("连接器通道：%s" % url)
    print("待同步 %d 个文件:" % len(items))
    for rel, content in items:
        print("  %-58s %6d bytes" % (rel, len(content.encode("utf-8"))))
    if check_only:
        print("--check 模式，未写入。")
        return 0

    sid, _, _ = _mcp_call(url, headers, {
        "jsonrpc": "2.0", "id": 1, "method": "initialize",
        "params": {"protocolVersion": "2025-03-26", "capabilities": {},
                   "clientInfo": {"name": "wb-nx-sync", "version": "1.0"}}})
    if not sid:
        print("ERROR: 连接器 MCP 会话建立失败")
        return 1
    _mcp_call(url, headers, {"jsonrpc": "2.0", "method": "notifications/initialized"}, sid)
    args = {
        "owner": OWNER, "repo": REPO, "branch": BRANCH, "message": MSG,
        "files": [{"path": rel, "content": content} for rel, content in items],
    }
    _, code, raw = _mcp_call(url, headers, {
        "jsonrpc": "2.0", "id": 3, "method": "tools/call",
        "params": {"name": "push_files", "arguments": args}}, sid)
    d = _unwrap(raw)
    if "error" in d:
        print("ERROR: JSON-RPC", json.dumps(d["error"], ensure_ascii=False)[:400])
        return 1
    res = d.get("result", {})
    text = "".join(c.get("text", "") for c in res.get("content", []) if c.get("type") == "text")
    print("push_files HTTP %s -> %s" % (code, text[:600]))
    if res.get("isError"):
        print("提示：403 表示 GitHub 集成没有被授予该仓库的写权限；")
        print("      请在 GitHub → Settings → Applications 中把 NX-Agent-Hub 加入该集成的仓库授权，")
        print("      或改用 PAT 通道：python sync_github.py <TOKEN>")
        return 1
    print("全部同步完成：https://github.com/%s/%s" % (OWNER, REPO))
    return 0


def run_l0():
    """推送前跑仓库 L0 静态自检；不通过就中止，避免把不自洽的内容推上线。"""
    script = os.path.join(PAYLOAD, "scripts", "validate_repo.py")
    if not os.path.isfile(script):
        print("WARN: 找不到 L0 自检脚本，跳过：" + script)
        return True
    env = dict(os.environ)
    env["NX_AGENT_HUB_WORKSPACE"] = WS
    env["PYTHONIOENCODING"] = "utf-8"
    proc = subprocess.run([sys.executable, script], env=env, cwd=PAYLOAD,
                          capture_output=True, text=True,
                          encoding="utf-8", errors="replace", timeout=120)
    print(proc.stdout.strip() or proc.stderr.strip())
    if proc.returncode != 0:
        print("ERROR: L0 静态自检未通过，已中止推送。修复后重试。")
        return False
    return True


def main():
    argv = sys.argv[1:]
    check_only = "--check" in argv
    use_connector = "--connector" in argv
    if use_connector:
        if not check_only and not run_l0():
            return 1
        return sync_via_connector(check_only)
    args = [a for a in argv if a != "--check"]
    token = args[0] if args else os.environ.get("GITHUB_TOKEN", "")
    if not token:
        print("ERROR: 缺少写入方式。用法：")
        print("  python sync_github.py --connector")
        print("  python sync_github.py <TOKEN>")
        return 2
    if not check_only and not run_l0():
        return 1
    return sync_via_pat(token, check_only)


if __name__ == "__main__":
    sys.exit(main())
