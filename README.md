# CAD Agent Hub

Windows-focused MCP servers, application bridges, engineering Skills, and reproducible modeling examples for AI-assisted CAD/CAE workflows.

Chinese documentation: [README.zh-CN.md](README.zh-CN.md)

## Included projects

| Path | Purpose |
| --- | --- |
| [`MCP/CATIA`](MCP/CATIA) | CATIA V5 modeling and native Analysis MCP server |
| [`MCP/Solidworks`](MCP/Solidworks) | Stateful SolidWorks modeling MCP server |
| [`MCP/UG`](MCP/UG) | Siemens NX/UG MCP server and in-process bridge |
| [`fusion_electronics_write_bridge`](fusion_electronics_write_bridge) | Local Fusion Electronics write bridge |
| [`skills/ansys-structural-workbench`](skills/ansys-structural-workbench) | Quality-gated ANSYS Workbench structural-analysis Skill |
| [`models`](models) | Reproducible build123d/cadpy model source examples |
| [`fusion_starship_v3_builder.py`](fusion_starship_v3_builder.py) | Autodesk Fusion parametric modeling example |

Each MCP directory contains its own setup and validation instructions. These integrations require the corresponding proprietary CAD application and must generally run under the same Windows user and integrity level as that application.

## Repository scope

This repository intentionally contains source code, tests, schemas, portable configuration examples, and documentation only. Local workspaces, solver jobs, caches, logs, dependency copies, screenshots, and generated CAD binaries are excluded. Example paths such as `C:\path\to\CAD-Agent-Hub` must be replaced with the local clone path.

## Validation

Run each MCP project's documented unit tests before using it with a live CAD session. A successful COM/API call is not by itself proof that a model, mesh, drawing, or simulation result is correct; inspect the native application state and generated artifacts. For the NX path, see the [layered acceptance checklist](docs/validation.md).

## NX capabilities and validation (v3.2.0, verified 2026-11-09)

This repository is the **daily working path** for a local Siemens NX2007 session.
`Mrxiaoxiaobai/NX_MCP` (fork of `DreamEnding/NX_MCP`) is the **methodology reference**;
its NX2506 Python batch / NX2206 C# GUI bridge is **not** interchangeable with this
`.NET Remoting` bridge. See the [comparison](docs/nx-mcp-comparison.md).

| Area | Claim | Evidence |
| --- | --- | --- |
| Bridge chain (`ping` → Remoting `:48161` → in-process NXOpen) | ✅ Real NX2007 | [Capabilities](CAPABILITIES.md) §1, skill §16 |
| Modeling: block / arc-based cylinders / exact ellipsoids / assemblies / view / colors / save | ✅ Real-machine recipes | [Skill](skills/nx-mcp-bridge-modeling/SKILL.md) §3–§8 |
| Feature editing: chamfer / fillet / cylindrical hole | ✅ Dedicated tools only | [Capabilities](CAPABILITIES.md) §3.2, skill §15 |
| Body move/rotate, in-script blend builder, face-normal top detection | ❌ Verified **unusable** on this binding | [Capabilities](CAPABILITIES.md) §4 |
| Upstream typed `nx_*` tools and `nx_measure_*` proposals | ➖ Not provided | [Comparison](docs/nx-mcp-comparison.md) |
| L0 static self-check (files / copies / versions / template / links / tokens) | ✅ No NX required | `scripts/validate_repo.py`, CI |
| L1 bridge check and L2 real-model acceptance | ⚠️ Local NX2007 only, deliberately excluded from CI | [Validation](docs/validation.md) |

**Default availability, static checks and real-NX acceptance are separate claims.**
A tool returning `ok:true`, a green CI run, or an API existing in `NXOpen.xml` does **not**
certify native CAD behavior. Only the post-change query (body count, feature count,
bounding box) counts as modeling evidence. See the [inspection contract](docs/inspection-contract.md).

```
python scripts/validate_repo.py            # L0, zero third-party dependencies
python -m unittest discover -s tests -v   # same checks via unittest
```

## Documentation

| Guide | What it covers |
| --- | --- |
| [Capabilities](CAPABILITIES.md) | Authoritative verified / unusable capability matrix |
| [NX modeling skill](skills/nx-mcp-bridge-modeling/SKILL.md) | 820+ lines of real-machine NXOpen recipes (v3.2.0) |
| [Architecture](docs/architecture.md) | Process boundaries, object lifecycle, recovery contract |
| [Validation](docs/validation.md) | L0 / L1 / L2 acceptance and evidence boundaries |
| [Inspection contract](docs/inspection-contract.md) | Reliable queries, known-unreliable queries, rejected proposals |
| [NX_MCP comparison](docs/nx-mcp-comparison.md) | What was borrowed from upstream and what was not |
| [Agent conventions](AGENTS.md) | Rules for AI agents and maintainers |
| [Changelog](CHANGELOG.md) · [Contributing](CONTRIBUTING.md) · [Security](SECURITY.md) | Version history, change discipline, trust boundary |

The [Chinese README](README.zh-CN.md) mirrors this page.
