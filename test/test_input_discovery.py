import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class InputDiscoveryTests(unittest.TestCase):
    def test_forward_dwi_grouping_and_order(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            input_dir = root / "input"
            for subject in ("subject-one", "subject-two"):
                directory = input_dir / subject
                directory.mkdir(parents=True)
                for suffix in ("nii.gz", "bval", "bvec"):
                    (directory / f"sample_dwi.{suffix}").touch()

            script = root / "discovery.nf"
            script.write_text(
                f"""include {{ get_data }} from '{ROOT / 'main.nf'}'
workflow {{
    get_data()
    get_data.out.dwi.view {{ meta, dwi, bval, bvec ->
        'DISCOVERY ' + groovy.json.JsonOutput.toJson(
            [meta.id, dwi.toString(), bval.toString(), bvec.toString()])
    }}
}}
"""
            )
            config = root / "empty.config"
            config.touch()
            result = subprocess.run(
                ["nextflow", "-C", str(config), "-log", str(root / "nextflow.log"),
                 "run", str(script), "-work-dir", str(root / "work"),
                 "--input", str(input_dir)],
                cwd=root, env={**os.environ, "NXF_ANSI_LOG": "false"},
                capture_output=True, text=True, timeout=180,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            discovered = [
                json.loads(line.removeprefix("DISCOVERY "))
                for line in result.stdout.splitlines()
                if line.startswith("DISCOVERY ")
            ]
            expected = [
                [subject, *(str(input_dir / subject / f"sample_dwi.{suffix}")
                            for suffix in ("nii.gz", "bval", "bvec"))]
                for subject in ("subject-one", "subject-two")
            ]
            self.assertCountEqual(discovered, expected)


if __name__ == "__main__":
    unittest.main()
