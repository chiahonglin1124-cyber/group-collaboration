
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GROUPCTL = ROOT / "groupctl.py"


def run_cli(*args):
    """執行 groupctl CLI，回傳執行結果"""
    return subprocess.run(
        [sys.executable, str(GROUPCTL), *args],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace"
    )


class TestGroupCtlCLI(unittest.TestCase):

    def test_help(self):
        """沒有輸入指令時，應顯示可用指令"""
        result = run_cli()

        self.assertEqual(result.returncode, 0)
        self.assertIn("Available commands", result.stdout)
        self.assertIn("publish", result.stdout)
        self.assertIn("sync", result.stdout)
        self.assertIn("status", result.stdout)

    def test_group(self):
        """測試查詢小組資訊"""
        result = run_cli("group")

        self.assertEqual(result.returncode, 0)
        self.assertIn("G-01", result.stdout)
        self.assertIn("main", result.stdout)

    def test_members(self):
        """測試查詢小組成員"""
        result = run_cli("members")

        self.assertEqual(result.returncode, 0)
        self.assertIn("P-01", result.stdout)
        self.assertIn("P-02", result.stdout)

    def test_unknown_command(self):
        """未知指令應顯示錯誤提示"""
        result = run_cli("invalid_command")

        self.assertIn("Unknown command", result.stdout)

    def test_review_missing_argument(self):
        """REV 未提供 Change ID 應被拒絕"""
        result = run_cli("rev")

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Usage: rev", result.stdout)

    def test_test_missing_argument(self):
        """TEST 未提供成員 ID 應被拒絕"""
        result = run_cli("test")

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Usage: test", result.stdout)

    def test_final_missing_argument(self):
        """FINAL 候選指令缺少成員 ID"""
        result = run_cli("final-candidate")

        self.assertNotEqual(result.returncode, 0)
        self.assertIn(
            "Usage: final-candidate",
            result.stdout
        )


if __name__ == "__main__":
    unittest.main()
