
import unittest
from src.demo import calculate_sum, calculate_product


class TestDemoIntegration(unittest.TestCase):

    def test_sum_positive(self):
        self.assertEqual(calculate_sum(3, 5), 8)

    def test_sum_negative(self):
        self.assertEqual(calculate_sum(-3, 5), 2)

    def test_sum_zero(self):
        self.assertEqual(calculate_sum(0, 0), 0)

    def test_product_positive(self):
        self.assertEqual(calculate_product(3, 5), 15)

    def test_product_negative(self):
        self.assertEqual(calculate_product(-3, 5), -15)

    def test_product_zero(self):
        self.assertEqual(calculate_product(0, 10), 0)


if __name__ == "__main__":
    unittest.main()
