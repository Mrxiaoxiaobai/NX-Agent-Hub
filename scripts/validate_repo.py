# -*- coding: utf-8 -*-
"""NX-Agent-Hub 静态一致性自检（零第三方依赖，不需要 Siemens NX）。

用法：
    python scripts/validate_repo.py            # 从仓库任意目录运行均可
    python scripts/validate_repo.py --quiet   # 只打印失败项

对应 docs/validation.md 的 L0 层。它只能证明「仓库内容自洽」，
**不能**证明任何 NX 建模行为正确 —— 那一层要跑 docs/validation.md 的 L1 / L2。

可选环境变量：
    NX_AGENT_HUB_WORKSPACE  本机工作区根目录；设置后会额外检查本地四处技能副本
                            与运行副本 CAD-Agent-Hub 的一致性（CI 上不设置 → SKIP）。
"""
import argparse
import json
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
VERSION = "3.2.0"

REQUIRED = [
    "README.md",
    "README.zh-CN.md",
    "CAPABILITIES.md",
    "CHANGELOG.md",
    "AGENTS.md",
    "CONTRIBUTING.md",
    "SECURITY.md",
    "docs/architecture.md",
    "docs/validation.md",
    "docs/inspection-contract.md",
    "docs/nx-mcp-comparison.md",
    "scripts/validate_repo.py",
    "tests/test_repo_consistency.py",
    ".github/workflows/validate.yml",
    "skills/nx-mcp-bridge-modeling/SKILL.md",
    "MCP/UG/config/siemens-nx.mcp.json.example",
    "MCP/UG/workbuddy_scripts/nx_ready.py",
]

# 只检查这些文件里的相对 .md 链接，避免把历史子项目 README 的旧链接算成失败。
LINK_SCOPE = [
    "README.md", "README.zh-CN.md", "CAPABILITIES.md", "CHANGELOG.md",
    "AGENTS.md", "CONTRIBUTING.md", "SECURITY.md",
] + ["docs/" + p.name for p in sorted((ROOT / "docs").glob("*.md"))]

LINK_RE = re.compile(r"\[[^\]]*\]\(([^)]+)\)")
TOKEN_RE = re.compile(r"gh[pousr]_[A-Za-z0-9]{20,}")
SCAN_SUFFIX = {".md", ".py", ".json", ".yml", ".yaml", ".example", ".vb"}


def rel(path):
    return str(path).replace("\\", "/")


def read(path):
    return path.read_text(encoding="utf-8", errors="replace")


def result(name, ok, detail="", skipped=False):
    return ("SKIP" if skipped else ("OK" if ok else "FAIL"), name, detail)


def check_required():
    missing = [p for p in REQUIRED if not (ROOT / p).is_file()]
    return result("关键文件齐全", not missing, "缺失: " + ", ".join(missing) if missing else "%d 个" % len(REQUIRED))


def check_versions():
    problems = []
    skill = ROOT / "skills/nx-mcp-bridge-modeling/SKILL.md"
    cap = ROOT / "CAPABILITIES.md"
    chg = ROOT / "CHANGELOG.md"
    if not all(p.is_file() for p in (skill, cap, chg)):
        return result("版本号统一", False, "关键文件缺失")
    if 'version: "%s"' % VERSION not in read(skill):
        problems.append("SKILL.md frontmatter")
    if "v" + VERSION not in read(cap):
        problems.append("CAPABILITIES.md")
    if "## [%s]" % VERSION not in read(chg):
        problems.append("CHANGELOG.md 最新条目")
    for name in ("README.md", "README.zh-CN.md"):
        p = ROOT / name
        if p.is_file() and "v" + VERSION not in read(p):
            problems.append(name)
    return result("版本号统一 (v%s)" % VERSION, not problems,
                  "不一致: " + ", ".join(problems) if problems else "技能 / 能力清单 / 变更日志 / 双 README")


def check_connector_template():
    p = ROOT / "MCP/UG/config/siemens-nx.mcp.json.example"
    if not p.is_file():
        return result("连接器模板", False, "文件缺失")
    try:
        cfg = json.loads(read(p))
        env = cfg["mcpServers"]["siemens-nx"]["env"]
    except Exception as e:
        return result("连接器模板", False, "JSON/结构错误: %s" % e)
    needed = ["cwd", "UGII_BASE_DIR", "UGII_USER_DIR", "NX_MCP_TRANSPORT",
              "NX_MCP_REMOTING_PORT", "NX_MCP_ALLOW_EXECUTE", "NX_MCP_WORKSPACE",
              "NX_MCP_CLIENT_EXE", "NX_MCP_REMOTE_OPS", "NX_MCP_NXOPEN_DLL",
              "PYTHONUTF8", "PYTHONIOENCODING"]
    cfg_all = json.dumps(cfg, ensure_ascii=False)
    missing = [k for k in needed if k not in cfg_all]
    if missing:
        return result("连接器模板", False, "缺关键项: " + ", ".join(missing))
    if "<REPO>" not in cfg_all or "<NXROOT>" not in cfg_all:
        return result("连接器模板", False, "占位符被替换成本机绝对路径，不可提交")
    if "E:\\workbuddy" in cfg_all or "C:\\Users" in cfg_all:
        return result("连接器模板", False, "含本机绝对路径")
    if env.get("NX_MCP_TRANSPORT") != "remoting":
        return result("连接器模板", False, "transport 不是 remoting")
    return result("连接器模板", True, "可解析 / 占位符齐全 / remoting")


