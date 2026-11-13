import unittest

from src.hello_int import greet, group_message


class TestHelloInt(unittest.TestCase):

    def test_greet_includes_name(self):
        self.assertEqual(greet("Student 1"), "Hello, Student 1!")

    def test_greet_uses_a_different_name(self):
        self.assertEqual(greet("Alice"), "Hello, Alice!")

    def test_group_message_returns_collaboration_message(self):
        self.assertEqual(
            group_message(),
            "Group collaboration is working!"
        )


if __name__ == "__main__":
    unittest.main()
