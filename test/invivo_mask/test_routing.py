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
            for name in ("b0_anatomy", "b0_fallback", "anat", "duplicate", "provided_mask"):
                (root / f"{name}.nii.gz").touch()
            config = root / "nextflow.config"
            config.write_text(
                f"process.cpus = 2\ndocker.enabled = true\n"
                f"docker.runOptions = '-u {os.getuid()}:{os.getgid()}'\n"
            )
            for scenario in ("mixed", "no-anatomy", "provided-no-anatomy",
                             "duplicate-anatomy", "duplicate-b0",
                             "orphan-anatomy", "orphan-mask"):
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
                    elif scenario in ("orphan-anatomy", "orphan-mask"):
                        self.assertNotEqual(result.returncode, 0, output)
                        message = ("anatomical input" if scenario == "orphan-anatomy"
                                   else "provided mask")
                        self.assertIn(f"orphan: {message} has no matching DWI b0", output)
                    else:
                        self.assertEqual(result.returncode, 0, output)
                        self.assertIn("RESULT anatomy ", output)
                        self.assertIn("RESULT fallback ", output)
                        prep = [p.parent for p in work.glob("*/*/.command.sh")
                                if "N4BiasFieldCorrection -h" in p.read_text()]
                        expected_prep_count = {
                            "mixed": 1,
                            "no-anatomy": 2,
                            "provided-no-anatomy": 1,
                        }[scenario]
                        self.assertEqual(len(prep), expected_prep_count)
                        inputs = {path.name for task in prep for path in task.iterdir()
                                  if path.is_symlink()}
                        if scenario in ("mixed", "no-anatomy"):
                            self.assertIn("b0_fallback.nii.gz", inputs)
                        if scenario == "no-anatomy":
                            self.assertIn("b0_anatomy.nii.gz", inputs)
                        elif scenario == "mixed":
                            self.assertNotIn("anat.nii.gz", inputs)
                        else:
                            self.assertIn("b0_anatomy.nii.gz", inputs)
                        staged_inputs = {
                            path.name for task in work.glob("*/*")
                            for path in task.iterdir() if path.is_symlink()
                        }
                        if scenario == "mixed":
                            self.assertIn("anat_mask.nii.gz", staged_inputs)
                        elif scenario == "provided-no-anatomy":
                            self.assertIn("provided_mask.nii.gz", staged_inputs)
                        self.assertEqual(output.count("Submitted process > INVIVO_MASK:MOUSE_ALIGNANATMASK"),
                                         1 if scenario == "mixed" else 0)
                        self.assertEqual(output.count("Submitted process > INVIVO_MASK:MOUSE_VALIDATEINVIVOMASK"),
                                         1 if scenario == "mixed" else 2)


if __name__ == "__main__":
    unittest.main()