def check_links():
    bad = []
    checked = 0
    for name in LINK_SCOPE:
        p = ROOT / name
        if not p.is_file():
            continue
        for target in LINK_RE.findall(read(p)):
            t = target.strip().split("#")[0]
            if not t or t.startswith(("http://", "https://", "mailto:")):
                continue
            if not t.endswith(".md"):
                continue
            checked += 1
            if not (p.parent / t).resolve().is_file():
                bad.append("%s -> %s" % (name, t))
    return result("文档相对链接", not bad,
                  "失效: " + "; ".join(bad[:6]) if bad else "检查 %d 条" % checked)


def check_no_tokens():
    hits = []
    for dirpath, dirnames, filenames in os.walk(ROOT):
        dirnames[:] = [d for d in dirnames if d not in (".git", ".venv", "__pycache__")]
        for fn in filenames:
            p = Path(dirpath) / fn
            if p.suffix.lower() not in SCAN_SUFFIX and not p.name.endswith(".example"):
                continue
            if p.stat().st_size > 2_000_000:
                continue
            try:
                text = read(p)
            except Exception:
                continue
            for m in TOKEN_RE.findall(text):
                # 文档里的占位符示例不算泄漏
                if set(m.replace("ghp_", "")) == {"x"}:
                    continue
                hits.append(rel(p.relative_to(ROOT)))
                break
    # 允许 sync_github.py 里出现形如 ghp_xxxx 的说明文字，但不允许真实形态的令牌
    return result("无令牌泄漏", not hits, "疑似: " + ", ".join(hits[:6]) if hits else "已扫描文本类文件")


def check_local_copies():
    ws = os.environ.get("NX_AGENT_HUB_WORKSPACE", "")
    if not ws:
        return result("本机四处技能副本", False,
                      "未设置 NX_AGENT_HUB_WORKSPACE（CI 上跳过）", skipped=True)
    import hashlib
    base = Path(ws)
    copies = [
        Path.home() / ".workbuddy/skills/nx-mcp-bridge-modeling/SKILL.md",
        base / "CAD-Agent-Hub/skills/nx-mcp-bridge-modeling/SKILL.md",
        base / "github_publish/skills/nx-mcp-bridge-modeling/SKILL.md",
        base / "github_sync/skills/nx-mcp-bridge-modeling/SKILL.md",
    ]
    present = [p for p in copies if p.is_file()]
    if not present:
        return result("本机四处技能副本", False, "一个副本都找不到", skipped=True)
    digests = {}
    for p in present:
        digests.setdefault(hashlib.md5(p.read_bytes()).hexdigest(), []).append(rel(p))
    ok = len(digests) == 1
    detail = "md5 一致（%d 份）" % len(present) if ok else "不一致: " + str(digests)
    return result("本机四处技能副本", ok, detail)


def check_run_copy():
    ws = os.environ.get("NX_AGENT_HUB_WORKSPACE", "")
    if not ws:
        return result("运行副本同步", False, "未设置 NX_AGENT_HUB_WORKSPACE（CI 上跳过）", skipped=True)
    run = Path(ws) / "CAD-Agent-Hub"
    if not run.is_dir():
        return result("运行副本同步", False, "CAD-Agent-Hub 不存在", skipped=True)
    diff = [p for p in REQUIRED if (ROOT / p).is_file() and
            (not (run / p).is_file() or
             (ROOT / p).read_bytes() != (run / p).read_bytes())]
    return result("运行副本同步", not diff,
                  "不一致: " + ", ".join(diff[:6]) if diff else "运行副本与推送副本逐字节一致")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args()
    rows = [check_required(), check_versions(), check_connector_template(),
            check_links(), check_no_tokens(), check_local_copies(), check_run_copy()]
    for status, name, detail in rows:
        if args.quiet and status != "FAIL":
            continue
        line = "[%-4s] %-26s %s" % (status, name, detail)
        print(line)
    failed = [r for r in rows if r[0] == "FAIL"]
    print("-" * 64)
    print("L0 静态自检：%d OK / %d SKIP / %d FAIL" % (
        sum(1 for r in rows if r[0] == "OK"),
        sum(1 for r in rows if r[0] == "SKIP"), len(failed)))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
