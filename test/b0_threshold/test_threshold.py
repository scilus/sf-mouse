import os
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


class ThresholdTests(unittest.TestCase):
    def run_component(self, component, threshold):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            for name in ("dwi.nii.gz", "dwi.bval", "dwi.bvec", "mask.nii.gz"):
                (root / name).touch()
            for name in ("scil_dwi_extract_shell", "scil_dti_metrics", "scil_qball_metrics"):
                command = root / name
                command.write_text("#!/bin/sh\necho 'test command stopped' >&2\nexit 42\n")
                command.chmod(0o755)
            command = root / "scil_dwi_powder_average"
            command.write_text("#!/bin/sh\nprintf '%s\\n' \"$@\" > powder.args\ntouch \"$3\"\n")
            command.chmod(0o755)
            (root / "uv").symlink_to("/bin/true")
            result = subprocess.run(
                ["nextflow", "-log", str(root / "nextflow.log"), "run",
                 str(ROOT / "test/b0_threshold/workflow.nf"), "-c", str(ROOT / "nextflow.config"),
                 "-c", str(ROOT / "test/b0_threshold/nextflow.config"),
                 "-work-dir", str(root / "work"), "--outdir", str(root / "results"),
                 "--component", component, "--b0_threshold", str(threshold),
                 "--dwi", str(root / "dwi.nii.gz"), "--bval", str(root / "dwi.bval"),
                 "--bvec", str(root / "dwi.bvec"), "--mask", str(root / "mask.nii.gz")],
                cwd=root, env={**os.environ, "NXF_ANSI_LOG": "false",
                               "PATH": str(root) + os.pathsep + os.environ["PATH"]},
                capture_output=True, text=True, timeout=180,
            )
            scripts = list((root / "work").glob("*/*/.command.sh"))
            self.assertEqual(len(scripts), 1, result.stdout + result.stderr)
            script = scripts[0].read_text()
            if component == "powder":
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                args = (scripts[0].parent / "powder.args").read_text().splitlines()
                self.assertEqual(args[args.index("--b0_thr") + 1], str(threshold))
            else:
                self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
                self.assertIn("test command stopped", result.stdout + result.stderr)
            return script

    def test_user_threshold_reaches_process_commands(self):
        for component in ("powder", "registration", "frf", "qball"):
            with self.subTest(component=component):
                script = self.run_component(component, 150)
                if component == "registration":
                    commands = [line for line in script.splitlines()
                                if line.strip().startswith(("scil_dti_metrics ", "scil_dwi_extract_b0 "))]
                    self.assertEqual(len(commands), 2)
                    for command in commands:
                        self.assertIn("--b0_threshold 150", command)
                elif component != "powder":
                    self.assertIn("--b0_threshold 150", script)

    def test_default_threshold_configuration(self):
        result = subprocess.run(
            ["nextflow", "config", "-flat", str(ROOT)], capture_output=True, text=True, timeout=180,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        for selector, setting in (
            ("NNUNET:IMAGE_POWDERAVERAGE", "b0_thr"),
            ("MOUSE_REGISTRATION", "b0_threshold"),
            ("RECONST_FRF", "b0_thr_extract_b0"),
            ("RECONST_QBALL", "b0_threshold"),
        ):
            self.assertIn(f"process.'withName:{selector}'.ext.{setting} = 100", result.stdout)


if __name__ == "__main__":
    unittest.main()
