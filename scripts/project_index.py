"""
Generate a navigable project index (local import graph + per-file summary).

Deterministic, stdlib-only. Also backfills missing module docstrings in local Python files.
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
}


DOCSTRING_HINTS: dict[str, str] = {
    "src/cv_compiler/cli.py": "CLI argument parsing and command dispatch.",
    "src/cv_compiler/pipeline.py": "Build pipeline request/response types and entrypoint.",
    "src/cv_compiler/explain.py": "Formatting helpers for selection explanations.",
    "src/cv_compiler/types.py": "Shared enums and lint issue types.",
    "src/cv_compiler/schema/models.py": "Dataclasses representing validated CV entities.",
    "src/cv_compiler/parse/frontmatter.py": "Frontmatter parsing for Markdown sources.",
    "src/cv_compiler/parse/loaders.py": "Load canonical data and job specs from disk.",
    "src/cv_compiler/select/selector.py": "Deterministic selection interface.",
    "src/cv_compiler/select/types.py": "Selection result and decision types.",
    "src/cv_compiler/render/renderer.py": "Rendering interface for CV output.",
    "src/cv_compiler/render/types.py": "Rendering request/response types.",
    "src/cv_compiler/lint/linter.py": "Lint interfaces for inputs and outputs.",
    "src/cv_compiler/llm/base.py": "Optional LLM provider protocol and request types.",
}


@dataclass(frozen=True, slots=True)
class PythonModuleInfo:
    path: Path
    module: str
    doc: str | None
    defined: tuple[str, ...]
    imported_modules: tuple[str, ...]
    local_imports: tuple[str, ...]
    external_import_roots: tuple[str, ...]


def _iter_files(root: Path) -> list[Path]:
    files: list[Path] = []
    for path in root.rglob("*"):
        if any(part in EXCLUDED_DIR_NAMES for part in path.parts):
            continue
        if path.is_file():
            files.append(path)
    return sorted(files)


def _module_name_for_path(path: Path) -> str | None:
    try:
        rel = path.relative_to(Path.cwd())
    except ValueError:
        return None

    if rel.parts[:1] == ("src",) and rel.suffix == ".py":
        parts = list(rel.parts[1:])
        if parts[-1] == "__init__.py":
            parts = parts[:-1]
        else:
            parts[-1] = parts[-1].removesuffix(".py")
        return ".".join(parts)

    if rel.parts[:1] == ("tests",) and rel.suffix == ".py":
        return f"tests.{rel.stem}"

    if rel.parts[:1] == ("scripts",) and rel.suffix == ".py":
        return f"scripts.{rel.stem}"

    return None


def _is_package_file(path: Path) -> bool:
    return path.name == "__init__.py"


def _resolve_relative_module(
    current_module: str, *, level: int, module: str | None, is_package: bool
) -> str:
    package_parts = current_module.split(".") if is_package else current_module.split(".")[:-1]
    up = max(level - 1, 0)
    base = package_parts[:-up] if up else package_parts
    if module:
        base = [*base, *module.split(".")]
    return ".".join(base)


def _extract_imports(tree: ast.AST, *, current_module: str, is_package: bool) -> list[str]:
    imports: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            if node.level and node.level > 0:
                base = _resolve_relative_module(
                    current_module, level=node.level, module=node.module, is_package=is_package
                )
            else:
                base = node.module or ""

            if base:
                imports.append(base)

            for alias in node.names:
                if not base:
                    continue
                imports.append(f"{base}.{alias.name}")

    return imports


def _defined_symbols(tree: ast.AST) -> tuple[str, ...]:
    defined: list[str] = []
    for node in tree.body if isinstance(tree, ast.Module) else []:  # type: ignore[attr-defined]
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            defined.append(node.name)
    return tuple(sorted(defined))


def _ensure_module_docstring(path: Path, *, module_name: str, fallback: str) -> str:
    text = path.read_text(encoding="utf-8")
    tree = ast.parse(text)
    existing = ast.get_docstring(tree)
    if existing:
        return existing.strip()

    rel = path.relative_to(Path.cwd()).as_posix()
    summary = DOCSTRING_HINTS.get(rel) or fallback
    doc = f'"""{summary}"""\n\n'

    lines = text.splitlines(keepends=True)
    insert_at = 0

    if lines and lines[0].startswith("#!"):
        insert_at = 1
    if len(lines) > insert_at and "coding" in lines[insert_at]:
        insert_at += 1

    new_text = "".join(lines[:insert_at]) + doc + "".join(lines[insert_at:])
    path.write_text(new_text, encoding="utf-8")
    return summary


def _build_module_info(
    py_path: Path, module_name: str, local_modules: dict[str, Path]
) -> PythonModuleInfo:
    text = py_path.read_text(encoding="utf-8")
    tree = ast.parse(text)
    doc = ast.get_docstring(tree)
    defined = _defined_symbols(tree)

    imported = _extract_imports(
        tree, current_module=module_name, is_package=_is_package_file(py_path)
    )
    imported_modules = sorted(set(imported))

    local_imports: set[str] = set()
    external_roots: set[str] = set()
    for mod in imported_modules:
        if mod in local_modules:
            local_imports.add(mod)
            continue

        # If importing a symbol from a local module (e.g., `cv_compiler.schema.models.Profile`),
        # count the base module as the dependency.
        parts = mod.split(".")
        for i in range(len(parts), 0, -1):
            prefix = ".".join(parts[:i])
            if prefix in local_modules:
                local_imports.add(prefix)
                break
        else:
            if parts[0] != "__future__":
                external_roots.add(parts[0])

    return PythonModuleInfo(
        path=py_path,
        module=module_name,
        doc=doc.strip() if doc else None,
        defined=defined,
        imported_modules=tuple(imported_modules),
        local_imports=tuple(sorted(local_imports)),
        external_import_roots=tuple(sorted(external_roots)),
    )


def _render_markdown_index(
    *,
    python_modules: list[PythonModuleInfo],
    local_modules: dict[str, Path],
    reverse_edges: dict[str, list[str]],
    other_files: list[Path],
) -> str:
    lines: list[str] = []
    lines.append("# Project Index")
    lines.append("")
    lines.append("Deterministic index of files + local import connections (includes tests).")
    lines.append("")
    lines.append("## Overview")
    lines.append("")
    lines.append(f"- Python modules indexed: {len(python_modules)}")
    lines.append(f"- Other files indexed: {len(other_files)}")
    lines.append("")

    lines.append("## Python Modules")
    lines.append("")
    for info in sorted(python_modules, key=lambda m: m.path.as_posix()):
        rel = info.path.relative_to(Path.cwd()).as_posix()
        lines.append(f"### `{rel}`")
        lines.append("")
        lines.append(f"- Module: `{info.module}`")
        lines.append(f"- Doc: {info.doc.splitlines()[0] if info.doc else '(none)'}")
        lines.append(
            f"- Defines: {', '.join(f'`{d}`' for d in info.defined) if info.defined else '(none)'}"
        )

        if info.local_imports:
            rendered = ", ".join(
                f"`{m}` → `{local_modules[m].relative_to(Path.cwd()).as_posix()}`"
                for m in info.local_imports
            )
            lines.append(f"- Imports (local): {rendered}")
        else:
            lines.append("- Imports (local): (none)")

        imported_by = sorted(reverse_edges.get(info.module, []))
        if imported_by:
            rendered = ", ".join(f"`{m}`" for m in imported_by)
            lines.append(f"- Imported by (local): {rendered}")
        else:
            lines.append("- Imported by (local): (none)")

        if info.external_import_roots:
            external = ", ".join(f"`{r}`" for r in info.external_import_roots)
            lines.append(f"- External import roots: {external}")
        else:
            lines.append("- External import roots: (none)")
        lines.append("")

    lines.append("## Other Files")
    lines.append("")
    for path in other_files:
        rel = path.relative_to(Path.cwd()).as_posix()
        lines.append(f"- `{rel}`")
    lines.append("")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="project_index")
    parser.add_argument(
        "--write-docstrings",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Backfill missing module docstrings in local Python files.",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("docs/PROJECT_INDEX.md"),
        help="Output markdown path.",
    )
    args = parser.parse_args(argv)

    root = Path.cwd()
    files = _iter_files(root)

    python_files = [p for p in files if p.suffix == ".py"]
    other_files = [
        p for p in files if p.suffix != ".py" and not any(part in {"tmp"} for part in p.parts)
    ]

    local_modules: dict[str, Path] = {}
    for py in python_files:
        mod = _module_name_for_path(py)
        if mod:
            local_modules[mod] = py

    module_infos: list[PythonModuleInfo] = []
    for mod, py in sorted(local_modules.items(), key=lambda kv: kv[1].as_posix()):
        if args.write_docstrings:
            fallback = f"Module {mod}."
            _ensure_module_docstring(py, module_name=mod, fallback=fallback)
        module_infos.append(_build_module_info(py, mod, local_modules))

    reverse_edges: dict[str, list[str]] = defaultdict(list)
    for info in module_infos:
        for dep in info.local_imports:
            reverse_edges[dep].append(info.module)

    out_path: Path = args.out
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(
        _render_markdown_index(
            python_modules=module_infos,
            local_modules=local_modules,
            reverse_edges=reverse_edges,
            other_files=sorted(other_files),
        ),
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
