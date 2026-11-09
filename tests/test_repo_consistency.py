# -*- coding: utf-8 -*-
"""L0 静态一致性的 unittest 包装（零第三方依赖，不需要 Siemens NX）。

    python -m unittest discover -s tests -v

这些测试只检查仓库内容自洽，不连接 NX、不证明任何建模行为。
真机验收见 docs/validation.md 的 L1 / L2 层。
"""
import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


class RepoConsistencyTest(unittest.TestCase):
    def test_validate_repo_script_passes(self):
        proc = subprocess.run(
            [sys.executable, str(ROOT / "scripts/validate_repo.py")],
            cwd=str(ROOT), capture_output=True, text=True,
            encoding="utf-8", errors="replace", timeout=120)
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)

    def test_key_documents_exist(self):
        for rel in ("CAPABILITIES.md", "CHANGELOG.md", "AGENTS.md",
                    "docs/architecture.md", "docs/validation.md",
                    "docs/inspection-contract.md", "docs/nx-mcp-comparison.md",
                    "skills/nx-mcp-bridge-modeling/SKILL.md"):
            with self.subTest(rel=rel):
                self.assertTrue((ROOT / rel).is_file(), rel)

    def test_connector_template_is_valid_json(self):
        p = ROOT / "MCP/UG/config/siemens-nx.mcp.json.example"
        cfg = json.loads(p.read_text(encoding="utf-8"))
        self.assertEqual(
            cfg["mcpServers"]["siemens-nx"]["env"]["NX_MCP_TRANSPORT"],
            "remoting")

    def test_skill_is_not_a_stub(self):
        # 纪律：技能只能增补/修正，绝不精简重写。763 行是 v3.1.0 的基线。
        text = (ROOT / "skills/nx-mcp-bridge-modeling/SKILL.md").read_text(encoding="utf-8")
        self.assertGreaterEqual(len(text.splitlines()), 760)
        for keyword in ("CreateArc", "CreateScaleBuilder", "chamfer_edges",
                        "create_cylindrical_hole", "AskBoundingBox", "NewDisplay"):
            with self.subTest(keyword=keyword):
                self.assertIn(keyword, text)


if __name__ == "__main__":
    unittest.main(verbosity=2)
