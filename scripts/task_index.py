"""
Generate a per-file task index as a temporary working checklist.

Deterministic, stdlib-only. Detects signature-only stubs and turns them into per-file tasks.
"""

from __future__ import annotations

import argparse
import ast
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

EXCLUDED_DIR_NAMES = {
    ".git",
    ".venv",
    ".uv-cache",
    ".ruff_cache",
    ".pytest_cache",
    "__pycache__",
    "out",
    "dist",
    "build",
    "tmp",
}


@dataclass(frozen=True, slots=True)
class Stub:
    qualname: str
    lineno: int


def _iter_python_files(root: Path) -> list[Path]:
    files: list[Path] = []
    for path in root.rglob("*.py"):
        if any(part in EXCLUDED_DIR_NAMES for part in path.parts):
            continue
        files.append(path)
    return sorted(files)


def _module_name_for_path(path: Path) -> str | None:
    rel = path.relative_to(Path.cwd())
    if rel.parts[:1] == ("src",):
        parts = list(rel.parts[1:])
        if parts[-1] == "__init__.py":
            parts = parts[:-1]
        else:
            parts[-1] = parts[-1].removesuffix(".py")
        return ".".join(parts)
    if rel.parts[:1] == ("tests",):
        return f"tests.{rel.stem}"
    if rel.parts[:1] == ("scripts",):
        return f"scripts.{rel.stem}"
    return None


def _is_not_implemented_raise(stmt: ast.stmt) -> bool:
    if not isinstance(stmt, ast.Raise):
        return False
    exc = stmt.exc
    if exc is None:
        return False
    if isinstance(exc, ast.Name):
        return exc.id == "NotImplementedError"
    if isinstance(exc, ast.Call) and isinstance(exc.func, ast.Name):
        return exc.func.id == "NotImplementedError"
    return False


def _is_stub_body(stmts: list[ast.stmt]) -> bool:
    remaining = list(stmts)
    if (
        remaining
        and isinstance(remaining[0], ast.Expr)
        and isinstance(remaining[0].value, ast.Constant)
    ):
        if isinstance(remaining[0].value.value, str):
            remaining = remaining[1:]

    if not remaining:
        return True
    if len(remaining) == 1 and isinstance(remaining[0], ast.Pass):
        return True
    if len(remaining) == 1 and _is_not_implemented_raise(remaining[0]):
        return True
    if (
        len(remaining) == 1
        and isinstance(remaining[0], ast.Expr)
        and isinstance(remaining[0].value, ast.Constant)
    ):
        return remaining[0].value.value is Ellipsis
    return False


def _find_stubs(tree: ast.AST) -> tuple[Stub, ...]:
    stubs: list[Stub] = []
    if not isinstance(tree, ast.Module):
        return ()

    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and _is_stub_body(node.body):
            stubs.append(Stub(qualname=node.name, lineno=node.lineno))
        elif isinstance(node, ast.ClassDef):
            for child in node.body:
                if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)) and _is_stub_body(
                    child.body
                ):
                    stubs.append(Stub(qualname=f"{node.name}.{child.name}", lineno=child.lineno))

    return tuple(sorted(stubs, key=lambda s: (s.qualname, s.lineno)))


def _extract_local_import_edges(
    path: Path, *, module_name: str, local_modules: set[str]
) -> tuple[str, ...]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    imports: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            base = node.module or ""
            if base:
                imports.add(base)
            for alias in node.names:
                if base:
                    imports.add(f"{base}.{alias.name}")

    edges: set[str] = set()
    for mod in imports:
        if mod in local_modules:
            edges.add(mod)
            continue
        parts = mod.split(".")
        for i in range(len(parts), 0, -1):
            prefix = ".".join(parts[:i])
            if prefix in local_modules:
                edges.add(prefix)
                break

    edges.discard(module_name)
    return tuple(sorted(edges))


