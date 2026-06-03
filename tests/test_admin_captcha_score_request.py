import ast
import unittest
from pathlib import Path


class AdminCaptchaScoreRequestTest(unittest.TestCase):
    def test_captcha_score_uses_parameter_not_undefined_request_name(self):
        source = Path("src/api/admin.py").read_text(encoding="utf-8")
        module = ast.parse(source)
        functions = [
            node
            for node in module.body
            if isinstance(node, ast.AsyncFunctionDef)
            and node.name == "test_captcha_score"
        ]
        self.assertEqual(len(functions), 1)
        function = functions[0]
        loaded_names = {
            node.id
            for node in ast.walk(function)
            if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load)
        }
        self.assertIn("_request", loaded_names)
        self.assertNotIn("request", loaded_names)


if __name__ == "__main__":
    unittest.main()
