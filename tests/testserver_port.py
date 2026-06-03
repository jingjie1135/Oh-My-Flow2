import os
import unittest
from unittest.mock import patch

from main import resolve_server_port


class ServerPortTest(unittest.TestCase):
    def test_port_environment_variable_overrides_config_port(self) -> None:
        with patch.dict(os.environ, {"PORT": "8080"}, clear=False):
            self.assertEqual(resolve_server_port(8000), 8080)

    def test_invalid_port_environment_variable_uses_config_port(self) -> None:
        with patch.dict(os.environ, {"PORT": "not-a-port"}, clear=False):
            self.assertEqual(resolve_server_port(8000), 8000)


if __name__ == "__main__":
    _ = unittest.main()
