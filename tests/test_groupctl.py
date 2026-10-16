
import unittest
import json
import tempfile
from pathlib import Path
from unittest.mock import patch

import groupctl


class TestGroupCtl(unittest.TestCase):

    def test_load_group(self):
        """測試是否能讀取小組資料"""

        group = groupctl.load_group()

        self.assertIn("group_id", group)
        self.assertIn("protocol_version", group)
        self.assertIn("canonical_branch", group)

        self.assertEqual(group["group_id"], "G-01")
        self.assertEqual(group["canonical_branch"], "main")

    def test_load_members(self):
        """測試是否能讀取成員"""

        members = groupctl.load_members()

        self.assertGreaterEqual(len(members), 1)

        person_ids = [
            member["person_id"]
            for member in members
        ]

        self.assertIn("P-01", person_ids)

    def test_make_event(self):
        """測試是否能建立合法的 finding 事件"""

        with tempfile.TemporaryDirectory() as temp_dir:

            temp_path = Path(temp_dir)

            with patch.object(
                groupctl, "EVENTS_DIR", temp_path
            ):
                path, event = groupctl.make_event(
                    "finding",
                    "P-01",
                    {
                        "summary": "Unit test finding",
                        "evidence": []
                    }
                )

                self.assertTrue(path.exists())

                with open(
                    path, "r", encoding="utf-8"
                ) as file:
                    saved = json.load(file)

                self.assertEqual(
                    saved["event_type"], "finding"
                )

                self.assertEqual(
                    saved["person_id"], "P-01"
                )

                self.assertEqual(
                    saved["group_id"], "G-01"
                )

                self.assertEqual(
                    saved["event_id"], event["event_id"]
                )

                self.assertEqual(
                    saved["summary"], "Unit test finding"
                )

    def test_unknown_member(self):
        """測試不存在的成員是否遭到拒絕"""

        with tempfile.TemporaryDirectory() as temp_dir:

            with patch.object(
                groupctl,
                "MEMBERS_DIR",
                Path(temp_dir)
            ):
                with self.assertRaises(ValueError):
                    groupctl.make_event(
                        "finding",
                        "P-UNKNOWN",
                        {
                            "summary": "Invalid member",
                            "evidence": []
                        }
                    )


if __name__ == "__main__":
    unittest.main()
