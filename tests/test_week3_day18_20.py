import json
import unittest
from unittest.mock import patch

from click.testing import CliRunner

from sentinelai.approval import ApprovalError, request_approval
from sentinelai.cli import main


class WeekThreeWorkflowTests(unittest.TestCase):
    def setUp(self):
        self.runner = CliRunner()

    def test_logs_sample_json_contains_analysis(self):
        result = self.runner.invoke(main, ["logs", "--sample", "--analyze", "--json"])

        self.assertEqual(result.exit_code, 0, result.output)
        payload = json.loads(result.output)
        self.assertEqual(payload["log_metadata"]["source"], "sample")
        self.assertEqual(len(payload["events"]), 3)
        self.assertEqual(payload["analysis"]["threat_level"], "LOW")
        self.assertEqual(payload["llm_analysis"]["status"], "mock")

    def test_logs_sample_filters_event_ids(self):
        result = self.runner.invoke(main, ["logs", "--sample", "--event-ids", "4625", "--json"])

        self.assertEqual(result.exit_code, 0, result.output)
        payload = json.loads(result.output)
        self.assertEqual([event["event_id"] for event in payload["events"]], [4625])

    def test_scan_confirmation_denies_before_scanner_runs(self):
        with patch("sentinelai.cli.request_approval", return_value=False), patch(
            "sentinelai.cli.NmapScanner"
        ) as scanner:
            result = self.runner.invoke(main, ["scan", "--target", "127.0.0.1", "--confirm"])

        self.assertEqual(result.exit_code, 0, result.output)
        self.assertIn("cancelled", result.output.lower())
        scanner.assert_not_called()

    def test_approval_validates_and_supports_explicit_noninteractive_consent(self):
        with self.assertRaises(ApprovalError):
            request_approval("scan", "")
        self.assertTrue(request_approval("scan", "127.0.0.1", assume_yes=True))


if __name__ == "__main__":
    unittest.main()