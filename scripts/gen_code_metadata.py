"""Generate docs/code_metadata.md — per-file metrics for every source file.

Python: line count, McCabe cyclomatic complexity, max indent depth, local imports, imported-by.
TypeScript/TSX: line count, max brace nesting depth, local import paths.
Files over 500 lines are flagged as refactor candidates.

Usage:
    uv run python scripts/gen_code_metadata.py          # writes docs/code_metadata.md
    uv run python scripts/gen_code_metadata.py --quiet  # suppress output
"""

from __future__ import annotations

import argparse
import ast
import re
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path

# ── Configuration ─────────────────────────────────────────────────────────────

# Directories to scan for Python source
PYTHON_DIRS = [
    "src",
    "app/backend",
    "scripts",
    "tests",
]

# Directories to scan for TypeScript/TSX source
TS_DIRS = [
    "app/frontend/src",
]

# Directories whose names are always skipped (anywhere in the tree)
SKIP_DIR_NAMES = {
    ".git", ".venv", "node_modules", "__pycache__", ".pytest_cache",
    ".ruff_cache", ".uv-cache", ".uv_cache", "dist", "build", ".vite",
    "out", "tmp", "logs", "playwright-report", "test-results",
}

LINE_LIMIT = 500

# ── Data model ────────────────────────────────────────────────────────────────


@dataclass
class FileMetrics:
    path: Path
    rel: str
    language: str
    lines: int
    complexity: int | None  # McCabe (Python only)
    max_depth: int
    local_imports: list[str]
    imported_by: list[str] = field(default_factory=list)

    @property
    def over_limit(self) -> bool:
        return self.lines > LINE_LIMIT


def _iter_source_files(dirs: list[str], suffixes: set[str], root: Path) -> list[Path]:
    results: list[Path] = []
    for d in dirs:
        base = root / d
        if not base.exists():
            continue
        for path in sorted(base.rglob("*")):
            if any(part in SKIP_DIR_NAMES for part in path.parts):
                continue
            if path.is_file() and path.suffix in suffixes:
                results.append(path)
    return results


def _count_lines(source: str) -> int:
    return len(source.splitlines())


# ── Python analysis ───────────────────────────────────────────────────────────


def _python_cyclomatic(tree: ast.AST) -> int:
    """File-level McCabe cyclomatic complexity (starts at 1)."""
    complexity = 1
    for node in ast.walk(tree):
        if isinstance(
            node,
            (
                ast.If,
                ast.While,
                ast.For,
                ast.AsyncFor,
                ast.ExceptHandler,
                ast.With,
                ast.AsyncWith,
                ast.Assert,
                ast.comprehension,
            ),
        ):
            complexity += 1
        elif isinstance(node, ast.BoolOp):
            # `and`/`or` with N operands adds N-1 branches
            complexity += len(node.values) - 1
    return complexity


