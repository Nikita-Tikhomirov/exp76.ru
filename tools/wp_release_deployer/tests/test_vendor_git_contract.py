import hashlib
import subprocess
import unittest
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
REGISTRY_PATH = "tools/wp_release_deployer/land76-release-deployer/vendor/service-hub-registry.php"
REGISTRY_SHA256 = "467220e5c953cce729805a33f28c0cc19d2542ff1adc8ffd0381e3a54d0cc412"


class VendorGitContractTest(unittest.TestCase):
    def test_registry_disables_git_text_normalization(self) -> None:
        result = subprocess.run(
            ["git", "check-attr", "-z", "text", "--", REGISTRY_PATH],
            cwd=REPOSITORY_ROOT,
            check=True,
            capture_output=True,
        )

        self.assertEqual(
            result.stdout,
            f"{REGISTRY_PATH}\0text\0unset\0".encode(),
        )

    def test_registry_matches_frozen_a2_bytes(self) -> None:
        registry = REPOSITORY_ROOT / Path(REGISTRY_PATH)

        self.assertEqual(
            hashlib.sha256(registry.read_bytes()).hexdigest(),
            REGISTRY_SHA256,
        )


if __name__ == "__main__":
    unittest.main()
