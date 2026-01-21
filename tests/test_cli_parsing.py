"""
Tests for CLI argument parsing.

These checks lock down flag behavior and basic parsing constraints without depending on the
pipeline implementation.
"""

from __future__ import annotations

import io
import unittest
from contextlib import redirect_stderr

from cv_compiler.cli import _build_parser


class TestCliParsing(unittest.TestCase):
    def test_build_accepts_example_flag(self) -> None:
        parser = _build_parser()
        args = parser.parse_args(["build", "--example", "basic"])
        self.assertEqual(args.example, "basic")

    def test_build_accepts_data_flag(self) -> None:
        parser = _build_parser()
        args = parser.parse_args(["build", "--data", "data"])
        self.assertEqual(args.data, "data")

    def test_build_data_and_example_are_mutually_exclusive(self) -> None:
        parser = _build_parser()
        with redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit):
                parser.parse_args(["build", "--data", "data", "--example", "basic"])

    def test_build_accepts_no_pdf_flag(self) -> None:
        parser = _build_parser()
        args = parser.parse_args(["build", "--no-pdf"])
        self.assertTrue(args.no_pdf)

    def test_build_accepts_from_markdown_flag(self) -> None:
        parser = _build_parser()
        args = parser.parse_args(["build", "--from-markdown", "out/cv_generic.md"])
        self.assertEqual(args.from_markdown, "out/cv_generic.md")

    def test_ingest_accepts_pdf_flag(self) -> None:
        parser = _build_parser()
        args = parser.parse_args(["to_mds_from_pdf", "--pdf", "data/cv.pdf"])
        self.assertEqual(args.pdf, "data/cv.pdf")
