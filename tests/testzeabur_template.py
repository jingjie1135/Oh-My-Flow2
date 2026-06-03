import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TEMPLATE_PATH = ROOT / "template.yaml"


def _template_text() -> str:
    return TEMPLATE_PATH.read_text(encoding="utf-8")


def _inline_dockerfile() -> str:
    template = _template_text()
    return template.split("dockerfile: |-", 1)[1].split("        ports:", 1)[0]


class ZeaburTemplateTest(unittest.TestCase):
    def test_inline_dockerfile_has_headed_browser_dependencies(self) -> None:
        dockerfile = _inline_dockerfile().lower()

        for package in ("xvfb", "fluxbox", "xauth"):
            with self.subTest(package=package):
                self.assertIn(package, dockerfile)

    def test_template_uses_browser_captcha_mode(self) -> None:
        template = _template_text()

        self.assertIn("preconfigured for browser captcha mode", template)
        self.assertIn('captcha_method = "browser"', template)
        self.assertNotIn('captcha_method = "personal"', template)

    def test_template_uses_project_github_repo_id(self) -> None:
        template = _template_text()

        self.assertIn("repo: 1210757887", template)

if __name__ == "__main__":
    _ = unittest.main()