def _render_task_index(
    *,
    goal: str | None,
    modules: dict[str, Path],
    doc_by_module: dict[str, str | None],
    stubs_by_module: dict[str, tuple[Stub, ...]],
    deps: dict[str, tuple[str, ...]],
    reverse_deps: dict[str, tuple[str, ...]],
) -> str:
    lines: list[str] = []
    lines.append("# Task Index (Temporary)")
    lines.append("")
    if goal:
        lines.append(f"Goal: {goal}")
        lines.append("")
    lines.append("This file is generated; edit freely while working, then clear it when done.")
    lines.append("")

    lines.append("## Suggested Order (Dependency-Aware)")
    lines.append("")
    ordered = _topo_order(modules, deps)
    for mod in ordered:
        rel = modules[mod].relative_to(Path.cwd()).as_posix()
        stub_count = len(stubs_by_module.get(mod, ()))
        lines.append(f"- `{rel}` ({stub_count} stubs)")
    lines.append("")

    lines.append("## Per-File Tasks")
    lines.append("")
    for mod in ordered:
        path = modules[mod]
        rel = path.relative_to(Path.cwd()).as_posix()
        lines.append(f"### `{rel}`")
        lines.append("")
        local_deps = deps.get(mod, ())
        imported_by = reverse_deps.get(mod, ())
        doc = doc_by_module.get(mod)
        lines.append(f"- Module: `{mod}`")
        lines.append(f"- Doc: {doc.splitlines()[0] if doc else '(none)'}")
        lines.append(
            f"- Depends on: {', '.join(f'`{d}`' for d in local_deps) if local_deps else '(none)'}"
        )
        imported_by_text = ", ".join(f"`{d}`" for d in imported_by) if imported_by else "(none)"
        lines.append(f"- Imported by: {imported_by_text}")
        stubs = stubs_by_module.get(mod, ())
        if stubs:
            lines.append("- Tasks:")
            for stub in stubs:
                lines.append(f"  - Implement `{stub.qualname}` (`{rel}:{stub.lineno}`)")
            lines.append("  - Add/adjust tests for the implemented behavior")
        else:
            lines.append("- Tasks: (none detected)")
        lines.append("")
    return "\n".join(lines)


def _topo_order(modules: dict[str, Path], deps: dict[str, tuple[str, ...]]) -> list[str]:
    """
    Produce a stable topological order using local import edges.

    If cycles exist, remaining nodes are appended in a stable path-sorted order.
    """
    all_nodes = set(modules.keys())
    incoming_count: dict[str, int] = {n: 0 for n in all_nodes}
    outgoing: dict[str, set[str]] = {n: set() for n in all_nodes}

    for node, node_deps in deps.items():
        for dep in node_deps:
            if dep not in all_nodes or node not in all_nodes:
                continue
            incoming_count[node] += 1
            outgoing[dep].add(node)

    ready = sorted(
        [n for n, c in incoming_count.items() if c == 0],
        key=lambda m: modules[m].as_posix(),
    )
    order: list[str] = []
    while ready:
        node = ready.pop(0)
        order.append(node)
        for nxt in sorted(outgoing[node], key=lambda m: modules[m].as_posix()):
            incoming_count[nxt] -= 1
            if incoming_count[nxt] == 0:
                ready.append(nxt)

    remaining = sorted((all_nodes - set(order)), key=lambda m: modules[m].as_posix())
    order.extend(remaining)
    return order


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="task_index")
    parser.add_argument(
        "--goal", type=str, default=None, help="Optional goal statement to include at top."
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("tmp/task_index.md"),
        help="Output path (recommended under tmp/).",
    )
    parser.add_argument(
        "--clear",
        action="store_true",
        help="Overwrite the task index with a short 'done' marker.",
    )
    args = parser.parse_args(argv)

    out_path: Path = args.out
    out_path.parent.mkdir(parents=True, exist_ok=True)
    if args.clear:
        out_path.write_text("# Task Index (Temporary)\n\nCleared.\n", encoding="utf-8")
        return 0

    root = Path.cwd()
    python_files = _iter_python_files(root)
    modules: dict[str, Path] = {}
    for path in python_files:
        mod = _module_name_for_path(path)
        if mod:
            modules[mod] = path

    local_module_names = set(modules.keys())

    doc_by_module: dict[str, str | None] = {}
    stubs_by_module: dict[str, tuple[Stub, ...]] = {}
    deps: dict[str, tuple[str, ...]] = {}
    reverse: dict[str, set[str]] = defaultdict(set)

    for mod, path in modules.items():
        tree = ast.parse(path.read_text(encoding="utf-8"))
        doc_by_module[mod] = ast.get_docstring(tree)
        stubs_by_module[mod] = _find_stubs(tree)
        deps[mod] = _extract_local_import_edges(
            path, module_name=mod, local_modules=local_module_names
        )
        for dep in deps[mod]:
            reverse[dep].add(mod)

    reverse_deps: dict[str, tuple[str, ...]] = {k: tuple(sorted(v)) for k, v in reverse.items()}

    out_path.write_text(
        _render_task_index(
            goal=args.goal,
            modules=modules,
            doc_by_module=doc_by_module,
            stubs_by_module=stubs_by_module,
            deps=deps,
            reverse_deps=reverse_deps,
        ),
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
