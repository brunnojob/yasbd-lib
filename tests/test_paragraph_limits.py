import unittest
from yasbd.utils.paragraph_stream import ParagraphStream


class ParagraphLimitTests(unittest.TestCase):
    def test_cumulative_limit(self):
        with self.assertRaises(ValueError):
            list(ParagraphStream("ab\ncd\n", max_paragraph_chars=5))

    def test_limit_resets_between_paragraphs(self):
        self.assertEqual(list(ParagraphStream("ab\n\ncd\n", max_paragraph_chars=4)), ["ab\n\n", "cd\n"])

    def test_invalid_limits_and_single_long_line(self):
        for limit in (True, 0, -1, 0.5):
            with self.assertRaises(ValueError):
                ParagraphStream("hello", max_paragraph_chars=limit)
        with self.assertRaises(ValueError):
            list(ParagraphStream("abcdef", max_paragraph_chars=5))


if __name__ == "__main__":
    unittest.main()
