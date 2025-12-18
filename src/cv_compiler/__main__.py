"""
Module entrypoint for `python -m cv_compiler`.

Delegates directly to the CLI (`cv_compiler.cli.main`).
"""

from __future__ import annotations

from .cli import main

raise SystemExit(main())
