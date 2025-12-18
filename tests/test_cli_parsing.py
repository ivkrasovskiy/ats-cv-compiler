from __future__ import annotations

import unittest

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
        with self.assertRaises(SystemExit):
            parser.parse_args(["build", "--data", "data", "--example", "basic"])
