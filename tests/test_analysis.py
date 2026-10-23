from __future__ import annotations

import unittest
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from codearchaeologist import analyze_repository

SAMPLE_PROJECT = ROOT / "sample_project"


class AnalyzerTests(unittest.TestCase):
    def test_sample_project_extracts_core_symbols(self) -> None:
        report = analyze_repository(SAMPLE_PROJECT)
        function_names = {
            function["qualified_name"]
            for function in report["functions"]
        }
        class_names = {
            class_info["qualified_name"]
            for class_info in report["classes"]
        }

        self.assertIn("CheckoutService.checkout", function_names)
        self.assertIn("calculate_total", function_names)
        self.assertIn("CheckoutService", class_names)
        self.assertGreaterEqual(report["summary"]["call_edges"], 5)

    def test_dead_code_detection_finds_demo_unused_function(self) -> None:
        report = analyze_repository(SAMPLE_PROJECT)
        dead_names = {
            function["qualified_name"]
            for function in report["dead_code"]["functions"]
        }
        self.assertIn("unused_promo_code_normalizer", dead_names)

    def test_json_contains_ai_context(self) -> None:
        report = analyze_repository(SAMPLE_PROJECT)
        self.assertIn("ai_context", report)
        self.assertIn("call_graph", report["ai_context"]["available_sections"])


if __name__ == "__main__":
    unittest.main()
