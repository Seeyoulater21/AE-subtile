import tomllib
import unittest
from pathlib import Path


class PackagingTests(unittest.TestCase):
    def test_python_pyproject_does_not_reference_files_outside_package_root(self):
        pyproject = tomllib.loads(Path("python/pyproject.toml").read_text(encoding="utf-8"))
        readme = pyproject["project"].get("readme")

        if isinstance(readme, str):
            self.assertFalse(readme.startswith("../"), "setuptools rejects readme paths outside python/")

    def test_python_pyproject_exposes_cli_and_server_scripts(self):
        pyproject = tomllib.loads(Path("python/pyproject.toml").read_text(encoding="utf-8"))

        self.assertEqual(pyproject["project"]["scripts"]["ae-subtitle"], "aesubtitle.cli:main")
        self.assertEqual(pyproject["project"]["scripts"]["ae-subtitle-server"], "aesubtitle.server:main")


if __name__ == "__main__":
    unittest.main()
