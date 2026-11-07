"""Check CLI input failures without loading the model."""

from pathlib import Path
import subprocess
import sys
import unittest


SCRIPT = Path(__file__).with_name("example_infer.py")


class PromptValidationTests(unittest.TestCase):
    def test_empty_prompt_stops_before_model_loading(self):
        result = subprocess.run(
            [sys.executable, str(SCRIPT)], input="  \n", text=True, capture_output=True
        )
        self.assertEqual(result.returncode, 2)
        self.assertIn("Prompt must not be empty.", result.stderr)
        self.assertNotIn("Loading", result.stdout)

    def test_missing_stdin_has_a_clear_error(self):
        result = subprocess.run(
            [sys.executable, str(SCRIPT)], input="", text=True, capture_output=True
        )
        self.assertEqual(result.returncode, 2)
        self.assertIn("No prompt received.", result.stderr)
        self.assertNotIn("Loading", result.stdout)


if __name__ == "__main__":
    unittest.main()
