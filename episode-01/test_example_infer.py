"""Check CLI failures and device selection without downloading a model."""

from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from pathlib import Path
import subprocess
import sys
import unittest
from unittest.mock import MagicMock, patch

import example_infer


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


class DeviceSelectionTests(unittest.TestCase):
    def setUp(self):
        self.torch = MagicMock()
        self.transformers = MagicMock()
        self.model = self.transformers.AutoModelForCausalLM.from_pretrained.return_value
        self.model.to.return_value = self.model
        self.tokenizer = self.transformers.AutoTokenizer.from_pretrained.return_value
        self.input_ids = MagicMock()
        self.input_ids.shape = (1, 3)
        self.inputs = self.tokenizer.apply_chat_template.return_value
        self.inputs.to.return_value = {"input_ids": self.input_ids}
        self.tokenizer.decode.return_value = "Test answer."
        self.stdout = StringIO()
        self.stderr = StringIO()

    def run_main(self, args):
        with (
            patch.dict(sys.modules, {"torch": self.torch, "transformers": self.transformers}),
            patch("builtins.input", return_value="Test prompt"),
            redirect_stdout(self.stdout),
            redirect_stderr(self.stderr),
        ):
            return example_infer.main(args)

    def test_cpu_remains_the_default_when_cuda_is_available(self):
        self.torch.cuda.is_available.return_value = True
        self.assertEqual(self.run_main([]), 0)
        self.model.to.assert_called_once_with("cpu")
        self.inputs.to.assert_called_once_with("cpu")
        self.assertIn("on CPU (float32)", self.stdout.getvalue())

    def test_cuda_moves_both_model_and_input_before_generation(self):
        self.torch.cuda.is_available.return_value = True
        self.assertEqual(self.run_main(["--device", "cuda"]), 0)
        self.model.to.assert_called_once_with("cuda")
        self.inputs.to.assert_called_once_with("cuda")
        self.assertIs(self.model.generate.call_args.kwargs["input_ids"], self.input_ids)
        self.assertIn("on CUDA (float32)", self.stdout.getvalue())
        self.assertIn("Test answer.", self.stdout.getvalue())

    def test_unavailable_cuda_stops_before_model_download(self):
        self.torch.cuda.is_available.return_value = False
        self.assertEqual(self.run_main(["--device", "cuda"]), 2)
        self.assertIn("CUDA is not available", self.stderr.getvalue())
        self.assertIn("--device cpu", self.stderr.getvalue())
        self.transformers.AutoTokenizer.from_pretrained.assert_not_called()
        self.transformers.AutoModelForCausalLM.from_pretrained.assert_not_called()


if __name__ == "__main__":
    unittest.main()
