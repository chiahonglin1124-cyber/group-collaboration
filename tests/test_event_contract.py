
import json
import unittest
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parents[1]
GROUP_DIR = ROOT / ".group"
EVENTS_DIR = GROUP_DIR / "events"

COMMON_FIELDS = {
    "protocol_version",
    "event_id",
    "event_type",
    "group_id",
    "person_id",
    "created_at",
    "related_events"
}

SUPPORTED_TYPES = {
    "change_published",
    "finding",
    "question",
    "answer",
    "review",
    "test_result",
    "integration_result",
    "blocker",
    "final_candidate",
    "final_result"
}

TYPE_FIELDS = {
    "change_published": {
        "change_id", "branch", "commit", "summary",
        "files_changed", "interface_changes",
        "tests_run", "known_issues",
        "proposed_for_integration"
    },
    "finding": {"summary", "evidence"},
    "question": {"question_id", "text", "blocking"},
    "answer": {"question_id", "text"},
    "review": {
        "change_id", "verdict", "summary",
        "issues", "tests_run"
    },
    "test_result": {
        "scope", "commit", "commands",
        "automated_result", "passed",
        "failed", "skipped",
        "human_checks_required", "summary"
    },
    "integration_result": {
        "change_id", "target_branch",
        "result", "merge_commit", "conflicts",
        "conflict_resolution_summary",
        "verification", "summary"
    },
    "blocker": {
        "summary", "blocking_change_id",
        "requested_action"
    }
}


class TestEventContract(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        with open(
            GROUP_DIR / "group.json",
            encoding="utf-8"
        ) as f:
            cls.group = json.load(f)

        cls.paths = sorted(EVENTS_DIR.glob("*.json"))

    def test_events_exist(self):
        self.assertGreater(
            len(self.paths), 0,
            "No collaboration events found."
        )

    def test_event_format(self):
        seen_ids = set()

        for path in self.paths:
            with self.subTest(file=path.name):

                with open(path, encoding="utf-8") as f:
                    event = json.load(f)

                # Common envelope
                missing = COMMON_FIELDS - event.keys()

                self.assertFalse(
                    missing,
                    f"{path.name}: Missing {sorted(missing)}"
                )

                event_id = event["event_id"]
                event_type = event["event_type"]

                self.assertEqual(
                    path.stem,
                    event_id,
                    "Filename and event_id differ."
                )

                self.assertNotIn(
                    event_id,
                    seen_ids,
                    "Duplicate event ID."
                )
                seen_ids.add(event_id)

                self.assertEqual(
                    event["protocol_version"],
                    self.group["protocol_version"]
                )

                self.assertEqual(
                    event["group_id"],
                    self.group["group_id"]
                )

                self.assertIn(
                    event_type,
                    SUPPORTED_TYPES
                )

                self.assertIsInstance(
                    event["related_events"],
                    list
                )

                # Timestamp validation
                timestamp = event["created_at"]
                parsed = datetime.fromisoformat(
                    timestamp.replace("Z", "+00:00")
                )
                self.assertIsNotNone(parsed.tzinfo)

                # Event-specific required fields
                required = TYPE_FIELDS.get(
                    event_type, set()
                )

                missing = required - event.keys()

                self.assertFalse(
                    missing,
                    f"{event_type}: Missing {sorted(missing)}"
                )

                # Allowed review verdicts
                if event_type == "review":
                    self.assertIn(
                        event["verdict"],
                        {
                            "accept",
                            "accept_with_changes",
                            "reject",
                            "needs_more_evidence"
                        }
                    )

                # Allowed test results
                if event_type == "test_result":
                    self.assertIn(
                        event["automated_result"],
                        {
                            "pass", "fail",
                            "partial", "not_available"
                        }
                    )

                # Allowed integration outcomes
                if event_type == "integration_result":
                    self.assertIn(
                        event["result"],
                        {
                            "success",
                            "failed",
                            "needs_human"
                        }
                    )

                    verification = event["verification"]

                    self.assertIsInstance(
                        verification, dict
                    )

                    for key in (
                        "build",
                        "tests",
                        "semantic_review"
                    ):
                        self.assertIn(key, verification)

    def test_event_references(self):
        ids = set()

        for path in self.paths:
            with open(path, encoding="utf-8") as f:
                event = json.load(f)
                ids.add(event["event_id"])

        for path in self.paths:
            with open(path, encoding="utf-8") as f:
                event = json.load(f)

            for related in event["related_events"]:
                with self.subTest(
                    file=path.name,
                    related=related
                ):
                    self.assertIn(
                        related,
                        ids,
                        "Related event not found locally."
                    )


if __name__ == "__main__":
    unittest.main()
