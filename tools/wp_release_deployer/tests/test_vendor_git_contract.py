import hashlib
import subprocess
import unittest
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
REGISTRY_PATH = "tools/wp_release_deployer/land76-release-deployer/vendor/service-hub-registry.php"
REGISTRY_SHA256 = "87aa0a611cdc9bd62f9b46edfae39274977a13d6863e0d5140cbf923242f99e5"


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
