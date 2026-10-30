
import json
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EVENTS_DIR = ROOT / ".group" / "events"
CHANGE_ID = "C-d89dcaf2"


def git(*args):
    result = subprocess.run(
        ["git", *args],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace"
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip())
    return result.stdout.strip()


def is_ancestor(older, newer):
    result = subprocess.run(
        ["git", "merge-base", "--is-ancestor",
         older, newer],
        cwd=ROOT
    )
    return result.returncode == 0


def load_events():
    events = []
    for path in EVENTS_DIR.glob("*.json"):
        with open(path, encoding="utf-8") as f:
            events.append(json.load(f))
    return events


class TestCollaborationE2E(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.events = load_events()

        cls.published = next(
            (
                event for event in cls.events
                if event.get("event_type")
                == "change_published"
                and event.get("change_id") == CHANGE_ID
            ),
            None
        )

    def test_publication_exists(self):
        """確認 P-02 的 PUB 事件存在"""
        self.assertIsNotNone(self.published)
        self.assertEqual(
            self.published["person_id"], "P-02"
        )
        self.assertEqual(
            self.published["branch"],
            "people/P-02/demo"
        )

    def test_published_commit_exists(self):
        """確認發布的 Commit 真實存在"""
        self.assertIsNotNone(self.published)

        commit = self.published["commit"]

        self.assertEqual(
            git("cat-file", "-t", commit),
            "commit"
        )

    def test_source_commit_integrated(self):
        """確認 P-02 的修改已進入 main"""
        self.assertIsNotNone(self.published)

        self.assertTrue(
            is_ancestor(
                self.published["commit"],
                "main"
            )
        )

    def test_integration_event_exists(self):
        """確認有對應的整合結果紀錄"""
        matching = [
            e for e in self.events
            if e.get("event_type")
            == "integration_result"
            and e.get("change_id") == CHANGE_ID
        ]

        self.assertGreater(
            len(matching), 0,
            "No integration_result event found."
        )

    def test_integrated_function_exists(self):
        """確認整合後的功能可正常運作"""
        from src.demo import (
            calculate_sum,
            calculate_product
        )

        self.assertEqual(
            calculate_sum(3, 5), 8
        )
        self.assertEqual(
            calculate_product(3, 5), 15
        )


if __name__ == "__main__":
    unittest.main()
