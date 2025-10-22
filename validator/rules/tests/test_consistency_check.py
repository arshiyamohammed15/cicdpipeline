"""
Integration test to ensure Constitution sources are consistent.

This test runs the enhanced CLI consistency check and asserts zero differences.
"""

import subprocess
import sys
import unittest


class TestConstitutionConsistency(unittest.TestCase):
    """End-to-end consistency verification for Constitution sources."""

    def test_verify_consistency_ok(self):
        """Run the CLI verify and require zero differences."""
        # Use the same Python interpreter and run the CLI in-process environment
        cmd = [sys.executable, "enhanced_cli.py", "--verify-consistency"]
        proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, check=False)

        output = proc.stdout
        self.assertEqual(proc.returncode, 0, msg=f"CLI exited with non-zero code. Output:\n{output}")
        self.assertIn("All sources are consistent", output, msg=f"Consistency check failed. Output:\n{output}")


if __name__ == '__main__':
    unittest.main()


