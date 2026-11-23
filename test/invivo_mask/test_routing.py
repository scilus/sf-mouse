import os
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


class RoutingTests(unittest.TestCase):
    def test_subject_routing(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            for name in ("b0_anatomy", "b0_fallback", "anat", "duplicate"):
                (root / f"{name}.nii.gz").touch()
            config = root / "nextflow.config"
            config.write_text(
                f"process.cpus = 2\ndocker.enabled = true\n"
                f"docker.runOptions = '-u {os.getuid()}:{os.getgid()}'\n"
            )
            for scenario in ("mixed", "no-anatomy", "duplicate-anatomy",
                             "duplicate-b0", "orphan-anatomy"):
                with self.subTest(scenario=scenario):
                    work = root / scenario
                    result = subprocess.run(
                        ["nextflow", "-C", str(config), "-log", str(root / f"{scenario}.log"),
                         "run", str(ROOT / "test/invivo_mask/routing.nf"),
                         "-stub-run", "-work-dir", str(work),
                         "--input", str(root), "--scenario", scenario],
                        cwd=root, env={**os.environ, "NXF_ANSI_LOG": "false"},
                        capture_output=True, text=True, timeout=180,
                    )
                    output = result.stdout + result.stderr
                    if scenario.startswith("duplicate"):
                        self.assertNotEqual(result.returncode, 0, output)
                        self.assertIn("duplicate", output.lower())
                    elif scenario == "orphan-anatomy":
                        self.assertNotEqual(result.returncode, 0, output)
                        self.assertIn("orphan: anatomical input has no matching DWI b0", output)
                    else:
                        self.assertEqual(result.returncode, 0, output)
                        self.assertIn("RESULT anatomy ", output)
                        self.assertIn("RESULT fallback ", output)
                        prep = [p.parent for p in work.glob("*/*/.command.sh")
                                if "N4BiasFieldCorrection -h" in p.read_text()]
                        self.assertEqual(len(prep), 2)
                        inputs = {path.name for task in prep for path in task.iterdir()
                                  if path.is_symlink()}
                        self.assertIn("b0_fallback.nii.gz", inputs)
                        self.assertIn("anat.nii.gz" if scenario == "mixed"
                                      else "b0_anatomy.nii.gz", inputs)
                        self.assertEqual(output.count("Submitted process > INVIVO_MASK:MOUSE_ALIGNANATMASK"),
                                         1 if scenario == "mixed" else 0)
                        self.assertEqual(output.count("Submitted process > INVIVO_MASK:MOUSE_VALIDATEINVIVOMASK"),
                                         1 if scenario == "mixed" else 2)


if __name__ == "__main__":
    unittest.main()