def _python_max_indent(source: str) -> int:
    """Max indent depth (4 spaces = 1 level)."""
    max_depth = 0
    for line in source.splitlines():
        stripped = line.lstrip()
        if not stripped or stripped.startswith("#"):
            continue
        indent = len(line) - len(stripped)
        max_depth = max(max_depth, indent // 4)
    return max_depth


def _python_local_imports(
    tree: ast.AST, *, module_name: str, is_package: bool, local_module_names: set[str]
) -> list[str]:
    raw: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            raw.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            if node.level and node.level > 0:
                # relative import
                pkg = module_name.split(".") if is_package else module_name.split(".")[:-1]
                up = max(node.level - 1, 0)
                base_parts = pkg[:-up] if up else pkg
                base = ".".join([*base_parts, *(node.module.split(".") if node.module else [])])
            else:
                base = node.module or ""
            if base:
                raw.append(base)
                for alias in node.names:
                    raw.append(f"{base}.{alias.name}")

    local: set[str] = set()
    for mod in raw:
        if mod in local_module_names:
            local.add(mod)
            continue
        # walk up: cv_compiler.schema.models → cv_compiler.schema → cv_compiler
        parts = mod.split(".")
        for i in range(len(parts), 0, -1):
            prefix = ".".join(parts[:i])
            if prefix in local_module_names:
                local.add(prefix)
                break
    return sorted(local)


def _python_module_name(path: Path, root: Path) -> str | None:
    try:
        rel = path.relative_to(root)
    except ValueError:
        return None
    parts = list(rel.parts)
    if parts[-1] == "__init__.py":
        parts = parts[:-1]
    else:
        parts[-1] = parts[-1].removesuffix(".py")
    # Strip leading 'src' segment
    if parts and parts[0] == "src":
        parts = parts[1:]
    return ".".join(parts) if parts else None


def _analyze_python(path: Path, root: Path, local_module_names: set[str]) -> FileMetrics:
    source = path.read_text(encoding="utf-8", errors="replace")
    lines = _count_lines(source)
    rel = path.relative_to(root).as_posix()

    try:
        tree = ast.parse(source, filename=str(path))
        complexity = _python_cyclomatic(tree)
        max_depth = _python_max_indent(source)
        module_name = _python_module_name(path, root) or rel
        is_package = path.name == "__init__.py"
        local_imports = _python_local_imports(
            tree,
            module_name=module_name,
            is_package=is_package,
            local_module_names=local_module_names,
        )
    except SyntaxError:
        complexity = None
        max_depth = 0
        local_imports = []

    return FileMetrics(
        path=path,
        rel=rel,
        language="python",
        lines=lines,
        complexity=complexity,
        max_depth=max_depth,
        local_imports=local_imports,
    )


# ── TypeScript analysis ──────────────────────────────────────────────────────

_TS_IMPORT_RE = re.compile(
    r"""import\s+(?:type\s+)?(?:\{[^}]*\}|[\w*]+|\*\s+as\s+\w+)(?:\s*,\s*(?:\{[^}]*\}|[\w*]+))*\s+from\s+['"]([^'"]+)['"]""",
    re.DOTALL,
)
_TS_SIDE_EFFECT_RE = re.compile(r"""import\s+['"]([^'"]+)['"]""")


def _ts_local_imports(source: str) -> list[str]:
    found: set[str] = set()
    for m in _TS_IMPORT_RE.finditer(source):
        p = m.group(1)
        if p.startswith(".") or p.startswith("@/"):
            found.add(p)
    for m in _TS_SIDE_EFFECT_RE.finditer(source):
        p = m.group(1)
        if p.startswith(".") or p.startswith("@/"):
            found.add(p)
    return sorted(found)


def _ts_max_nesting(source: str) -> int:
    """Max brace depth, skipping string/template literals."""
    depth = 0
    max_depth = 0
    in_single = False
    in_double = False
    in_template = 0  # template nesting depth
    i = 0
    n = len(source)
    while i < n:
        c = source[i]
        if in_single:
            if c == "\\" and i + 1 < n:
                i += 2
                continue
            if c == "'":
                in_single = False
        elif in_double:
            if c == "\\" and i + 1 < n:
                i += 2
                continue
            if c == '"':
                in_double = False
        elif in_template > 0:
            if c == "\\" and i + 1 < n:
                i += 2
                continue
            if c == "`":
                in_template -= 1
            elif c == "{" and i > 0 and source[i - 1] == "$":
                depth += 1
                max_depth = max(max_depth, depth)
        else:
            if c == "'":
                in_single = True
            elif c == '"':
                in_double = True
            elif c == "`":
                in_template += 1
            elif c == "{":
                depth += 1
                max_depth = max(max_depth, depth)
            elif c == "}":
                depth = max(depth - 1, 0)
        i += 1
    return max_depth


def _analyze_typescript(path: Path, root: Path) -> FileMetrics:
    source = path.read_text(encoding="utf-8", errors="replace")
    return FileMetrics(
        path=path,
        rel=path.relative_to(root).as_posix(),
        language="typescript",
        lines=_count_lines(source),
        complexity=None,
        max_depth=_ts_max_nesting(source),
        local_imports=_ts_local_imports(source),
    )


# ── Import graph (imported-by) ───────────────────────────────────────────────


def _build_imported_by(metrics: list[FileMetrics]) -> None:
    # Python: build module→file map
    py_module_to_rel: dict[str, str] = {}
    for m in metrics:
        if m.language == "python":
            module = _python_module_name(m.path, m.path.parents[len(m.path.parts) - 2]) or m.rel
            # Use a simpler key: the rel path itself also works as ID
            py_module_to_rel[module] = m.rel

    # Build reverse: rel → list[rel of importers]
    imported_by: dict[str, list[str]] = defaultdict(list)

    for m in metrics:
        if m.language == "python":
            for dep_mod in m.local_imports:
                dep_rel = py_module_to_rel.get(dep_mod)
                if dep_rel:
                    imported_by[dep_rel].append(m.rel)
        else:
            # TypeScript: resolve relative import paths
            file_dir = m.path.parent
            for imp in m.local_imports:
                # Try to resolve relative path
                candidate = (file_dir / imp).resolve()
                for suffix in ("", ".ts", ".tsx", ".js"):
                    c = Path(str(candidate) + suffix)
                    try:
                        rel = c.relative_to(m.path.parents[len(m.path.parts) - 2]).as_posix()
                        imported_by[rel].append(m.rel)
                        break
                    except ValueError:
                        pass

    for m in metrics:
        m.imported_by = sorted(set(imported_by.get(m.rel, [])))


# ── Rendering ────────────────────────────────────────────────────────────────

_COMPLEXITY_LABEL = {
    range(0, 11): "low",
    range(11, 21): "moderate",
    range(21, 51): "high",
    range(51, 10000): "very high",
}


def _complexity_label(c: int) -> str:
    for r, label in _COMPLEXITY_LABEL.items():
        if c in r:
            return label
    return "very high"


def _render(metrics: list[FileMetrics]) -> str:
    now = datetime.now(UTC).strftime("%Y-%m-%d %H:%M UTC")
    py = [m for m in metrics if m.language == "python"]
    ts = [m for m in metrics if m.language == "typescript"]
    over = [m for m in metrics if m.over_limit]

    lines: list[str] = []
    lines += [
        "# Code Metadata",
        "",
        f"> Auto-generated by `scripts/gen_code_metadata.py` — do not edit manually.",
        f"> Last updated: {now}",
        ">",
        "> **For agents**: Before editing a file, check its **Imported by** list — those files",
        "> may need updating too. Files marked ⚠️ are over 500 lines and should be split.",
        "",
        "## Summary",
        "",
        f"| | Count |",
        f"|---|---|",
        f"| Python files | {len(py)} |",
        f"| TypeScript files | {len(ts)} |",
        f"| ⚠️ Files over {LINE_LIMIT} lines | {len(over)} |",
        "",
    ]

    if over:
        lines += [
            f"## ⚠️ Refactor Candidates (> {LINE_LIMIT} lines)",
            "",
            "| File | Lines | Language |",
            "|---|---|---|",
        ]
        for m in sorted(over, key=lambda x: -x.lines):
            lines.append(f"| `{m.rel}` | **{m.lines}** | {m.language} |")
        lines.append("")

    # ── Python ──
    lines += ["## Python Files", ""]
    for m in sorted(py, key=lambda x: x.rel):
        size_flag = " ⚠️" if m.over_limit else ""
        lines.append(f"### `{m.rel}`")
        lines.append("")
        lines.append(f"- **Lines**: {m.lines}{size_flag}")
        if m.complexity is not None:
            label = _complexity_label(m.complexity)
            lines.append(f"- **Complexity** (McCabe): {m.complexity} ({label})")
        lines.append(f"- **Max indent depth**: {m.max_depth}")
        if m.local_imports:
            lines.append(f"- **Imports (local)**: {', '.join(f'`{i}`' for i in m.local_imports)}")
        else:
            lines.append("- **Imports (local)**: none")
        if m.imported_by:
            lines.append(f"- **Imported by**: {', '.join(f'`{i}`' for i in m.imported_by)}")
        else:
            lines.append("- **Imported by**: none")
        lines.append("")

    # ── TypeScript ──
    lines += ["## TypeScript / TSX Files", ""]
    for m in sorted(ts, key=lambda x: x.rel):
        size_flag = " ⚠️" if m.over_limit else ""
        lines.append(f"### `{m.rel}`")
        lines.append("")
        lines.append(f"- **Lines**: {m.lines}{size_flag}")
        lines.append(f"- **Max brace nesting**: {m.max_depth}")
        if m.local_imports:
            lines.append(f"- **Imports (local)**: {', '.join(f'`{i}`' for i in m.local_imports)}")
        else:
            lines.append("- **Imports (local)**: none")
        if m.imported_by:
            lines.append(f"- **Imported by**: {', '.join(f'`{i}`' for i in m.imported_by)}")
        else:
            lines.append("- **Imported by**: none")
        lines.append("")

    return "\n".join(lines)


# ── Main ─────────────────────────────────────────────────────────────────────


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate docs/code_metadata.md")
    parser.add_argument("--out", type=Path, default=Path("docs/code_metadata.md"))
    parser.add_argument("--quiet", action="store_true", help="Suppress file-by-file output")
    args = parser.parse_args(argv)

    root = Path.cwd()

    py_paths = _iter_source_files(PYTHON_DIRS, {".py"}, root)
    ts_paths = _iter_source_files(TS_DIRS, {".ts", ".tsx"}, root)

    if not args.quiet:
        print(f"[i] Scanning {len(py_paths)} Python + {len(ts_paths)} TypeScript files...")

    # Build set of all local Python module names for import resolution
    local_module_names: set[str] = set()
    for p in py_paths:
        mod = _python_module_name(p, root)
        if mod:
            local_module_names.add(mod)

    metrics: list[FileMetrics] = []

    for p in py_paths:
        m = _analyze_python(p, root, local_module_names)
        metrics.append(m)

    for p in ts_paths:
        m = _analyze_typescript(p, root)
        metrics.append(m)

    _build_imported_by(metrics)

    # Report warnings
    over = [m for m in metrics if m.over_limit]
    if over and not args.quiet:
        print(f"[⚠] {len(over)} file(s) over {LINE_LIMIT} lines:", file=sys.stderr)
        for m in sorted(over, key=lambda x: -x.lines):
            print(f"    {m.lines:5d}  {m.rel}", file=sys.stderr)

    out: Path = args.out
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(_render(metrics), encoding="utf-8")

    if not args.quiet:
        print(f"[✓] {out} updated ({len(metrics)} files analyzed)")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
