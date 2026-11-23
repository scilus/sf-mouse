import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
IMAGE = "scilus/scilus:2.2.2"


class AlignmentTests(unittest.TestCase):
    def test_alignment_and_identity_resampling(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            shutil.copy(ROOT / "modules/local/mouse/alignanatmask/validate_grids.py", root / "validator.py")
            script = """
import nibabel as nib
import numpy as np
from pathlib import Path
p = Path('/data')
indices = np.indices((32, 32, 32))
signal = np.exp(-sum(((indices[i] - [14, 16, 15][i]) / [5, 6, 4][i])**2 for i in range(3)))
mask = (signal > .2).astype(np.uint8)
for name, spacing in [('same', 1), ('different', 2)]:
    affine = np.diag([spacing, spacing, spacing, 1])
    nib.save(nib.Nifti1Image(signal.astype(np.float32), np.eye(4)), p / f'{name}_b0.nii.gz')
    nib.save(nib.Nifti1Image(signal.astype(np.float32), affine), p / f'{name}_anat.nii.gz')
    nib.save(nib.Nifti1Image(mask, affine), p / f'{name}_mask.nii.gz')
"""
            subprocess.run(
                ["docker", "run", "--rm", "-u", f"{os.getuid()}:{os.getgid()}",
                 "-v", f"{root}:/data", "--entrypoint", "python",
                 IMAGE, "-c", script],
                check=True, capture_output=True, text=True, timeout=120,
            )
            config = root / "nextflow.config"
            config.write_text(f"process.cpus = 2\ndocker.runOptions = '-u {os.getuid()}:{os.getgid()}'\n"
                              "params.register = true\n")
            for register in (False, True):
                with self.subTest(register=register):
                    work = root / f"work-{register}"
                    result = subprocess.run(
                        ["nextflow", "-C", str(config), "-log", str(root / f"{register}.log"),
                         "run", str(ROOT / "test/invivo_mask/workflow.nf"),
                         "-work-dir", str(work), "-with-docker", IMAGE,
                         "--input", str(root), "--register", str(register).lower()],
                        cwd=root, env={**os.environ, "NXF_ANSI_LOG": "false"},
                        capture_output=True, text=True, timeout=600,
                    )
                    self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                    self.assertIn(f"REGISTER {str(register).lower()}", result.stdout)
                    outputs = {parts[1]: parts[2] for line in result.stdout.splitlines()
                               if line.startswith("MASK ") for parts in [line.split()]}
                    self.assertEqual(set(outputs), {"same", "different"})
                    scripts = [p.read_text() for p in work.glob("*/*/.command.sh")]
                    self.assertEqual(len(scripts), 2)
                    for command in scripts:
                        if register:
                            self.assertIn("antsRegistrationSyNQuick.sh", command)
                        else:
                            self.assertNotIn("antsRegistrationSyNQuick.sh", command)
                            self.assertIn("-t identity -n NearestNeighbor", command)
                    for subject, output in outputs.items():
                        verify = subprocess.run(
                            ["docker", "run", "--rm", "-v", f"{root}:/data", "--entrypoint", "python",
                             IMAGE, "/data/validator.py", f"/data/{subject}_b0.nii.gz",
                             f"/data/{Path(output).relative_to(root)}", "--require-match"],
                            capture_output=True, text=True, timeout=120,
                        )
                        self.assertEqual(verify.returncode, 0, verify.stdout + verify.stderr)
                    if not register:
                        self.assertEqual((root / "same_mask.nii.gz").read_bytes(),
                                         Path(outputs["same"]).read_bytes())

            default_result = subprocess.run(
                ["nextflow", "-C", str(config), "-log", str(root / "default.log"),
                 "run", str(ROOT / "test/invivo_mask/workflow.nf"), "-stub-run",
                 "-work-dir", str(root / "default-work"), "-with-docker", IMAGE,
                 "--input", str(root)],
                cwd=root, env={**os.environ, "NXF_ANSI_LOG": "false"},
                capture_output=True, text=True, timeout=120,
            )
            self.assertEqual(default_result.returncode, 0, default_result.stdout + default_result.stderr)
            self.assertIn("REGISTER true", default_result.stdout)

            result = subprocess.run(
                ["nextflow", "-C", str(config), "-log", str(root / "invalid.log"),
                 "run", str(ROOT / "test/invivo_mask/workflow.nf"),
                 "--input", str(root), "--register", "invalid"],
                cwd=root, env={**os.environ, "NXF_ANSI_LOG": "false"},
                capture_output=True, text=True, timeout=120,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("invivo_register_anat must be true or false", result.stdout + result.stderr)

            move_reference = """
import nibabel as nib
img = nib.load('/data/different_b0.nii.gz')
affine = img.affine.copy()
affine[0, 3] = 1000
nib.save(nib.Nifti1Image(img.get_fdata(), affine), '/data/different_b0.nii.gz')
"""
            subprocess.run(
                ["docker", "run", "--rm", "-u", f"{os.getuid()}:{os.getgid()}",
                 "-v", f"{root}:/data", "--entrypoint", "python", IMAGE, "-c", move_reference],
                check=True, capture_output=True, text=True, timeout=120,
            )
            result = subprocess.run(
                ["nextflow", "-C", str(config), "-log", str(root / "no-overlap.log"),
                 "run", str(ROOT / "test/invivo_mask/workflow.nf"),
                 "-work-dir", str(root / "no-overlap"), "-with-docker", IMAGE,
                 "--input", str(root), "--register", "false"],
                cwd=root, env={**os.environ, "NXF_ANSI_LOG": "false"},
                capture_output=True, text=True, timeout=120,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("nonempty", result.stdout + result.stderr)

    def test_grid_and_mask_validation(self):
        script = """
import subprocess
import tempfile
from pathlib import Path
import nibabel as nib
import numpy as np

with tempfile.TemporaryDirectory() as directory:
    p = Path(directory)
    def save(name, values, affine=np.eye(4)):
        nib.save(nib.Nifti1Image(np.asarray(values, dtype=np.float32), affine), p / (name + '.nii.gz'))
    def check(mask, *options, succeeds):
        result = subprocess.run(['python', '/validator.py', str(p / 'reference.nii.gz'),
                                 str(p / (mask + '.nii.gz')), *options],
                                capture_output=True, text=True)
        assert (result.returncode == 0) == succeeds, result.stdout + result.stderr
        return result.stdout.strip()
    save('reference', np.ones((4, 4, 4)))
    save('valid', np.ones((4, 4, 4)))
    save('empty', np.zeros((4, 4, 4)))
    negative = np.ones((4, 4, 4)); negative[0, 0, 0] = -1
    save('negative', negative)
    invalid = np.ones((4, 4, 4)); invalid[0, 0, 0] = np.nan
    save('nonfinite', invalid)
    save('four_d', np.ones((4, 4, 4, 1)))
    shifted = np.eye(4); shifted[0, 3] = 1
    save('shifted', np.ones((4, 4, 4)), shifted)
    assert check('valid', '--require-match', succeeds=True) == 'same'
    assert check('shifted', succeeds=True) == 'different'
    check('shifted', '--require-match', succeeds=False)
    check('shifted', '--anatomy', str(p / 'valid.nii.gz'), succeeds=False)
    for mask in ['empty', 'negative', 'nonfinite', 'four_d']:
        check(mask, succeeds=False)
"""
        result = subprocess.run(
            ["docker", "run", "--rm", "--entrypoint", "python",
             "-v", f"{ROOT / 'modules/local/mouse/alignanatmask/validate_grids.py'}:/validator.py:ro",
             IMAGE, "-c", script],
            capture_output=True, text=True, timeout=120,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
