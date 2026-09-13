import contextlib
import io
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from app import run_react_agent
from mcp_server import MCPQCServer
from providers import MockOfflineProvider
from tools import TOOLS_SCHEMA


class MockQCTests(unittest.TestCase):
    def test_configured_scenarios_finish_with_expected_tools(self):
        cases = json.loads((ROOT / "config/test_cases.json").read_text(encoding="utf-8"))
        expected = {
            "TC01": [], "TC02": ["qc_case_query"],
            "TC03": ["create_rework_ticket"],
            "TC04": ["qc_case_query", "create_rework_ticket"],
            "TC05": ["qc_case_query"]
        }
        for case in cases:
            with self.subTest(case=case["id"]), contextlib.redirect_stdout(io.StringIO()):
                logs = run_react_agent(case["question"], MockOfflineProvider(), MCPQCServer())
                actions = [e for e in logs if e["action_type"] == "TOOL_EXECUTION"]
                self.assertEqual([e["tool_name"] for e in actions], expected[case["id"]])
                self.assertEqual(logs[-1]["action_type"], "FINAL_ANSWER")
                self.assertEqual(len(logs), len(actions) + 1)
                for action in actions:
                    self.assertEqual(action["observation"]["status"],
                                     "NOT_FOUND" if case["id"] == "TC05" else "SUCCESS")
                if case["id"] in ("TC03", "TC04"):
                    self.assertIn(actions[-1]["observation"]["rework_id"], logs[-1]["output"])
                if case["id"] == "TC03":
                    self.assertIn("kiểm tra lại nhãn lớp", actions[0]["arguments"]["description"])

    def test_observations_that_must_not_create_rework(self):
        question = "Tra cứu CASE-1001. Nếu QC_FAIL, tạo phiếu Rework."
        observations = [
            {"status": "NOT_FOUND"}, {"status": "EXECUTION_ERROR"},
            {"status": "SUCCESS", "case_id": "CASE-1001", "data": {"status": "QC_PASS"}},
            {"status": "SUCCESS", "case_id": "CASE-1001", "data": {"status": "QC_FAIL"}}
        ]
        for observation in observations:
            with self.subTest(observation=observation):
                prompt = question + "\n\nTool đã gọi: qc_case_query\nArguments: {}\nObservation: " + json.dumps(observation)
                self.assertEqual(MockOfflineProvider().generate_with_tools(prompt, TOOLS_SCHEMA)["type"], "text")

    def test_missing_tool_or_case_does_not_invent_a_call(self):
        provider = MockOfflineProvider()
        self.assertEqual(provider.generate_with_tools("Tra cứu CASE-1001", [])["type"], "text")
        self.assertEqual(provider.generate_with_tools("Tra cứu ca lỗi", TOOLS_SCHEMA)["type"], "text")


if __name__ == "__main__":
    unittest.main()
